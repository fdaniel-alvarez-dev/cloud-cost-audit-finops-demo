from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from cloud_cost_audit.analytics.metrics import TagCoverage
from cloud_cost_audit.models.core import QuickWin


@dataclass(frozen=True)
class ExecutiveReportInputs:
    invoice_month: str
    baseline_cost_usd: float
    quick_wins: list[QuickWin]
    tag_coverage: TagCoverage


def render_executive_report(
    *, inputs: ExecutiveReportInputs, template_dir: Path, out_html: Path, out_md: Path
) -> None:
    savings_total = sum(q.expected_savings_monthly_usd for q in inputs.quick_wins)
    savings_pct = (
        (savings_total / inputs.baseline_cost_usd * 100.0) if inputs.baseline_cost_usd else 0.0
    )

    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("executive_report.html.j2")
    html = template.render(
        invoice_month=inputs.invoice_month,
        baseline_cost_usd=f"{inputs.baseline_cost_usd:,.0f}",
        savings_total_usd=f"{savings_total:,.0f}",
        savings_pct=round(savings_pct, 1),
        quick_wins=inputs.quick_wins,
        required_keys=", ".join(inputs.tag_coverage.required_keys),
        fully_allocated_pct=round(inputs.tag_coverage.fully_allocated_pct * 100.0, 1),
        coverage_by_key=inputs.tag_coverage.coverage_by_key,
    )
    out_html.write_text(html, encoding="utf-8")

    # Markdown companion (easy diffing, useful for PR reviews)
    md_lines = [
        "# Cloud Cost Audit — Executive Report",
        f"- Invoice month: **{inputs.invoice_month}**",
        f"- Baseline spend (monthly): **${inputs.baseline_cost_usd:,.0f}**",
        f"- Top-10 quick wins savings: **${savings_total:,.0f}**",
        f"- Estimated savings rate: **{savings_pct:.1f}%**",
        "",
        "## Top 10 Quick Wins",
        "",
        "| # | Quick win | Scope | Expected monthly savings | Confidence | Risk | Effort |",
        "|---:|---|---|---:|---|---|---|",
    ]
    for q in inputs.quick_wins:
        md_lines.append(
            f"| {q.rank} | {q.title} | {q.scope} | "
            f"${q.expected_savings_monthly_usd:,.0f} | {q.confidence} | {q.risk} | {q.effort} |"
        )
    md_lines += [
        "",
        "## Cost allocation readiness (tags / labels)",
        f"Fully allocated spend: **{inputs.tag_coverage.fully_allocated_pct*100.0:.1f}%**",
        "",
        "| Key | Cost coverage |",
        "|---|---:|",
    ]
    for k, v in inputs.tag_coverage.coverage_by_key.items():
        md_lines.append(f"| {k} | {v*100.0:.1f}% |")
    out_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
