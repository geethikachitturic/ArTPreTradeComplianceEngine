"""
MI Dashboard and NL reporting endpoints.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.engine.ai_simulator import generate_nl_summary, parse_nl_query
from app.models.decision import ArtDecision, DecisionOutcome
from app.models.override import OverrideRequest, OverrideStatus
from app.models.rule import Rule
from app.models.trade import Trade
from app.models.user import User

router = APIRouter(prefix="/reports", tags=["MI Dashboard"])


@router.get("/summary")
def get_summary(days: int = 30, db: Session = Depends(get_db)):
    """High-level decision outcome summary for the dashboard."""
    cutoff = datetime.utcnow() - timedelta(days=days)

    outcome_counts = (
        db.query(ArtDecision.outcome, func.count(ArtDecision.id).label("count"))
        .filter(ArtDecision.created_at >= cutoff)
        .group_by(ArtDecision.outcome)
        .all()
    )

    totals = {row.outcome.value: row.count for row in outcome_counts}
    total_all = sum(totals.values())

    pending_overrides = (
        db.query(func.count(OverrideRequest.id))
        .filter(OverrideRequest.status == OverrideStatus.PENDING)
        .scalar()
    )

    return {
        "period_days": days,
        "total_trades": total_all,
        "outcomes": {
            "CLEAN_PASS": totals.get("CLEAN_PASS", 0),
            "SOFT_BLOCK": totals.get("SOFT_BLOCK", 0),
            "HARD_BLOCK": totals.get("HARD_BLOCK", 0),
            "HARD_BLOCK_WITH_OVERRIDE": totals.get("HARD_BLOCK_WITH_OVERRIDE", 0),
        },
        "block_rate": round(
            (totals.get("SOFT_BLOCK", 0) + totals.get("HARD_BLOCK", 0) + totals.get("HARD_BLOCK_WITH_OVERRIDE", 0))
            / total_all * 100, 1
        ) if total_all > 0 else 0,
        "pending_overrides": pending_overrides,
    }


@router.get("/daily-trend")
def get_daily_trend(days: int = 14, db: Session = Depends(get_db)):
    """Per-day outcome counts for the trend chart."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    rows = (
        db.query(
            func.date(ArtDecision.created_at).label("date"),
            ArtDecision.outcome,
            func.count(ArtDecision.id).label("count"),
        )
        .filter(ArtDecision.created_at >= cutoff)
        .group_by(func.date(ArtDecision.created_at), ArtDecision.outcome)
        .order_by(func.date(ArtDecision.created_at))
        .all()
    )

    # Pivot into date → {outcome: count}
    trend: Dict[str, Dict[str, int]] = {}
    for row in rows:
        d = str(row.date)
        if d not in trend:
            trend[d] = {"CLEAN_PASS": 0, "SOFT_BLOCK": 0, "HARD_BLOCK": 0, "HARD_BLOCK_WITH_OVERRIDE": 0}
        trend[d][row.outcome.value] = row.count

    return [{"date": d, **counts} for d, counts in sorted(trend.items())]


@router.get("/top-rules")
def get_top_rules(days: int = 30, limit: int = 10, db: Session = Depends(get_db)):
    """Most frequently triggered rules."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    decisions = (
        db.query(ArtDecision)
        .filter(ArtDecision.created_at >= cutoff)
        .filter(ArtDecision.outcome != DecisionOutcome.CLEAN_PASS)
        .all()
    )

    rule_counts: Dict[str, Dict[str, Any]] = {}
    for d in decisions:
        for rule in (d.rules_triggered or []):
            code = rule.get("rule_code", "UNKNOWN")
            if code not in rule_counts:
                rule_counts[code] = {
                    "rule_code": code,
                    "rule_name": rule.get("rule_name", "Unknown"),
                    "rule_type": rule.get("rule_type", "UNKNOWN"),
                    "count": 0,
                }
            rule_counts[code]["count"] += 1

    sorted_rules = sorted(rule_counts.values(), key=lambda x: x["count"], reverse=True)
    return sorted_rules[:limit]


@router.get("/top-traders")
def get_top_traders_by_blocks(days: int = 30, limit: int = 10, db: Session = Depends(get_db)):
    """Traders with the most block decisions."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    rows = (
        db.query(Trade.trader_id, func.count(Trade.id).label("block_count"))
        .join(ArtDecision, ArtDecision.trade_id == Trade.id)
        .filter(ArtDecision.created_at >= cutoff)
        .filter(ArtDecision.outcome != DecisionOutcome.CLEAN_PASS)
        .group_by(Trade.trader_id)
        .order_by(func.count(Trade.id).desc())
        .limit(limit)
        .all()
    )

    result = []
    for row in rows:
        user = db.query(User).filter(User.id == row.trader_id).first()
        result.append({
            "trader_id": row.trader_id,
            "trader_name": user.full_name if user else "Unknown",
            "desk": user.desk if user else "N/A",
            "seniority": user.seniority_level.value if user else "N/A",
            "block_count": row.block_count,
        })
    return result


