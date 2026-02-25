from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_validator


class Thresholds(BaseModel):
    underutilized_cpu_pct: float = Field(ge=0.0, le=100.0)
    min_compute_cost_usd: float = Field(ge=0.0)


class AuditConfig(BaseModel):
    invoice_month: str
    data_dir: Path
    output_dir: Path
    duckdb_path: Path
    required_allocation_keys: list[str]
    thresholds: Thresholds

    @field_validator("required_allocation_keys")
    @classmethod
    def _validate_required_allocation_keys(cls, v: list[str]) -> list[str]:
        allowed = {"env", "app", "team", "cost_center"}
        unknown = sorted(set(v) - allowed)
        if unknown:
            raise ValueError(f"Unknown allocation keys: {unknown}. Allowed: {sorted(allowed)}")
        return v

    @staticmethod
    def load(path: Path) -> AuditConfig:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return AuditConfig.model_validate(data)
