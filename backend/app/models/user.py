import enum
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class UserRole(str, enum.Enum):
    TRADER = "TRADER"
    SUPERVISOR = "SUPERVISOR"
    HEAD_OF_DESK = "HEAD_OF_DESK"
    MANAGING_DIRECTOR = "MANAGING_DIRECTOR"
    CONTROLS_TEAM = "CONTROLS_TEAM"
    ADMIN = "ADMIN"


class SeniorityLevel(str, enum.Enum):
    ANALYST = "ANALYST"
    ASSOCIATE = "ASSOCIATE"
    VP = "VP"
    DIRECTOR = "DIRECTOR"
    MANAGING_DIRECTOR = "MANAGING_DIRECTOR"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    seniority_level = Column(Enum(SeniorityLevel), nullable=False)
    desk = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    trades = relationship("Trade", back_populates="trader", foreign_keys="Trade.trader_id")
    override_requests = relationship("OverrideRequest", back_populates="requested_by", foreign_keys="OverrideRequest.requested_by_id")
    override_approvals = relationship("OverrideRequest", back_populates="approver", foreign_keys="OverrideRequest.approver_id")
