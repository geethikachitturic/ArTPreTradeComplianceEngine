"""
Simulated AI layer for ArT.

Three capabilities:
1. NL Rules Builder — parses plain English into structured rule definitions
2. Risk Scorer — scores override requests on 0-100 risk scale
3. NL Reporter — translates natural language queries into report filters + summary text
"""
import math
import re
from typing import Any, Dict, List, Optional, Tuple

from app.models.rule import AssetClassScope, BlockType, RuleType
from app.models.override import RiskBand


# ---------------------------------------------------------------------------
# 1. Natural Language Rules Builder
# ---------------------------------------------------------------------------

_ASSET_PATTERNS = {
    AssetClassScope.EQUITY: [
        r"\b(equit(y|ies)|stock|share|etf)\b"
    ],
    AssetClassScope.FIXED_INCOME: [
        r"\b(fixed income|bond|debt|credit|corporate bond|govt bond|treasury)\b"
    ],
}

_BLOCK_PATTERNS = {
    BlockType.HARD_BLOCK: [
        r"\b(hard block|reject|prohibit|deny|must not|cannot proceed|block entirely)\b"
    ],
    BlockType.HARD_BLOCK_WITH_OVERRIDE: [
        r"\b(override|escalat|supervisor|approval required|require approval)\b"
    ],
    BlockType.SOFT_BLOCK: [
        r"\b(warn|soft block|alert|notify|caution|flag)\b"
    ],
}

_CONDITION_PATTERNS = [
    # Notional size
    (r"notional\s+(exceeds?|above|greater than|>)\s*\$?([\d,\.]+[mk]?)", "notional_gt"),
    (r"notional\s+(below|less than|under|<)\s*\$?([\d,\.]+[mk]?)", "notional_lt"),
    # Trader seniority
    (r"trader(s?)\s+(below|under)\s+(analyst|associate|vp|director|md|managing director)", "seniority_below"),
    (r"trader(s?)\s+(above|over|at least)\s+(analyst|associate|vp|director|md|managing director)", "seniority_above"),
    # Account equity / margin ratio
    (r"(account equity|margin ratio|equity)\s+(below|less than|under)\s+([\d\.]+)%?", "equity_below"),
    (r"(account equity|margin)\s+(above|greater than|exceeds?)\s+([\d\.]+)%?", "equity_above"),
    # Intraday deficit
    (r"(intraday|iml)\s+(deficit|shortfall)\s+(exceeds?|above|greater than)\s*\$?([\d,\.]+[mk]?)", "deficit_gt"),
]

_SENIORITY_MAP = {
    "analyst": "ANALYST",
    "associate": "ASSOCIATE",
    "vp": "VP",
    "director": "DIRECTOR",
    "md": "MANAGING_DIRECTOR",
    "managing director": "MANAGING_DIRECTOR",
}


def _parse_amount(raw: str) -> float:
    raw = raw.replace(",", "").lower().strip()
    multiplier = 1
    if raw.endswith("m"):
        multiplier = 1_000_000
        raw = raw[:-1]
    elif raw.endswith("k"):
        multiplier = 1_000
        raw = raw[:-1]
    return float(raw) * multiplier


