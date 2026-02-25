from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DataPaths:
    base_dir: Path

    @property
    def generated_dir(self) -> Path:
        return self.base_dir / "generated"

    @property
    def aws_billing_csv(self) -> Path:
        return self.generated_dir / "aws_cur.csv"

    @property
    def gcp_billing_csv(self) -> Path:
        return self.generated_dir / "gcp_billing.csv"

    @property
    def inventory_csv(self) -> Path:
        return self.generated_dir / "inventory.csv"

    @property
    def utilization_csv(self) -> Path:
        return self.generated_dir / "utilization.csv"
