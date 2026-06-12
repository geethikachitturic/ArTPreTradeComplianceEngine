"""
ArT Rules Engine — orchestrator.

Processes a trade through:
1. Database-stored custom rules (conditions evaluated against trade fields)
2. Regulation T hard-coded checks
3. FINRA Rule 4210 (2026) hard-coded checks

Determines the most severe outcome across all triggered rules:
  CLEAN_PASS < SOFT_BLOCK < HARD_BLOCK_WITH_OVERRIDE < HARD_BLOCK

Returns a structured decision result.
"""
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.engine.reg_t_checks import check_reg_t
from app.engine.finra_4210_checks import check_finra_4210
from app.models.rule import Rule, AssetClassScope, BlockType
from app.models.trade import AssetClass, TradeDirection
from app.models.user import SeniorityLevel


_OUTCOME_SEVERITY = {
    "CLEAN_PASS": 0,
    "SOFT_BLOCK": 1,
    "HARD_BLOCK_WITH_OVERRIDE": 2,
    "HARD_BLOCK": 3,
}

_BLOCK_TO_OUTCOME = {
    BlockType.SOFT_BLOCK: "SOFT_BLOCK",
    BlockType.HARD_BLOCK_WITH_OVERRIDE: "HARD_BLOCK_WITH_OVERRIDE",
    BlockType.HARD_BLOCK: "HARD_BLOCK",
}

_SENIORITY_ORDER = {
    SeniorityLevel.ANALYST: 1,
    SeniorityLevel.ASSOCIATE: 2,
    SeniorityLevel.VP: 3,
    SeniorityLevel.DIRECTOR: 4,
    SeniorityLevel.MANAGING_DIRECTOR: 5,
}


@dataclass
class EngineDecision:
    outcome: str
    rules_triggered: List[Dict[str, Any]] = field(default_factory=list)
    reasoning: str = ""
    reg_t_margin_required: Optional[float] = None
    reg_t_margin_available: Optional[float] = None
    intraday_margin_deficit: Optional[float] = None
    processing_time_ms: int = 0


def _evaluate_condition(condition: Dict[str, Any], trade_data: dict, trader_data: dict) -> bool:
    """Evaluate a single condition rule against trade and trader data."""
    field_name = condition.get("field")
    operator = condition.get("operator")
    value = condition.get("value")

    # Resolve field value
    field_value = None
    if field_name == "notional":
        field_value = trade_data.get("notional", 0)
    elif field_name == "account_equity":
        field_value = trade_data.get("account_equity", 0)
    elif field_name == "margin_ratio":
        equity = trade_data.get("account_equity", 0)
        notional = trade_data.get("notional", 1)
        field_value = equity / notional if notional > 0 else 0
    elif field_name == "intraday_deficit":
        field_value = trade_data.get("intraday_margin_level", 0)
    elif field_name == "trader_seniority":
        seniority_str = trader_data.get("seniority_level", "ANALYST")
        try:
            field_value = _SENIORITY_ORDER.get(SeniorityLevel(seniority_str), 1)
        except ValueError:
            field_value = 1
        # Compare against mapped seniority level value
        try:
            value = _SENIORITY_ORDER.get(SeniorityLevel(value), 1)
        except (ValueError, TypeError):
            value = 1
    elif field_name == "asset_class":
        field_value = trade_data.get("asset_class")
    elif field_name == "direction":
        field_value = trade_data.get("direction")
    else:
        return False

    if field_value is None:
        return False

    # Evaluate operator
    try:
        if operator == ">":
            return float(field_value) > float(value)
        elif operator == ">=":
            return float(field_value) >= float(value)
        elif operator == "<":
            return float(field_value) < float(value)
        elif operator == "<=":
            return float(field_value) <= float(value)
        elif operator == "==":
            return str(field_value) == str(value)
        elif operator == "!=":
            return str(field_value) != str(value)
        elif operator == "in":
            return field_value in value
    except (TypeError, ValueError):
        return False

    return False


def _evaluate_conditions(conditions: Dict[str, Any], trade_data: dict, trader_data: dict) -> bool:
    """Recursively evaluate a conditions tree (AND/OR groups)."""
    if not conditions:
        return False

    logic_type = conditions.get("type", "AND")
    rules = conditions.get("rules", [])

    if not rules:
        return False

    results = []
    for rule in rules:
        if "type" in rule:
            # Nested group
            results.append(_evaluate_conditions(rule, trade_data, trader_data))
        else:
            results.append(_evaluate_condition(rule, trade_data, trader_data))

    if logic_type == "AND":
        return all(results)
    elif logic_type == "OR":
        return any(results)
    return False


