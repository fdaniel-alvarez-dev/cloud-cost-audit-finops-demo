from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import duckdb
import pandas as pd

from cloud_cost_audit.analytics.metrics import (
    TagCoverage,
    compute_tag_coverage,
    export_cost_by_service,
    export_unallocated_spend,
)
from cloud_cost_audit.analytics.quick_wins import build_top_10_quick_wins
from cloud_cost_audit.analytics.waste_detection import (
    detect_commitment_opportunities,
    detect_egress_hotspots,
    detect_schedule_nonprod_compute,
    detect_storage_tier_optimizations,
    detect_underutilized_compute,
    detect_zombie_assets,
)
from cloud_cost_audit.config import AuditConfig
from cloud_cost_audit.io.cloud_providers import Providers
from cloud_cost_audit.models.core import QuickWin
from cloud_cost_audit.transforms.normalize import (
    normalize_aws_billing,
    normalize_gcp_billing,
    unify_line_items,
)


@dataclass(frozen=True)
class AuditRunResult:
    baseline_cost_usd: float
    savings_total_usd: float
    quick_wins: list[QuickWin]
    tag_coverage: TagCoverage
    quick_wins_csv: Path
    duckdb_path: Path


def run_audit(*, config: AuditConfig) -> AuditRunResult:
    config.output_dir.mkdir(parents=True, exist_ok=True)
    providers = Providers.from_data_dir(config.data_dir)

    aws_billing = normalize_aws_billing(providers.aws.billing())
    gcp_billing = normalize_gcp_billing(providers.gcp.billing())
    line_items = unify_line_items([aws_billing, gcp_billing])

    baseline = float(line_items["cost_usd"].sum())

    # Pull inventory/utilization for both providers (still mocked, local CSV).
    inventory = pd.concat([providers.aws.inventory(), providers.gcp.inventory()], ignore_index=True)
    utilization = pd.concat(
        [providers.aws.utilization(), providers.gcp.utilization()], ignore_index=True
    )

    opps = []
    opps += detect_underutilized_compute(
        inventory=inventory,
        utilization=utilization,
        underutilized_cpu_pct=config.thresholds.underutilized_cpu_pct,
        min_cost_usd=config.thresholds.min_compute_cost_usd,
    )
    opps += detect_schedule_nonprod_compute(inventory=inventory)
    opps += detect_zombie_assets(inventory=inventory)
    opps += detect_storage_tier_optimizations(line_items=line_items)
    opps += detect_egress_hotspots(line_items=line_items)
    opps += detect_commitment_opportunities(line_items=line_items)

    quick_wins = build_top_10_quick_wins(opps)

    # Persist to DuckDB for dashboarding.
    config.duckdb_path.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(config.duckdb_path)) as con:
        con.register("line_items", line_items)
        con.execute("create or replace table unified_line_items as select * from line_items")
        con.register("quick_wins_df", pd.DataFrame([q.model_dump() for q in quick_wins]))
        con.execute("create or replace table quick_wins as select * from quick_wins_df")

    # Machine-readable exports.
    quick_wins_csv = config.output_dir / "quick_wins.csv"
    pd.DataFrame([q.model_dump() for q in quick_wins]).to_csv(quick_wins_csv, index=False)
    export_cost_by_service(line_items, config.output_dir / "cost_by_service.csv")
    export_unallocated_spend(
        line_items, config.required_allocation_keys, config.output_dir / "unallocated_spend.csv"
    )

    tag_coverage = compute_tag_coverage(line_items, config.required_allocation_keys)
    (config.output_dir / "tag_coverage.json").write_text(
        tag_coverage.to_json() + "\n", encoding="utf-8"
    )

    # Monthly plan (derived from findings, deterministic template).
    _write_monthly_plan(config.output_dir / "monthly_plan.md", tag_coverage=tag_coverage)

    savings_total = float(sum(q.expected_savings_monthly_usd for q in quick_wins))
    (config.output_dir / "run_summary.json").write_text(
        json.dumps(
            {
                "invoice_month": config.invoice_month,
                "baseline_cost_usd": baseline,
                "quick_wins_savings_total_usd": savings_total,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return AuditRunResult(
        baseline_cost_usd=baseline,
        savings_total_usd=savings_total,
        quick_wins=quick_wins,
        tag_coverage=tag_coverage,
        quick_wins_csv=quick_wins_csv,
        duckdb_path=config.duckdb_path,
    )


def _write_monthly_plan(out_path: Path, *, tag_coverage: TagCoverage) -> None:
    lines = [
        "# Monthly Optimization Plan (Anti Cost-Drift)",
        "",
        (
            "This plan is generated from the audit outputs to simulate a lightweight, "
            "repeatable FinOps cadence."
        ),
        "",
        "## Week 1 — Visibility + Allocation Hygiene",
        (
            f"- Target fully allocated spend: **{tag_coverage.fully_allocated_pct*100.0:.1f}%** "
            "(increase month-over-month)."
        ),
        "- Enforce required tags/labels on new resources (policy + CI/IaC guardrails).",
        "- Review unallocated spend bucket and assign ownership.",
        "",
        "## Week 2 — Waste Cleanup",
        "- Run orphaned volume/disk/snapshot/IP cleanup with a documented approval workflow.",
        "- Verify retention policies for backups and snapshots.",
        "",
        "## Week 3 — Rightsizing + Scheduling",
        "- Review underutilized compute candidates; validate with 7–14 days of metrics.",
        "- Apply non-prod scheduling for nights/weekends; prevent regressions with policy.",
        "",
        "## Week 4 — Pricing Optimization",
        "- Re-evaluate commitments (AWS Savings Plans/RIs, GCP CUDs) against steady-state usage.",
        "- Validate storage class lifecycle policies for cold data.",
        "- Revisit egress hotspots and architecture improvements.",
        "",
        "## KPIs to track",
        "- Total monthly spend (net) and % change MoM",
        "- Fully allocated spend (%)",
        "- Unallocated spend ($) by service",
        "- Savings realized vs expected (from quick wins)",
        "",
    ]
    out_path.write_text("\n".join(lines), encoding="utf-8")
