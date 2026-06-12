import random
import string
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.engine.ai_simulator import parse_nl_rule
from app.models.rule import Rule
from app.schemas.rule import NLRuleInput, NLRuleParsed, RuleCreate, RuleOut, RuleUpdate

router = APIRouter(prefix="/rules", tags=["Rules"])


def _generate_rule_code() -> str:
    return "CUST-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


@router.get("/", response_model=List[RuleOut])
def list_rules(active_only: bool = False, db: Session = Depends(get_db)):
    q = db.query(Rule).order_by(Rule.priority.asc(), Rule.created_at.desc())
    if active_only:
        q = q.filter(Rule.is_active == True)
    return q.all()


@router.get("/{rule_id}", response_model=RuleOut)
def get_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.post("/", response_model=RuleOut, status_code=201)
def create_rule(rule_in: RuleCreate, db: Session = Depends(get_db)):
    rule = Rule(
        rule_code=_generate_rule_code(),
        name=rule_in.name,
        description=rule_in.description,
        natural_language_description=rule_in.natural_language_description,
        rule_type=rule_in.rule_type,
        asset_class_scope=rule_in.asset_class_scope,
        block_type=rule_in.block_type,
        conditions=rule_in.conditions,
        priority=rule_in.priority,
        created_by=rule_in.created_by,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.patch("/{rule_id}", response_model=RuleOut)
def update_rule(rule_id: int, rule_update: RuleUpdate, db: Session = Depends(get_db)):
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    for field, value in rule_update.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/{rule_id}", status_code=204)
def deactivate_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    rule.is_active = False
    db.commit()


@router.post("/nl-parse", response_model=NLRuleParsed)
def parse_natural_language_rule(body: NLRuleInput):
    """
    AI (simulated) natural language rule parser.
    Takes plain English and returns a structured rule definition for review.
    """
    parsed = parse_nl_rule(body.natural_language)
    return NLRuleParsed(
        name=parsed["name"],
        description=parsed["description"],
        natural_language_description=parsed["natural_language_description"],
        rule_type=parsed["rule_type"],
        asset_class_scope=parsed["asset_class_scope"],
        block_type=parsed["block_type"],
        conditions=parsed["conditions"],
        confidence=parsed["confidence"],
        explanation=parsed["explanation"],
    )


@router.post("/nl-create", response_model=RuleOut, status_code=201)
def create_from_natural_language(body: NLRuleInput, db: Session = Depends(get_db)):
    """Parse and immediately persist a natural language rule."""
    parsed = parse_nl_rule(body.natural_language)
    rule = Rule(
        rule_code=_generate_rule_code(),
        name=parsed["name"],
        description=parsed["description"],
        natural_language_description=parsed["natural_language_description"],
        rule_type=parsed["rule_type"],
        asset_class_scope=parsed["asset_class_scope"],
        block_type=parsed["block_type"],
        conditions=parsed["conditions"],
        priority=parsed.get("priority", 50),
        created_by=parsed.get("created_by", "AI_NL_BUILDER"),
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule
