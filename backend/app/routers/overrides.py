from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.audit import AuditLog
from app.models.override import OverrideRequest, OverrideStatus
from app.models.trade import Trade, TradeStatus
from app.models.user import User
from app.schemas.override import OverrideAction, OverrideOut

router = APIRouter(prefix="/overrides", tags=["Override Approvals"])


@router.get("/", response_model=List[OverrideOut])
def list_overrides(status: str = None, db: Session = Depends(get_db)):
    q = db.query(OverrideRequest).order_by(OverrideRequest.requested_at.desc())
    if status:
        try:
            q = q.filter(OverrideRequest.status == OverrideStatus(status))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    return q.all()


@router.get("/{override_id}", response_model=OverrideOut)
def get_override(override_id: int, db: Session = Depends(get_db)):
    override = db.query(OverrideRequest).filter(OverrideRequest.id == override_id).first()
    if not override:
        raise HTTPException(status_code=404, detail="Override request not found")
    return override


@router.post("/{override_id}/action", response_model=OverrideOut)
def action_override(override_id: int, action: OverrideAction, db: Session = Depends(get_db)):
    """Approve or reject an override request."""
    override = db.query(OverrideRequest).filter(OverrideRequest.id == override_id).first()
    if not override:
        raise HTTPException(status_code=404, detail="Override request not found")

    if override.status != OverrideStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Override is already {override.status.value}")

    approver = db.query(User).filter(User.id == action.approver_id).first()
    if not approver:
        raise HTTPException(status_code=404, detail="Approver not found")

    override.status = action.status
    override.approver_id = action.approver_id
    override.approver_notes = action.approver_notes
    override.resolved_at = datetime.utcnow()

    # Update the trade status to reflect override outcome
    trade = db.query(Trade).filter(Trade.id == override.trade_id).first()
    if trade:
        if action.status == OverrideStatus.APPROVED:
            trade.status = TradeStatus.OVERRIDE_APPROVED
        elif action.status == OverrideStatus.REJECTED:
            trade.status = TradeStatus.OVERRIDE_REJECTED

    db.add(AuditLog(
        event_type="OVERRIDE_" + action.status.value,
        entity_type="OVERRIDE",
        entity_id=override.id,
        user_id=approver.id,
        username=approver.username,
        description=(
            f"Override {override.override_ref} {action.status.value} by {approver.full_name}. "
            f"Notes: {action.approver_notes or 'None'}"
        ),
        event_metadata={
            "override_ref": override.override_ref,
            "trade_id": override.trade_id,
            "risk_score": override.ai_risk_score,
            "risk_band": override.ai_risk_band.value,
        },
    ))

    db.commit()
    db.refresh(override)
    return override


@router.post("/{override_id}/escalate", response_model=OverrideOut)
def escalate_override(override_id: int, escalated_by_id: int, db: Session = Depends(get_db)):
    override = db.query(OverrideRequest).filter(OverrideRequest.id == override_id).first()
    if not override:
        raise HTTPException(status_code=404, detail="Override request not found")

    override.status = OverrideStatus.ESCALATED
    db.add(AuditLog(
        event_type="OVERRIDE_ESCALATED",
        entity_type="OVERRIDE",
        entity_id=override.id,
        user_id=escalated_by_id,
        username=None,
        description=f"Override {override.override_ref} escalated for senior review.",
        event_metadata={"override_ref": override.override_ref},
    ))
    db.commit()
    db.refresh(override)
    return override
