import enum
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class RuleType(str, enum.Enum):
    REG_T = "REG_T"
    FINRA_4210 = "FINRA_4210"
    CUSTOM = "CUSTOM"


class BlockType(str, enum.Enum):
    SOFT_BLOCK = "SOFT_BLOCK"
    HARD_BLOCK = "HARD_BLOCK"
    HARD_BLOCK_WITH_OVERRIDE = "HARD_BLOCK_WITH_OVERRIDE"


class AssetClassScope(str, enum.Enum):
    EQUITY = "EQUITY"
    FIXED_INCOME = "FIXED_INCOME"
    ALL = "ALL"


class Rule(Base):
    __tablename__ = "rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    natural_language_description = Column(Text, nullable=True)

    rule_type = Column(Enum(RuleType), nullable=False)
    asset_class_scope = Column(Enum(AssetClassScope), nullable=False, default=AssetClassScope.ALL)
    block_type = Column(Enum(BlockType), nullable=False)
    conditions = Column(JSON, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=100, nullable=False)
    created_by = Column(String(100), default="SYSTEM", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
