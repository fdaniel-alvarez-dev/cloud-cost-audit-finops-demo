from __future__ import annotations

import pytest

from cloud_cost_audit.analytics.quick_wins import build_top_10_quick_wins
from cloud_cost_audit.analytics.waste_detection import Opportunity


def test_builds_exactly_10_quick_wins_sorted() -> None:
    opps = [
        Opportunity(
            kind=f"k{i}",
            title=f"opp-{i}",
            scope="aws",
            estimated_savings_usd=float(i),
            confidence="high",
            risk="low",
            effort="S",
            details="x",
        )
        for i in range(1, 15)
    ]
    wins = build_top_10_quick_wins(opps)
    assert len(wins) == 10
    assert wins[0].expected_savings_monthly_usd == 14.0
    assert wins[-1].expected_savings_monthly_usd == 5.0


def test_raises_when_less_than_10_opportunities() -> None:
    opps = [
        Opportunity(
            kind="k",
            title="x",
            scope="aws",
            estimated_savings_usd=1.0,
            confidence="high",
            risk="low",
            effort="S",
            details="x",
        )
        for _ in range(3)
    ]
    with pytest.raises(ValueError):
        build_top_10_quick_wins(opps)
