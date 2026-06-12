from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.audit import AuditLog

router = APIRouter(prefix="/audit", tags=["Audit Log"])


@router.get("/")
def list_audit_log(
    days: int = 7,
    event_type: Optional[str] = None,
    entity_type: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    cutoff = datetime.utcnow() - timedelta(days=days)
    q = db.query(AuditLog).filter(AuditLog.created_at >= cutoff)
    if event_type:
        q = q.filter(AuditLog.event_type == event_type)
    if entity_type:
        q = q.filter(AuditLog.entity_type == entity_type)
    return q.order_by(AuditLog.created_at.desc()).limit(limit).all()
