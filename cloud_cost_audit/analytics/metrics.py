from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class TagCoverage:
    required_keys: list[str]
    total_cost_usd: float
    coverage_by_key: dict[str, float]
    fully_allocated_cost_usd: float
    fully_allocated_pct: float

    def to_json(self) -> str:
        return json.dumps(
            {
                "required_keys": self.required_keys,
                "total_cost_usd": self.total_cost_usd,
                "coverage_by_key": self.coverage_by_key,
                "fully_allocated_cost_usd": self.fully_allocated_cost_usd,
                "fully_allocated_pct": self.fully_allocated_pct,
            },
            indent=2,
            sort_keys=True,
        )


def compute_tag_coverage(line_items: pd.DataFrame, required_keys: list[str]) -> TagCoverage:
    total = float(line_items["cost_usd"].sum())
    coverage_by_key: dict[str, float] = {}
    for key in required_keys:
        has = line_items[key].astype(str).str.len() > 0
        coverage_by_key[key] = (
            float(line_items.loc[has, "cost_usd"].sum() / total) if total else 0.0
        )

    fully_allocated = line_items.copy()
    for key in required_keys:
        fully_allocated = fully_allocated[fully_allocated[key].astype(str).str.len() > 0]
    fully_allocated_cost = float(fully_allocated["cost_usd"].sum())
    fully_allocated_pct = (fully_allocated_cost / total) if total else 0.0
    return TagCoverage(
        required_keys=required_keys,
        total_cost_usd=total,
        coverage_by_key=coverage_by_key,
        fully_allocated_cost_usd=fully_allocated_cost,
        fully_allocated_pct=fully_allocated_pct,
    )


def export_cost_by_service(line_items: pd.DataFrame, out_csv: Path) -> pd.DataFrame:
    df = (
        line_items.groupby(["provider", "service"], as_index=False)["cost_usd"]
        .sum()
        .sort_values("cost_usd", ascending=False)
    )
    df.to_csv(out_csv, index=False)
    return df


def export_unallocated_spend(
    line_items: pd.DataFrame, required_keys: list[str], out_csv: Path
) -> pd.DataFrame:
    mask = pd.Series(False, index=line_items.index)
    for key in required_keys:
        mask = mask | (line_items[key].astype(str).str.len() == 0)
    df = (
        line_items.loc[mask]
        .groupby(["provider", "service"], as_index=False)["cost_usd"]
        .sum()
        .sort_values("cost_usd", ascending=False)
    )
    df.to_csv(out_csv, index=False)
    return df
