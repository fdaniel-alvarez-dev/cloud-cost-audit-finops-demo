from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

from cloud_cost_audit.io.paths import DataPaths


@dataclass(frozen=True)
class SyntheticDataSummary:
    invoice_month: str
    baseline_cost_usd: float


def _month_bounds(invoice_month: str) -> tuple[date, date]:
    year, month = (int(x) for x in invoice_month.split("-", 1))
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(year, month + 1, 1) - timedelta(days=1)
    return start, end


def ensure_synthetic_inputs(*, data_dir: Path, invoice_month: str) -> SyntheticDataSummary:
    paths = DataPaths(data_dir)
    paths.generated_dir.mkdir(parents=True, exist_ok=True)

    if (
        paths.aws_billing_csv.exists()
        and paths.gcp_billing_csv.exists()
        and paths.inventory_csv.exists()
        and paths.utilization_csv.exists()
    ):
        baseline = _compute_baseline_cost(paths)
        return SyntheticDataSummary(invoice_month=invoice_month, baseline_cost_usd=baseline)

    start, end = _month_bounds(invoice_month)
    start_dt = datetime.combine(start, datetime.min.time())
    end_dt = datetime.combine(end, datetime.max.time()).replace(microsecond=0)

    aws_rows: list[dict[str, object]] = []
    gcp_rows: list[dict[str, object]] = []

    def aws_line(
        *,
        account_id: str,
        payer_account_id: str,
        region: str,
        service: str,
        usage_type: str,
        operation: str,
        resource_id: str,
        env: str | None,
        app: str | None,
        team: str | None,
        cost_center: str | None,
        cost_usd: float,
        usage_amount: float,
        pricing_unit: str,
        line_item_type: str = "Usage",
    ) -> None:
        aws_rows.append(
            {
                "account_id": account_id,
                "payer_account_id": payer_account_id,
                "region": region,
                "service": service,
                "usage_type": usage_type,
                "operation": operation,
                "resource_id": resource_id,
                "tag_env": env,
                "tag_app": app,
                "tag_team": team,
                "tag_cost_center": cost_center,
                "cost_usd": cost_usd,
                "usage_amount": usage_amount,
                "pricing_unit": pricing_unit,
                "line_item_type": line_item_type,
                "invoice_month": invoice_month,
                "usage_start_time": start_dt.isoformat(),
                "usage_end_time": end_dt.isoformat(),
            }
        )

    def gcp_line(
        *,
        billing_account_id: str,
        project_id: str,
        location: str,
        service_description: str,
        sku_description: str,
        env: str | None,
        app: str | None,
        team: str | None,
        cost_center: str | None,
        cost_usd: float,
        credits_usd: float,
        usage_amount: float,
        usage_unit: str,
    ) -> None:
        gcp_rows.append(
            {
                "billing_account_id": billing_account_id,
                "project_id": project_id,
                "location": location,
                "service_description": service_description,
                "sku_description": sku_description,
                "label_env": env,
                "label_app": app,
                "label_team": team,
                "label_cost_center": cost_center,
                "cost_usd": cost_usd,
                "credits_usd": credits_usd,
                "usage_amount": usage_amount,
                "usage_unit": usage_unit,
                "invoice_month": invoice_month,
                "usage_start_time": start_dt.isoformat(),
                "usage_end_time": end_dt.isoformat(),
            }
        )

    # AWS baseline ~12k
    aws_line(
        account_id="111111111111",
        payer_account_id="999999999999",
        region="us-east-1",
        service="AmazonEC2",
        usage_type="Compute",
        operation="RunInstances",
        resource_id="i-prod-app-1",
        env="prod",
        app="app",
        team="core-platform",
        cost_center="cc-100",
        cost_usd=3100.0,
        usage_amount=720.0,
        pricing_unit="Hours",
    )
    aws_line(
        account_id="111111111111",
        payer_account_id="999999999999",
        region="us-east-1",
        service="AmazonEC2",
        usage_type="Compute",
        operation="RunInstances",
        resource_id="i-prod-app-2",
        env="prod",
        app="app",
        team="core-platform",
        cost_center="cc-100",
        cost_usd=2400.0,
        usage_amount=720.0,
        pricing_unit="Hours",
    )
    aws_line(
        account_id="222222222222",
        payer_account_id="999999999999",
        region="us-west-2",
        service="AmazonEC2",
        usage_type="Compute",
        operation="RunInstances",
        resource_id="i-dev-batch-1",
        env="dev",
        app="batch",
        team="data",
        cost_center=None,  # intentionally missing for allocation gap
        cost_usd=1600.0,
        usage_amount=720.0,
        pricing_unit="Hours",
    )
    aws_line(
        account_id="111111111111",
        payer_account_id="999999999999",
        region="us-east-1",
        service="AmazonRDS",
        usage_type="DBInstance",
        operation="CreateDBInstance",
        resource_id="db-prod-1",
        env="prod",
        app="app",
        team="core-platform",
        cost_center="cc-100",
        cost_usd=2000.0,
        usage_amount=720.0,
        pricing_unit="Hours",
    )
    aws_line(
        account_id="111111111111",
        payer_account_id="999999999999",
        region="us-east-1",
        service="AmazonS3",
        usage_type="TimedStorage-ByteHrs",
        operation="StandardStorage",
        resource_id="s3://prod-logs",
        env="prod",
        app="app",
        team="core-platform",
        cost_center="cc-100",
        cost_usd=1000.0,
        usage_amount=50_000.0,
        pricing_unit="GB-Month",
    )
    aws_line(
        account_id="111111111111",
        payer_account_id="999999999999",
        region="us-east-1",
        service="AWSDataTransfer",
        usage_type="Egress",
        operation="Internet",
        resource_id="egress:internet",
        env="prod",
        app="app",
        team="core-platform",
        cost_center="cc-100",
        cost_usd=700.0,
        usage_amount=7_000.0,
        pricing_unit="GB",
    )
    aws_line(
        account_id="111111111111",
        payer_account_id="999999999999",
        region="us-east-1",
        service="AmazonCloudWatch",
        usage_type="Metrics",
        operation="PutMetricData",
        resource_id="cloudwatch:metrics",
        env="prod",
        app="app",
        team="core-platform",
        cost_center="cc-100",
        cost_usd=700.0,
        usage_amount=10_000.0,
        pricing_unit="Metric",
    )
    aws_line(
        account_id="222222222222",
        payer_account_id="999999999999",
        region="us-west-2",
        service="AmazonEBS",
        usage_type="Storage",
        operation="VolumeUsage",
        resource_id="vol-orphan-1",
        env=None,
        app=None,
        team=None,
        cost_center=None,
        cost_usd=200.0,
        usage_amount=2_000.0,
        pricing_unit="GB-Month",
    )

    # GCP baseline ~8k
    gcp_line(
        billing_account_id="0000-AAAA-1111",
        project_id="saas-prod",
        location="us-central1",
        service_description="Compute Engine",
        sku_description="N2 Standard Core running in Americas",
        env="prod",
        app="app",
        team="core-platform",
        cost_center="cc-200",
        cost_usd=4500.0,
        credits_usd=150.0,
        usage_amount=3_000.0,
        usage_unit="vCPU-hours",
    )
    gcp_line(
        billing_account_id="0000-AAAA-1111",
        project_id="saas-prod",
        location="us-central1",
        service_description="Cloud SQL",
        sku_description="PostgreSQL instance",
        env="prod",
        app="app",
        team="core-platform",
        cost_center="cc-200",
        cost_usd=1500.0,
        credits_usd=0.0,
        usage_amount=720.0,
        usage_unit="hours",
    )
    gcp_line(
        billing_account_id="0000-AAAA-1111",
        project_id="saas-prod",
        location="us-central1",
        service_description="Cloud Storage",
        sku_description="Standard Storage",
        env="prod",
        app="app",
        team="core-platform",
        cost_center="cc-200",
        cost_usd=800.0,
        credits_usd=0.0,
        usage_amount=40_000.0,
        usage_unit="GB-month",
    )
    gcp_line(
        billing_account_id="0000-AAAA-1111",
        project_id="saas-prod",
        location="global",
        service_description="Networking",
        sku_description="Egress to Internet",
        env="prod",
        app="app",
        team="core-platform",
        cost_center="cc-200",
        cost_usd=700.0,
        credits_usd=0.0,
        usage_amount=6_000.0,
        usage_unit="GB",
    )
    gcp_line(
        billing_account_id="0000-AAAA-1111",
        project_id="saas-dev",
        location="us-central1",
        service_description="Compute Engine",
        sku_description="E2 Standard Core running in Americas",
        env="dev",
        app="batch",
        team="data",
        cost_center=None,  # intentionally missing
        cost_usd=500.0,
        credits_usd=0.0,
        usage_amount=600.0,
        usage_unit="vCPU-hours",
    )
    gcp_line(
        billing_account_id="0000-AAAA-1111",
        project_id="saas-prod",
        location="US",
        service_description="BigQuery",
        sku_description="Analysis",
        env="prod",
        app="app",
        team="data",
        cost_center="cc-200",
        cost_usd=450.0,
        credits_usd=0.0,
        usage_amount=2_000.0,
        usage_unit="GB",
    )

    aws_df = pd.DataFrame(aws_rows)
    gcp_df = pd.DataFrame(gcp_rows)

    # Inventory and utilization to support waste detection
    inventory_rows: list[dict[str, object]] = [
        {
            "provider": "aws",
            "resource_id": "i-prod-app-1",
            "resource_type": "instance",
            "service": "EC2",
            "region": "us-east-1",
            "name": "prod-app-1",
            "env": "prod",
            "app": "app",
            "team": "core-platform",
            "cost_center": "cc-100",
            "status": "running",
            "created_at": (start - timedelta(days=120)).isoformat(),
            "attached_to": "",
            "monthly_cost_estimate_usd": 3100.0,
        },
        {
            "provider": "aws",
            "resource_id": "i-prod-app-2",
            "resource_type": "instance",
            "service": "EC2",
            "region": "us-east-1",
            "name": "prod-app-2",
            "env": "prod",
            "app": "app",
            "team": "core-platform",
            "cost_center": "cc-100",
            "status": "running",
            "created_at": (start - timedelta(days=200)).isoformat(),
            "attached_to": "",
            "monthly_cost_estimate_usd": 2400.0,
        },
        {
            "provider": "aws",
            "resource_id": "i-dev-batch-1",
            "resource_type": "instance",
            "service": "EC2",
            "region": "us-west-2",
            "name": "dev-batch-1",
            "env": "dev",
            "app": "batch",
            "team": "data",
            "cost_center": "",
            "status": "running",
            "created_at": (start - timedelta(days=30)).isoformat(),
            "attached_to": "",
            "monthly_cost_estimate_usd": 1600.0,
        },
        {
            "provider": "aws",
            "resource_id": "vol-orphan-1",
            "resource_type": "volume",
            "service": "EBS",
            "region": "us-west-2",
            "name": "orphan-ebs-1",
            "env": "",
            "app": "",
            "team": "",
            "cost_center": "",
            "status": "available",
            "created_at": (start - timedelta(days=60)).isoformat(),
            "attached_to": "",
            "monthly_cost_estimate_usd": 200.0,
        },
        {
            "provider": "aws",
            "resource_id": "eip-unused-1",
            "resource_type": "ip",
            "service": "EC2",
            "region": "us-east-1",
            "name": "unused-eip-1",
            "env": "",
            "app": "",
            "team": "",
            "cost_center": "",
            "status": "unassociated",
            "created_at": (start - timedelta(days=90)).isoformat(),
            "attached_to": "",
            "monthly_cost_estimate_usd": 120.0,
        },
        {
            "provider": "aws",
            "resource_id": "snap-old-1",
            "resource_type": "snapshot",
            "service": "EBS",
            "region": "us-east-1",
            "name": "old-snap-1",
            "env": "",
            "app": "",
            "team": "",
            "cost_center": "",
            "status": "completed",
            "created_at": (start - timedelta(days=180)).isoformat(),
            "attached_to": "",
            "monthly_cost_estimate_usd": 180.0,
        },
        {
            "provider": "gcp",
            "resource_id": "gce-prod-1",
            "resource_type": "instance",
            "service": "Compute Engine",
            "region": "us-central1",
            "name": "gce-prod-1",
            "env": "prod",
            "app": "app",
            "team": "core-platform",
            "cost_center": "cc-200",
            "status": "running",
            "created_at": (start - timedelta(days=365)).isoformat(),
            "attached_to": "",
            "monthly_cost_estimate_usd": 2200.0,
        },
        {
            "provider": "gcp",
            "resource_id": "gce-prod-2",
            "resource_type": "instance",
            "service": "Compute Engine",
            "region": "us-central1",
            "name": "gce-prod-2",
            "env": "prod",
            "app": "app",
            "team": "core-platform",
            "cost_center": "cc-200",
            "status": "running",
            "created_at": (start - timedelta(days=220)).isoformat(),
            "attached_to": "",
            "monthly_cost_estimate_usd": 1800.0,
        },
        {
            "provider": "gcp",
            "resource_id": "pd-orphan-1",
            "resource_type": "disk",
            "service": "Compute Engine",
            "region": "us-central1",
            "name": "orphan-pd-1",
            "env": "",
            "app": "",
            "team": "",
            "cost_center": "",
            "status": "unattached",
            "created_at": (start - timedelta(days=45)).isoformat(),
            "attached_to": "",
            "monthly_cost_estimate_usd": 140.0,
        },
    ]
    utilization_rows: list[dict[str, object]] = [
        {
            "provider": "aws",
            "resource_id": "i-prod-app-1",
            "avg_cpu_pct": 6.0,  # underutilized
            "avg_mem_pct": 35.0,
            "avg_network_mbps": 5.2,
            "period_start": start_dt.isoformat(),
            "period_end": end_dt.isoformat(),
        },
        {
            "provider": "aws",
            "resource_id": "i-prod-app-2",
            "avg_cpu_pct": 8.5,  # underutilized
            "avg_mem_pct": 40.0,
            "avg_network_mbps": 4.1,
            "period_start": start_dt.isoformat(),
            "period_end": end_dt.isoformat(),
        },
        {
            "provider": "aws",
            "resource_id": "i-dev-batch-1",
            "avg_cpu_pct": 4.0,
            "avg_mem_pct": 15.0,
            "avg_network_mbps": 1.0,
            "period_start": start_dt.isoformat(),
            "period_end": end_dt.isoformat(),
        },
        {
            "provider": "gcp",
            "resource_id": "gce-prod-1",
            "avg_cpu_pct": 7.0,  # underutilized
            "avg_mem_pct": 30.0,
            "avg_network_mbps": 6.0,
            "period_start": start_dt.isoformat(),
            "period_end": end_dt.isoformat(),
        },
        {
            "provider": "gcp",
            "resource_id": "gce-prod-2",
            "avg_cpu_pct": 11.0,
            "avg_mem_pct": 42.0,
            "avg_network_mbps": 7.2,
            "period_start": start_dt.isoformat(),
            "period_end": end_dt.isoformat(),
        },
    ]

    aws_df.to_csv(paths.aws_billing_csv, index=False)
    gcp_df.to_csv(paths.gcp_billing_csv, index=False)
    pd.DataFrame(inventory_rows).to_csv(paths.inventory_csv, index=False)
    pd.DataFrame(utilization_rows).to_csv(paths.utilization_csv, index=False)

    baseline = _compute_baseline_cost(paths)
    return SyntheticDataSummary(invoice_month=invoice_month, baseline_cost_usd=baseline)


def _compute_baseline_cost(paths: DataPaths) -> float:
    aws = pd.read_csv(paths.aws_billing_csv)
    gcp = pd.read_csv(paths.gcp_billing_csv)
    gcp_net = (gcp["cost_usd"] - gcp["credits_usd"]).sum()
    return float(aws["cost_usd"].sum() + gcp_net)
