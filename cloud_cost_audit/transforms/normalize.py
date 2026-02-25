from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

REQUIRED_AWS_COLUMNS = {
    "account_id",
    "payer_account_id",
    "region",
    "service",
    "usage_type",
    "operation",
    "resource_id",
    "tag_env",
    "tag_app",
    "tag_team",
    "tag_cost_center",
    "cost_usd",
    "usage_amount",
    "pricing_unit",
    "line_item_type",
    "invoice_month",
    "usage_start_time",
    "usage_end_time",
}

REQUIRED_GCP_COLUMNS = {
    "billing_account_id",
    "project_id",
    "location",
    "service_description",
    "sku_description",
    "label_env",
    "label_app",
    "label_team",
    "label_cost_center",
    "cost_usd",
    "credits_usd",
    "usage_amount",
    "usage_unit",
    "invoice_month",
    "usage_start_time",
    "usage_end_time",
}


def _validate_columns(df: pd.DataFrame, required: set[str], *, name: str) -> None:
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"{name} is missing required columns: {missing}")


def normalize_aws_billing(df: pd.DataFrame) -> pd.DataFrame:
    _validate_columns(df, REQUIRED_AWS_COLUMNS, name="AWS billing input")
    out = pd.DataFrame(
        {
            "provider": "aws",
            "account": df["account_id"].astype(str),
            "project": "",
            "region": df["region"].astype(str),
            "service": df["service"].astype(str),
            "sku": df["usage_type"].astype(str),
            "operation": df["operation"].astype(str),
            "resource_id": df["resource_id"].astype(str),
            "env": df["tag_env"].fillna("").astype(str),
            "app": df["tag_app"].fillna("").astype(str),
            "team": df["tag_team"].fillna("").astype(str),
            "cost_center": df["tag_cost_center"].fillna("").astype(str),
            "cost_usd": df["cost_usd"].astype(float),
            "usage_amount": df["usage_amount"].astype(float),
            "unit": df["pricing_unit"].astype(str),
            "line_item_type": df["line_item_type"].astype(str),
            "invoice_month": df["invoice_month"].astype(str),
            "usage_start_time": df["usage_start_time"].astype(str),
            "usage_end_time": df["usage_end_time"].astype(str),
        }
    )
    return out


def normalize_gcp_billing(df: pd.DataFrame) -> pd.DataFrame:
    _validate_columns(df, REQUIRED_GCP_COLUMNS, name="GCP billing input")
    net_cost = (df["cost_usd"].astype(float) - df["credits_usd"].astype(float)).clip(lower=0.0)
    out = pd.DataFrame(
        {
            "provider": "gcp",
            "account": df["billing_account_id"].astype(str),
            "project": df["project_id"].astype(str),
            "region": df["location"].astype(str),
            "service": df["service_description"].astype(str),
            "sku": df["sku_description"].astype(str),
            "operation": "",
            "resource_id": "",
            "env": df["label_env"].fillna("").astype(str),
            "app": df["label_app"].fillna("").astype(str),
            "team": df["label_team"].fillna("").astype(str),
            "cost_center": df["label_cost_center"].fillna("").astype(str),
            "cost_usd": net_cost.astype(float),
            "usage_amount": df["usage_amount"].astype(float),
            "unit": df["usage_unit"].astype(str),
            "line_item_type": "Usage",
            "invoice_month": df["invoice_month"].astype(str),
            "usage_start_time": df["usage_start_time"].astype(str),
            "usage_end_time": df["usage_end_time"].astype(str),
        }
    )
    return out


def unify_line_items(parts: Iterable[pd.DataFrame]) -> pd.DataFrame:
    df = pd.concat(list(parts), ignore_index=True)
    # Normalize blanks to empty strings for allocation keys.
    for col in ["env", "app", "team", "cost_center"]:
        df[col] = df[col].fillna("").astype(str)
    return df
