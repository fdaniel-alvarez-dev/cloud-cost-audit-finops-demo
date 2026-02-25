from __future__ import annotations

from pathlib import Path

import yaml

from cloud_cost_audit.config import AuditConfig
from cloud_cost_audit.io.synthetic_data import ensure_synthetic_inputs
from cloud_cost_audit.pipeline import run_audit


def _write_config(tmp_dir: Path) -> Path:
    cfg = {
        "invoice_month": "2026-01",
        "data_dir": str(tmp_dir / "data"),
        "output_dir": str(tmp_dir / "out"),
        "duckdb_path": str(tmp_dir / "out" / "audit.duckdb"),
        "required_allocation_keys": ["env", "app", "team", "cost_center"],
        "thresholds": {"underutilized_cpu_pct": 10.0, "min_compute_cost_usd": 150.0},
    }
    path = tmp_dir / "config.yaml"
    path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return path


def test_end_to_end_pipeline_outputs(tmp_path: Path) -> None:
    cfg_path = _write_config(tmp_path)
    cfg = AuditConfig.load(cfg_path)
    ensure_synthetic_inputs(data_dir=Path(cfg.data_dir), invoice_month=cfg.invoice_month)
    result = run_audit(config=cfg)

    assert 19_000.0 <= result.baseline_cost_usd <= 21_000.0
    assert len(result.quick_wins) == 10
    assert 3_500.0 <= result.savings_total_usd <= 5_000.0

    out_dir = Path(cfg.output_dir)
    assert (out_dir / "quick_wins.csv").exists()
    assert (out_dir / "tag_coverage.json").exists()
    assert Path(cfg.duckdb_path).exists()
