from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class Opportunity:
    kind: str
    title: str
    scope: str
    estimated_savings_usd: float
    confidence: str
    risk: str
    effort: str
    details: str


def detect_underutilized_compute(
    *,
    inventory: pd.DataFrame,
    utilization: pd.DataFrame,
    underutilized_cpu_pct: float,
    min_cost_usd: float,
) -> list[Opportunity]:
    inv = inventory[inventory["resource_type"] == "instance"].copy()
    util = utilization.copy()
    merged = inv.merge(util, on=["provider", "resource_id"], how="left")
    merged["avg_cpu_pct"] = merged["avg_cpu_pct"].fillna(100.0).astype(float)
    merged["monthly_cost_estimate_usd"] = merged["monthly_cost_estimate_usd"].astype(float)
    candidates = merged[
        (merged["avg_cpu_pct"] < underutilized_cpu_pct)
        & (merged["monthly_cost_estimate_usd"] >= min_cost_usd)
    ].copy()
    opps: list[Opportunity] = []
    for _, row in candidates.sort_values("monthly_cost_estimate_usd", ascending=False).iterrows():
        # Conservative expected savings for "rightsizing" suggestions (validate before applying).
        savings = float(row["monthly_cost_estimate_usd"] * 0.25)
        opps.append(
            Opportunity(
                kind="underutilized_compute",
                title=f"Rightsize underutilized compute: {row['resource_id']}",
                scope=f"{row['provider']}:{row['region']}:{row['service']}",
                estimated_savings_usd=round(savings, 2),
                confidence="high",
                risk="medium",
                effort="M",
                details=(
                    f"avg_cpu_pct={float(row['avg_cpu_pct']):.1f}, "
                    f"current_estimated_monthly_cost=${float(row['monthly_cost_estimate_usd']):.0f}"
                ),
            )
        )
    return opps


def detect_schedule_nonprod_compute(*, inventory: pd.DataFrame) -> list[Opportunity]:
    inv = inventory[
        (inventory["resource_type"] == "instance") & (inventory["env"].astype(str) != "prod")
    ].copy()
    inv["monthly_cost_estimate_usd"] = inv["monthly_cost_estimate_usd"].astype(float)
    opps: list[Opportunity] = []
    for _, row in inv.sort_values("monthly_cost_estimate_usd", ascending=False).iterrows():
        # Assume a pragmatic schedule (nights + weekends), not full shutdown.
        savings = float(row["monthly_cost_estimate_usd"] * 0.35)
        opps.append(
            Opportunity(
                kind="schedule_nonprod",
                title=f"Schedule non-prod compute off-hours: {row['resource_id']}",
                scope=f"{row['provider']}:{row['region']}:{row['service']}",
                estimated_savings_usd=round(savings, 2),
                confidence="high",
                risk="low",
                effort="S",
                details="Implement instance schedules (nights/weekends) and enforce via policy.",
            )
        )
    return opps


def detect_zombie_assets(*, inventory: pd.DataFrame) -> list[Opportunity]:
    inv = inventory.copy()
    inv["monthly_cost_estimate_usd"] = inv["monthly_cost_estimate_usd"].astype(float)

    zombie = inv[
        (inv["resource_type"].isin(["volume", "disk", "ip", "snapshot"]))
        & (inv["status"].astype(str).str.len() > 0)
        & (inv["monthly_cost_estimate_usd"] > 0.0)
    ].copy()

    opps: list[Opportunity] = []
    for _, row in zombie.sort_values("monthly_cost_estimate_usd", ascending=False).iterrows():
        kind = f"zombie_{row['resource_type']}"
        opps.append(
            Opportunity(
                kind=kind,
                title=f"Remove zombie asset: {row['resource_type']} {row['resource_id']}",
                scope=f"{row['provider']}:{row['region']}:{row['service']}",
                estimated_savings_usd=round(float(row["monthly_cost_estimate_usd"]), 2),
                confidence="high",
                risk="low",
                effort="S",
                details=f"status={row['status']}, created_at={row['created_at']}",
            )
        )
    return opps


def detect_storage_tier_optimizations(*, line_items: pd.DataFrame) -> list[Opportunity]:
    storage = line_items[line_items["service"].isin(["AmazonS3", "Cloud Storage"])].copy()
    total = float(storage["cost_usd"].sum())
    if total <= 0:
        return []
    savings = round(total * 0.10, 2)
    return [
        Opportunity(
            kind="storage_tier",
            title="Move cold object storage to infrequent-access tiers",
            scope="aws+gcp:object_storage",
            estimated_savings_usd=savings,
            confidence="med",
            risk="low",
            effort="M",
            details=(
                "Identify low-access prefixes/buckets and apply lifecycle policies / "
                "storage class changes."
            ),
        )
    ]


def detect_egress_hotspots(*, line_items: pd.DataFrame) -> list[Opportunity]:
    egress = line_items[
        (line_items["service"].astype(str).str.contains("DataTransfer", case=False))
        | (line_items["sku"].astype(str).str.contains("Egress", case=False))
        | (line_items["service"].astype(str).str.contains("Networking", case=False))
    ].copy()
    total = float(egress["cost_usd"].sum())
    if total <= 0:
        return []
    savings = round(total * 0.05, 2)
    return [
        Opportunity(
            kind="egress",
            title="Reduce internet egress via CDN, caching, and topology review",
            scope="aws+gcp:network_egress",
            estimated_savings_usd=savings,
            confidence="med",
            risk="medium",
            effort="M",
            details=(
                "Start with top talkers, verify cross-zone/cross-region traffic, "
                "add CDN where appropriate."
            ),
        )
    ]


def detect_commitment_opportunities(*, line_items: pd.DataFrame) -> list[Opportunity]:
    compute = line_items[line_items["service"].isin(["AmazonEC2", "Compute Engine"])].copy()
    steady = float(compute[compute["env"].astype(str) == "prod"]["cost_usd"].sum())
    if steady <= 0:
        return []
    savings = round(steady * 0.08, 2)
    # Split into two opportunities for a richer "top 10" without inventing extra categories.
    return [
        Opportunity(
            kind="commitments_aws",
            title="Commitments for steady-state compute (AWS Savings Plans / RIs)",
            scope="aws:compute",
            estimated_savings_usd=round(savings * 0.55, 2),
            confidence="high",
            risk="low",
            effort="S",
            details=(
                "Use 1-year no-upfront plans for baseline usage; validate with utilization "
                "and roadmap."
            ),
        ),
        Opportunity(
            kind="commitments_gcp",
            title="Commitments for steady-state compute (GCP CUDs)",
            scope="gcp:compute",
            estimated_savings_usd=round(savings * 0.45, 2),
            confidence="high",
            risk="low",
            effort="S",
            details="Model sustained usage and buy CUDs for stable workloads; revisit monthly.",
        ),
    ]
