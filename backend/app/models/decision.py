import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class DecisionOutcome(str, enum.Enum):
    CLEAN_PASS = "CLEAN_PASS"
    SOFT_BLOCK = "SOFT_BLOCK"
    HARD_BLOCK = "HARD_BLOCK"
    HARD_BLOCK_WITH_OVERRIDE = "HARD_BLOCK_WITH_OVERRIDE"


class ArtDecision(Base):
    __tablename__ = "art_decisions"

    id = Column(Integer, primary_key=True, index=True)
    decision_ref = Column(String(20), unique=True, nullable=False, index=True)
    trade_id = Column(Integer, ForeignKey("trades.id"), nullable=False, unique=True)

    outcome = Column(Enum(DecisionOutcome), nullable=False)
    rules_triggered = Column(JSON, nullable=False, default=list)
    reasoning = Column(Text, nullable=False)
    reg_t_margin_required = Column(Float, nullable=True)
    reg_t_margin_available = Column(Float, nullable=True)
    intraday_margin_deficit = Column(Float, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    trade = relationship("Trade", back_populates="decision")
    override_request = relationship("OverrideRequest", back_populates="decision", uselist=False)
