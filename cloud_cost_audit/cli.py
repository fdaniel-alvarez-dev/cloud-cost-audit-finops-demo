from __future__ import annotations

import subprocess
from pathlib import Path

import pandas as pd
import typer

from cloud_cost_audit.config import AuditConfig
from cloud_cost_audit.io.synthetic_data import ensure_synthetic_inputs
from cloud_cost_audit.logging_config import configure_logging
from cloud_cost_audit.pipeline import AuditRunResult, run_audit
from cloud_cost_audit.reporting.dashboard_snapshot import generate_static_dashboard_snapshot
from cloud_cost_audit.reporting.executive_report import (
    ExecutiveReportInputs,
    render_executive_report,
)

app = typer.Typer(add_completion=False, no_args_is_help=True)


def _load_config(config_path: Path) -> AuditConfig:
    cfg = AuditConfig.load(config_path)
    cfg.data_dir = Path(cfg.data_dir)
    cfg.output_dir = Path(cfg.output_dir)
    cfg.duckdb_path = Path(cfg.duckdb_path)
    return cfg


def _ensure_demo_inputs(cfg: AuditConfig) -> None:
    ensure_synthetic_inputs(data_dir=cfg.data_dir, invoice_month=cfg.invoice_month)


@app.command()
def demo(
    config: Path = typer.Option(..., "--config", exists=True, dir_okay=False),
    log_level: str = typer.Option("INFO", "--log-level"),
) -> None:
    """End-to-end: generate deterministic inputs (if missing) and run the audit pipeline."""
    configure_logging(level=log_level)
    cfg = _load_config(config)
    _ensure_demo_inputs(cfg)
    result = run_audit(config=cfg)
    _render_report(cfg=cfg, result=result)
    _render_snapshot(cfg=cfg)


@app.command()
def audit(
    config: Path = typer.Option(..., "--config", exists=True, dir_okay=False),
    log_level: str = typer.Option("INFO", "--log-level"),
) -> None:
    """Run the audit pipeline (expects inputs to exist under data/)."""
    configure_logging(level=log_level)
    cfg = _load_config(config)
    run_audit(config=cfg)


@app.command()
def report(
    config: Path = typer.Option(..., "--config", exists=True, dir_okay=False),
    log_level: str = typer.Option("INFO", "--log-level"),
) -> None:
    """Generate the executive report (HTML + Markdown) from the audit outputs."""
    configure_logging(level=log_level)
    cfg = _load_config(config)
    _ensure_demo_inputs(cfg)
    result = run_audit(config=cfg)
    _render_report(cfg=cfg, result=result)


@app.command()
def snapshot(
    config: Path = typer.Option(..., "--config", exists=True, dir_okay=False),
    log_level: str = typer.Option("INFO", "--log-level"),
) -> None:
    """Generate a static HTML dashboard snapshot from the audit outputs."""
    configure_logging(level=log_level)
    cfg = _load_config(config)
    _ensure_demo_inputs(cfg)
    run_audit(config=cfg)
    _render_snapshot(cfg=cfg)


@app.command()
def dashboard(
    config: Path = typer.Option(..., "--config", exists=True, dir_okay=False),
    log_level: str = typer.Option("INFO", "--log-level"),
) -> None:
    """Run the Streamlit dashboard (local, no cloud credentials)."""
    configure_logging(level=log_level)
    cfg = _load_config(config)
    _ensure_demo_inputs(cfg)
    if not cfg.duckdb_path.exists():
        run_audit(config=cfg)
    subprocess.run(
        [
            "streamlit",
            "run",
            "cloud_cost_audit/dashboard/app.py",
            "--server.headless",
            "true",
        ],
        check=True,
    )


def _render_report(*, cfg: AuditConfig, result: AuditRunResult) -> None:
    inputs = ExecutiveReportInputs(
        invoice_month=cfg.invoice_month,
        baseline_cost_usd=result.baseline_cost_usd,
        quick_wins=result.quick_wins,
        tag_coverage=result.tag_coverage,
    )
    template_dir = Path(__file__).parent / "reporting" / "templates"
    render_executive_report(
        inputs=inputs,
        template_dir=template_dir,
        out_html=cfg.output_dir / "executive_report.html",
        out_md=cfg.output_dir / "executive_report.md",
    )


def _render_snapshot(*, cfg: AuditConfig) -> None:
    cost_by_service = pd.read_csv(cfg.output_dir / "cost_by_service.csv")
    quick_wins = pd.read_csv(cfg.output_dir / "quick_wins.csv")
    generate_static_dashboard_snapshot(
        cost_by_service=cost_by_service,
        quick_wins=quick_wins,
        out_html=cfg.output_dir / "dashboard_snapshot.html",
    )


def main() -> None:
    app()


if __name__ == "__main__":
    main()
