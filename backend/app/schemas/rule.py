from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel

from app.models.rule import RuleType, BlockType, AssetClassScope


class RuleCreate(BaseModel):
    name: str
    description: str
    natural_language_description: Optional[str] = None
    rule_type: RuleType
    asset_class_scope: AssetClassScope = AssetClassScope.ALL
    block_type: BlockType
    conditions: Optional[Dict[str, Any]] = None
    priority: int = 100
    created_by: str = "SYSTEM"


class RuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    natural_language_description: Optional[str] = None
    block_type: Optional[BlockType] = None
    conditions: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None


class RuleOut(BaseModel):
    id: int
    rule_code: str
    name: str
    description: str
    natural_language_description: Optional[str]
    rule_type: RuleType
    asset_class_scope: AssetClassScope
    block_type: BlockType
    conditions: Optional[Dict[str, Any]]
    is_active: bool
    priority: int
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NLRuleInput(BaseModel):
    natural_language: str


class NLRuleParsed(BaseModel):
    name: str
    description: str
    natural_language_description: str
    rule_type: RuleType
    asset_class_scope: AssetClassScope
    block_type: BlockType
    conditions: Dict[str, Any]
    confidence: float
    explanation: str
