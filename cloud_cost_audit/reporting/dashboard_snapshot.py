from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px


def generate_static_dashboard_snapshot(
    *, cost_by_service: pd.DataFrame, quick_wins: pd.DataFrame, out_html: Path
) -> None:
    fig_cost = px.bar(
        cost_by_service,
        x="cost_usd",
        y=cost_by_service["provider"] + " / " + cost_by_service["service"],
        orientation="h",
        title="Cost by provider/service (monthly)",
    )
    fig_cost.update_layout(height=450, margin=dict(l=10, r=10, t=60, b=10))

    fig_wins = px.bar(
        quick_wins.sort_values("expected_savings_monthly_usd", ascending=True),
        x="expected_savings_monthly_usd",
        y="title",
        orientation="h",
        title="Top 10 quick wins (expected monthly savings)",
    )
    fig_wins.update_layout(height=520, margin=dict(l=10, r=10, t=60, b=10))

    html = "\n".join(
        [
            "<!doctype html>",
            (
                "<html><head><meta charset='utf-8'>"
                "<title>Cloud Cost Audit — Dashboard Snapshot</title>"
                "</head><body>"
            ),
            "<h1>Cloud Cost Audit — Dashboard Snapshot</h1>",
            "<p>Static snapshot generated locally from the audit outputs.</p>",
            fig_cost.to_html(full_html=False, include_plotlyjs="cdn"),
            "<hr/>",
            fig_wins.to_html(full_html=False, include_plotlyjs=False),
            "</body></html>",
        ]
    )
    out_html.write_text(html, encoding="utf-8")
