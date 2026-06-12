from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.models.override import OverrideStatus, RiskBand


class OverrideAction(BaseModel):
    approver_id: int
    status: OverrideStatus
    approver_notes: Optional[str] = None


class OverrideOut(BaseModel):
    id: int
    override_ref: str
    decision_id: int
    trade_id: int
    requested_by_id: int
    approver_id: Optional[int]
    status: OverrideStatus
    ai_risk_score: float
    ai_risk_band: RiskBand
    ai_risk_rationale: str
    trader_justification: Optional[str]
    approver_notes: Optional[str]
    requested_at: datetime
    resolved_at: Optional[datetime]

    model_config = {"from_attributes": True}