def run_engine(trade_data: dict, trader_data: dict, db: Session) -> EngineDecision:
    """
    Main entry point for the ArT rules engine.

    trade_data: dict of trade fields (matches TradeCreate schema)
    trader_data: dict of trader fields (user record)
    db: SQLAlchemy session for loading custom rules
    """
    start_time = time.time()
    triggered_rules: List[Dict[str, Any]] = []
    worst_outcome = "CLEAN_PASS"
    reg_t_margin_required = None
    reg_t_margin_available = None
    intraday_margin_deficit = None

    asset_class = trade_data.get("asset_class")

    # --- 1. Custom rules from database ---
    db_rules = (
        db.query(Rule)
        .filter(Rule.is_active == True)
        .filter(
            (Rule.asset_class_scope == AssetClassScope.ALL) |
            (Rule.asset_class_scope == asset_class)
        )
        .order_by(Rule.priority.asc())
        .all()
    )

    for rule in db_rules:
        if rule.conditions and _evaluate_conditions(rule.conditions, trade_data, trader_data):
            outcome = _BLOCK_TO_OUTCOME.get(rule.block_type, "SOFT_BLOCK")
            triggered_rules.append({
                "rule_id": rule.id,
                "rule_code": rule.rule_code,
                "rule_name": rule.name,
                "rule_type": rule.rule_type,
                "block_type": rule.block_type,
                "outcome": outcome,
                "description": rule.description,
            })
            if _OUTCOME_SEVERITY[outcome] > _OUTCOME_SEVERITY[worst_outcome]:
                worst_outcome = outcome

    # --- 2. Regulation T checks ---
    reg_t_violations = check_reg_t(trade_data)
    for v in reg_t_violations:
        triggered_rules.append({
            "rule_id": None,
            "rule_code": v.rule_code,
            "rule_name": v.rule_name,
            "rule_type": "REG_T",
            "block_type": v.block_type,
            "outcome": v.block_type,
            "description": v.violation_description,
            "margin_required": v.margin_required,
            "margin_available": v.margin_available,
        })
        outcome = v.block_type
        if _OUTCOME_SEVERITY.get(outcome, 0) > _OUTCOME_SEVERITY[worst_outcome]:
            worst_outcome = outcome
        if reg_t_margin_required is None:
            reg_t_margin_required = v.margin_required
            reg_t_margin_available = v.margin_available

    # --- 3. FINRA Rule 4210 checks ---
    finra_violations = check_finra_4210(trade_data)
    for v in finra_violations:
        triggered_rules.append({
            "rule_id": None,
            "rule_code": v.rule_code,
            "rule_name": v.rule_name,
            "rule_type": "FINRA_4210",
            "block_type": v.block_type,
            "outcome": v.block_type,
            "description": v.violation_description,
            "intraday_margin_deficit": v.intraday_margin_deficit if v.intraday_margin_deficit > 0 else None,
            "iml_before": v.iml_before,
            "iml_after": v.iml_after,
        })
        outcome = v.block_type
        if _OUTCOME_SEVERITY.get(outcome, 0) > _OUTCOME_SEVERITY[worst_outcome]:
            worst_outcome = outcome
        if v.intraday_margin_deficit and v.intraday_margin_deficit > 0:
            intraday_margin_deficit = v.intraday_margin_deficit

    # --- 4. Build reasoning summary ---
    if worst_outcome == "CLEAN_PASS":
        reasoning = (
            "Trade passed all pre-trade compliance checks. "
            "No Regulation T violations detected. "
            "No FINRA Rule 4210 intraday margin deficits identified. "
            "No custom control rules triggered. Trade may proceed."
        )
    else:
        rule_names = [r["rule_name"] for r in triggered_rules]
        reasoning = (
            f"ArT outcome: {worst_outcome.replace('_', ' ')}. "
            f"{len(triggered_rules)} rule(s) triggered: {'; '.join(rule_names)}. "
        )
        if worst_outcome == "SOFT_BLOCK":
            reasoning += "Trade carries a compliance warning. Trader should acknowledge the risk before proceeding."
        elif worst_outcome == "HARD_BLOCK_WITH_OVERRIDE":
            reasoning += "Trade is blocked pending supervisory approval. An override request has been raised."
        elif worst_outcome == "HARD_BLOCK":
            reasoning += "Trade is rejected. This is a regulatory hard requirement with no override path."

    elapsed_ms = int((time.time() - start_time) * 1000)

    return EngineDecision(
        outcome=worst_outcome,
        rules_triggered=triggered_rules,
        reasoning=reasoning,
        reg_t_margin_required=reg_t_margin_required,
        reg_t_margin_available=reg_t_margin_available,
        intraday_margin_deficit=intraday_margin_deficit,
        processing_time_ms=elapsed_ms,
    )
