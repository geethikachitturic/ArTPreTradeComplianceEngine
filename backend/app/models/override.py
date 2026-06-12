import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class OverrideStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ESCALATED = "ESCALATED"


class RiskBand(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class OverrideRequest(Base):
    __tablename__ = "override_requests"

    id = Column(Integer, primary_key=True, index=True)
    override_ref = Column(String(20), unique=True, nullable=False, index=True)
    decision_id = Column(Integer, ForeignKey("art_decisions.id"), nullable=False, unique=True)
    trade_id = Column(Integer, ForeignKey("trades.id"), nullable=False)
    requested_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    status = Column(Enum(OverrideStatus), default=OverrideStatus.PENDING, nullable=False)

    ai_risk_score = Column(Float, nullable=False)
    ai_risk_band = Column(Enum(RiskBand), nullable=False)
    ai_risk_rationale = Column(Text, nullable=False)

    trader_justification = Column(Text, nullable=True)
    approver_notes = Column(Text, nullable=True)

    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    decision = relationship("ArtDecision", back_populates="override_request")
    requested_by = relationship("User", back_populates="override_requests", foreign_keys=[requested_by_id])
    approver = relationship("User", back_populates="override_approvals", foreign_keys=[approver_id])
    trade = relationship("Trade")