def parse_nl_rule(natural_language: str) -> Dict[str, Any]:
    """
    Parse a plain-English rule description into a structured rule definition.
    Returns dict compatible with RuleCreate schema.
    """
    text = natural_language.lower().strip()

    # Detect asset class scope
    scope = AssetClassScope.ALL
    for asset_class, patterns in _ASSET_PATTERNS.items():
        if any(re.search(p, text) for p in patterns):
            scope = asset_class
            break

    # Detect block type (check most specific first)
    block_type = BlockType.SOFT_BLOCK  # default
    for bt, patterns in _BLOCK_PATTERNS.items():
        if any(re.search(p, text) for p in patterns):
            block_type = bt
            break

    # Extract conditions
    conditions: Dict[str, Any] = {"type": "AND", "rules": []}
    confidence_factors = []

    for pattern, condition_type in _CONDITION_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue

        if condition_type == "notional_gt":
            amount = _parse_amount(match.group(2))
            conditions["rules"].append({
                "field": "notional",
                "operator": ">",
                "value": amount,
                "label": f"Notional > ${amount:,.0f}",
            })
            confidence_factors.append(0.9)

        elif condition_type == "notional_lt":
            amount = _parse_amount(match.group(2))
            conditions["rules"].append({
                "field": "notional",
                "operator": "<",
                "value": amount,
                "label": f"Notional < ${amount:,.0f}",
            })
            confidence_factors.append(0.9)

        elif condition_type == "seniority_below":
            level = _SENIORITY_MAP.get(match.group(3).lower(), "VP")
            conditions["rules"].append({
                "field": "trader_seniority",
                "operator": "<",
                "value": level,
                "label": f"Trader seniority below {level}",
            })
            confidence_factors.append(0.85)

        elif condition_type == "equity_below":
            pct = float(match.group(3)) / 100 if float(match.group(3)) > 1 else float(match.group(3))
            conditions["rules"].append({
                "field": "margin_ratio",
                "operator": "<",
                "value": pct,
                "label": f"Account equity/margin ratio below {pct*100:.0f}%",
            })
            confidence_factors.append(0.80)

        elif condition_type == "deficit_gt":
            amount = _parse_amount(match.group(4))
            conditions["rules"].append({
                "field": "intraday_deficit",
                "operator": ">",
                "value": amount,
                "label": f"Intraday deficit > ${amount:,.0f}",
            })
            confidence_factors.append(0.88)

    # Generate a readable name
    scope_label = {"EQUITY": "Equity", "FIXED_INCOME": "Fixed Income", "ALL": "All Asset Class"}[scope]
    block_label = {
        BlockType.SOFT_BLOCK: "Warning",
        BlockType.HARD_BLOCK: "Hard Block",
        BlockType.HARD_BLOCK_WITH_OVERRIDE: "Override Required",
    }[block_type]
    rule_name = f"Custom — {scope_label} {block_label} Rule"

    # Build plain English explanation of what was parsed
    condition_labels = [r["label"] for r in conditions["rules"]]
    if condition_labels:
        conditions_text = " AND ".join(condition_labels)
        explanation = (
            f"I identified this as a {block_label} rule applying to {scope_label} trades "
            f"where: {conditions_text}. "
            f"The rule will fire when all conditions are met simultaneously."
        )
    else:
        explanation = (
            f"I identified this as a {block_label} rule for {scope_label} trades. "
            f"I could not extract specific numeric conditions — please review and add conditions manually."
        )
        confidence_factors.append(0.40)

    avg_confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.50

    # Determine rule type
    rule_type = RuleType.CUSTOM
    if any(kw in text for kw in ["reg t", "regulation t", "initial margin", "50%"]):
        rule_type = RuleType.REG_T
    elif any(kw in text for kw in ["4210", "intraday", "iml", "deficit", "freeze"]):
        rule_type = RuleType.FINRA_4210

    return {
        "name": rule_name,
        "description": natural_language,
        "natural_language_description": natural_language,
        "rule_type": rule_type,
        "asset_class_scope": scope,
        "block_type": block_type,
        "conditions": conditions,
        "confidence": round(avg_confidence, 2),
        "explanation": explanation,
        "priority": 50,
        "created_by": "AI_NL_BUILDER",
    }


# ---------------------------------------------------------------------------
# 2. Override Risk Scorer
# ---------------------------------------------------------------------------

_SENIORITY_RISK_WEIGHT = {
    "ANALYST": 25,
    "ASSOCIATE": 18,
    "VP": 10,
    "DIRECTOR": 5,
    "MANAGING_DIRECTOR": 2,
}


