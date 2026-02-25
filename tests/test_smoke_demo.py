from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml


def test_smoke_cli_demo(tmp_path: Path) -> None:
    cfg = {
        "invoice_month": "2026-01",
        "data_dir": str(tmp_path / "data"),
        "output_dir": str(tmp_path / "out"),
        "duckdb_path": str(tmp_path / "out" / "audit.duckdb"),
        "required_allocation_keys": ["env", "app", "team", "cost_center"],
        "thresholds": {"underutilized_cpu_pct": 10.0, "min_compute_cost_usd": 150.0},
    }
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")

    subprocess.run(
        [sys.executable, "-m", "cloud_cost_audit.cli", "demo", "--config", str(cfg_path)],
        check=True,
        cwd=Path(__file__).resolve().parents[1],
    )

    out_dir = tmp_path / "out"
    assert (out_dir / "executive_report.html").exists()
    assert (out_dir / "dashboard_snapshot.html").exists()
    assert (out_dir / "quick_wins.csv").exists()
