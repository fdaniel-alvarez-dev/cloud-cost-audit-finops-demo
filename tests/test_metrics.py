from __future__ import annotations

import pandas as pd

from cloud_cost_audit.analytics.metrics import compute_tag_coverage


def test_tag_coverage_computation() -> None:
    df = pd.DataFrame(
        [
            {"env": "prod", "app": "a", "team": "t", "cost_center": "cc", "cost_usd": 100.0},
            {"env": "prod", "app": "a", "team": "", "cost_center": "cc", "cost_usd": 50.0},
            {"env": "", "app": "b", "team": "t", "cost_center": "", "cost_usd": 50.0},
        ]
    )
    cov = compute_tag_coverage(df, ["env", "app", "team", "cost_center"])
    assert cov.total_cost_usd == 200.0
    assert 0.0 < cov.coverage_by_key["env"] < 1.0
    assert cov.fully_allocated_cost_usd == 100.0
    assert cov.fully_allocated_pct == 0.5