@router.get("/override-stats")
def get_override_stats(days: int = 30, db: Session = Depends(get_db)):
    """Override request statistics."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    overrides = db.query(OverrideRequest).filter(OverrideRequest.requested_at >= cutoff).all()

    total = len(overrides)
    approved = sum(1 for o in overrides if o.status == OverrideStatus.APPROVED)
    rejected = sum(1 for o in overrides if o.status == OverrideStatus.REJECTED)
    pending = sum(1 for o in overrides if o.status == OverrideStatus.PENDING)
    escalated = sum(1 for o in overrides if o.status == OverrideStatus.ESCALATED)

    avg_risk = sum(o.ai_risk_score for o in overrides) / total if total > 0 else 0

    return {
        "total": total,
        "approved": approved,
        "rejected": rejected,
        "pending": pending,
        "escalated": escalated,
        "approval_rate": round(approved / total * 100, 1) if total > 0 else 0,
        "avg_ai_risk_score": round(avg_risk, 1),
    }


@router.post("/nl-query")
def nl_query(body: Dict[str, str], db: Session = Depends(get_db)):
    """
    Natural language reporting query (simulated AI).
    Parses the query, executes the appropriate database filters,
    returns data + AI-generated summary.
    """
    query = body.get("query", "")
    parsed = parse_nl_query(query)
    filters = parsed["filters"]
    days_back = filters.get("days_back", 30)
    cutoff = datetime.utcnow() - timedelta(days=days_back)

    q = db.query(ArtDecision).filter(ArtDecision.created_at >= cutoff)

    # Apply outcome filter
    if "outcome" in filters and filters["outcome"]:
        try:
            q = q.filter(ArtDecision.outcome == DecisionOutcome(filters["outcome"]))
        except ValueError:
            # "block" means any non-clean outcome
            q = q.filter(ArtDecision.outcome != DecisionOutcome.CLEAN_PASS)

    # Apply asset class filter
    if "asset_class" in filters:
        q = q.join(Trade, Trade.id == ArtDecision.trade_id).filter(
            Trade.asset_class == filters["asset_class"]
        )

    decisions = q.order_by(ArtDecision.created_at.desc()).limit(200).all()

    # Aggregate for summary
    outcome_counts = {}
    rule_counts: Dict[str, int] = {}
    trader_counts: Dict[int, int] = {}

    for d in decisions:
        outcome_counts[d.outcome.value] = outcome_counts.get(d.outcome.value, 0) + 1
        trade = db.query(Trade).filter(Trade.id == d.trade_id).first()
        if trade:
            trader_counts[trade.trader_id] = trader_counts.get(trade.trader_id, 0) + 1
        for rule in (d.rules_triggered or []):
            name = rule.get("rule_name", "Unknown")
            rule_counts[name] = rule_counts.get(name, 0) + 1

    top_rule = max(rule_counts, key=rule_counts.get) if rule_counts else None
    top_trader_id = max(trader_counts, key=trader_counts.get) if trader_counts else None
    top_trader_name = None
    if top_trader_id:
        u = db.query(User).filter(User.id == top_trader_id).first()
        top_trader_name = u.full_name if u else None

    data_summary = {
        **outcome_counts,
        "total": len(decisions),
        "top_rule": top_rule,
        "top_trader": top_trader_name,
    }

    nl_summary = generate_nl_summary(query, len(decisions), data_summary)

    return {
        "query": query,
        "parsed_filters": filters,
        "summary": nl_summary,
        "total_results": len(decisions),
        "data_summary": data_summary,
        "decisions": [
            {
                "decision_ref": d.decision_ref,
                "outcome": d.outcome.value,
                "created_at": d.created_at.isoformat(),
                "rules_count": len(d.rules_triggered or []),
            }
            for d in decisions[:50]
        ],
    }