def score_override_risk(trade_data: dict, decision_data: dict, override_history: dict) -> Dict[str, Any]:
    """
    Produce a 0-100 risk score for an override request.
    Higher score = higher risk of allowing the override.
    """
    score = 0.0
    factors = []

    notional = trade_data.get("notional", 0)
    account_equity = trade_data.get("account_equity", 1)
    deficit = decision_data.get("intraday_margin_deficit", 0) or 0
    seniority = trade_data.get("trader_seniority", "ANALYST")
    past_overrides_30d = override_history.get("approved_30d", 0)
    past_rejections_30d = override_history.get("rejected_30d", 0)
    rules_triggered = decision_data.get("rules_triggered", [])
    has_reg_t_violation = any(r.get("rule_code", "").startswith("REGT") for r in rules_triggered)

    # Notional size risk (0-30 pts) — log scale
    if notional > 0:
        notional_pts = min(30, math.log10(max(notional, 1)) * 5)
        score += notional_pts
        factors.append(f"Trade size ${notional:,.0f} contributes {notional_pts:.0f} risk points (scale: $1M=15pts, $10M=20pts, $100M=25pts).")

    # Deficit severity (0-25 pts)
    if deficit > 0 and account_equity > 0:
        deficit_ratio = deficit / account_equity
        deficit_pts = min(25, deficit_ratio * 100)
        score += deficit_pts
        factors.append(f"Intraday margin deficit ${deficit:,.0f} ({deficit_ratio*100:.1f}% of equity) contributes {deficit_pts:.0f} risk points.")

    # Trader seniority (0-20 pts) — junior traders carry more risk
    seniority_pts = _SENIORITY_RISK_WEIGHT.get(seniority, 15)
    score += seniority_pts
    factors.append(f"Trader seniority {seniority} contributes {seniority_pts} risk points (junior = higher risk).")

    # Override history (0-15 pts)
    history_pts = min(15, past_overrides_30d * 3 + past_rejections_30d * 2)
    score += history_pts
    if past_overrides_30d > 0 or past_rejections_30d > 0:
        factors.append(
            f"Override history: {past_overrides_30d} approved, {past_rejections_30d} rejected in past 30 days "
            f"({history_pts} risk points)."
        )

    # Regulatory rule type (0-10 pts) — Reg T violations are more serious
    if has_reg_t_violation:
        score += 10
        factors.append("Regulation T violation present: +10 risk points (regulatory hard requirement).")

    score = min(100, round(score, 1))

    # Determine risk band
    if score <= 30:
        band = RiskBand.LOW
        recommendation = "Low risk override. Likely appropriate to approve with standard documentation."
    elif score <= 60:
        band = RiskBand.MEDIUM
        recommendation = "Medium risk. Approve only with satisfactory trader justification and supervisor sign-off."
    elif score <= 80:
        band = RiskBand.HIGH
        recommendation = "High risk override. Recommend escalation to Head of Desk before approval. Ensure full audit trail."
    else:
        band = RiskBand.CRITICAL
        recommendation = "Critical risk. Strong recommendation to reject. If approved, requires MD-level sign-off and immediate regulatory notification review."

    rationale = (
        f"AI Risk Assessment — Score {score}/100 ({band.value}). "
        + " ".join(factors)
        + f" Recommendation: {recommendation}"
    )

    return {
        "score": score,
        "band": band,
        "rationale": rationale,
        "factors": factors,
        "recommendation": recommendation,
    }


# ---------------------------------------------------------------------------
# 3. Natural Language Reporter
# ---------------------------------------------------------------------------

_TIME_PATTERNS = {
    "today": {"days": 0},
    "yesterday": {"days": 1},
    "last week": {"days": 7},
    "past week": {"days": 7},
    "last month": {"days": 30},
    "past month": {"days": 30},
    "last quarter": {"days": 90},
    "past 30 days": {"days": 30},
    "past 7 days": {"days": 7},
    "year to date": {"days": 365},
}

_OUTCOME_PATTERNS = {
    "clean pass": "CLEAN_PASS",
    "pass": "CLEAN_PASS",
    "soft block": "SOFT_BLOCK",
    "hard block with override": "HARD_BLOCK_WITH_OVERRIDE",
    "override": "HARD_BLOCK_WITH_OVERRIDE",
    "hard block": "HARD_BLOCK",
    "block": None,  # any block type
}

