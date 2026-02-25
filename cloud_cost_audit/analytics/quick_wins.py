from __future__ import annotations

from cloud_cost_audit.analytics.waste_detection import Opportunity
from cloud_cost_audit.models.core import QuickWin


def _as_quick_win(rank: int, opp: Opportunity) -> QuickWin:
    return QuickWin(
        rank=rank,
        title=opp.title,
        description=opp.details,
        scope=opp.scope,
        expected_savings_monthly_usd=float(opp.estimated_savings_usd),
        confidence=opp.confidence,  # type: ignore[arg-type]
        risk=opp.risk,
        effort=opp.effort,  # type: ignore[arg-type]
        prerequisites="Change approval + small validation window.",
        owner_role="Platform Engineer",
        next_action="Create a ticket, validate with 7-day metrics, then execute via IaC/runbook.",
        kpi="Monthly spend reduction and % tagged/allocated spend.",
    )


def build_top_10_quick_wins(opportunities: list[Opportunity]) -> list[QuickWin]:
    ranked = sorted(opportunities, key=lambda o: o.estimated_savings_usd, reverse=True)
    top = ranked[:10]
    out: list[QuickWin] = []
    for idx, opp in enumerate(top, start=1):
        out.append(_as_quick_win(idx, opp))
    if len(out) != 10:
        raise ValueError(f"Expected exactly 10 quick wins, got {len(out)}")
    return out
