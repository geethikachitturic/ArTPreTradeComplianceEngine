from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from app.models.decision import DecisionOutcome


class ArtDecisionOut(BaseModel):
    id: int
    decision_ref: str
    trade_id: int
    outcome: DecisionOutcome
    rules_triggered: List[Dict[str, Any]]
    reasoning: str
    reg_t_margin_required: Optional[float]
    reg_t_margin_available: Optional[float]
    intraday_margin_deficit: Optional[float]
    processing_time_ms: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}


class TradeCheckResponse(BaseModel):
    trade: Dict[str, Any]
    decision: ArtDecisionOut
    override_request_id: Optional[int] = None