_ASSET_CLASS_PATTERNS = {
    r"\b(equit(y|ies)|stock)\b": "EQUITY",
    r"\bfixed income\b|\bbond\b": "FIXED_INCOME",
}


def parse_nl_query(query: str) -> Dict[str, Any]:
    """
    Parse a natural language reporting query into structured filter parameters
    and generate a descriptive summary template.
    """
    text = query.lower().strip()
    filters: Dict[str, Any] = {}
    description_parts = []

    # Time period
    for phrase, time_filter in _TIME_PATTERNS.items():
        if phrase in text:
            filters["days_back"] = time_filter["days"]
            description_parts.append(f"over the {'past ' + str(time_filter['days']) + ' days' if time_filter['days'] > 0 else 'today'}")
            break
    if "days_back" not in filters:
        filters["days_back"] = 30
        description_parts.append("over the past 30 days (default)")

    # Outcome filter
    for phrase, outcome in _OUTCOME_PATTERNS.items():
        if phrase in text:
            filters["outcome"] = outcome
            label = phrase.replace("_", " ").title()
            description_parts.append(f"filtered to {label} decisions")
            break

    # Asset class
    for pattern, asset_class in _ASSET_CLASS_PATTERNS.items():
        if re.search(pattern, text):
            filters["asset_class"] = asset_class
            description_parts.append(f"for {asset_class.replace('_', ' ').title()} trades")
            break

    # Specific trader mention
    trader_match = re.search(r"\btrader\s+([a-z]+(?:\s+[a-z]+)?)\b", text)
    if trader_match:
        filters["trader_name"] = trader_match.group(1).title()
        description_parts.append(f"for trader {filters['trader_name']}")

    # Aggregation intent
    if any(kw in text for kw in ["most", "top", "highest", "which trader", "which rule"]):
        filters["aggregate"] = True
        filters["sort"] = "count_desc"
        filters["limit"] = 10

    if any(kw in text for kw in ["rule", "rules triggered", "which rule"]):
        filters["group_by"] = "rule"

    if any(kw in text for kw in ["trader", "who", "which trader"]):
        if "group_by" not in filters:
            filters["group_by"] = "trader"

    # Build summary prompt for the AI response header
    summary_intro = "Showing results " + (", ".join(description_parts) if description_parts else "for the past 30 days")

    return {
        "filters": filters,
        "summary_intro": summary_intro,
        "original_query": query,
    }


def generate_nl_summary(query: str, result_count: int, data_summary: Dict[str, Any]) -> str:
    """
    Generate a natural language summary of query results.
    """
    parsed = parse_nl_query(query)
    days = parsed["filters"].get("days_back", 30)
    period = f"past {days} day{'s' if days != 1 else ''}" if days > 0 else "today"

    total = data_summary.get("total", result_count)
    clean = data_summary.get("CLEAN_PASS", 0)
    soft = data_summary.get("SOFT_BLOCK", 0)
    hard = data_summary.get("HARD_BLOCK", 0)
    override = data_summary.get("HARD_BLOCK_WITH_OVERRIDE", 0)
    blocked = soft + hard + override

    if total == 0:
        return f"No trades found matching your query for the {period}."

    block_rate = (blocked / total * 100) if total > 0 else 0
    top_rule = data_summary.get("top_rule", "N/A")
    top_trader = data_summary.get("top_trader", "N/A")

    summary = (
        f"In the {period}, ArT processed {total:,} trade{'s' if total != 1 else ''}. "
        f"{clean:,} passed cleanly ({clean/total*100:.0f}%). "
        f"{blocked:,} were blocked ({block_rate:.0f}%) — "
        f"{soft} soft blocks, {hard} hard blocks, {override} requiring supervisory override. "
    )

    if top_rule and top_rule != "N/A":
        summary += f"The most frequently triggered rule was '{top_rule}'. "
    if top_trader and top_trader != "N/A":
        summary += f"The trader with the highest block count was {top_trader}."

    return summary.strip()
