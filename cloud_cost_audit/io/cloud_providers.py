from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from cloud_cost_audit.io.paths import DataPaths


class MockAwsProvider:
    def __init__(self, data_dir: Path) -> None:
        self._paths = DataPaths(data_dir)

    def billing(self) -> pd.DataFrame:
        return pd.read_csv(self._paths.aws_billing_csv)

    def inventory(self) -> pd.DataFrame:
        df = pd.read_csv(self._paths.inventory_csv)
        return df[df["provider"] == "aws"].reset_index(drop=True)

    def utilization(self) -> pd.DataFrame:
        df = pd.read_csv(self._paths.utilization_csv)
        return df[df["provider"] == "aws"].reset_index(drop=True)


class MockGcpProvider:
    def __init__(self, data_dir: Path) -> None:
        self._paths = DataPaths(data_dir)

    def billing(self) -> pd.DataFrame:
        return pd.read_csv(self._paths.gcp_billing_csv)

    def inventory(self) -> pd.DataFrame:
        df = pd.read_csv(self._paths.inventory_csv)
        return df[df["provider"] == "gcp"].reset_index(drop=True)

    def utilization(self) -> pd.DataFrame:
        df = pd.read_csv(self._paths.utilization_csv)
        return df[df["provider"] == "gcp"].reset_index(drop=True)


@dataclass(frozen=True)
class Providers:
    aws: MockAwsProvider
    gcp: MockGcpProvider

    @staticmethod
    def from_data_dir(data_dir: Path) -> Providers:
        return Providers(aws=MockAwsProvider(data_dir), gcp=MockGcpProvider(data_dir))
