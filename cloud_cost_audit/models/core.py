from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Confidence = Literal["high", "med", "low"]
Effort = Literal["S", "M", "L"]


class QuickWin(BaseModel):
    rank: int = Field(ge=1)
    title: str
    description: str
    scope: str
    expected_savings_monthly_usd: float = Field(ge=0.0)
    confidence: Confidence
    risk: str
    effort: Effort
    prerequisites: str
    owner_role: str
    next_action: str
    kpi: str
