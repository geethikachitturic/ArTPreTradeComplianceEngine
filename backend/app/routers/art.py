"""
ArT core endpoint — runs the rules engine against a trade and persists the decision.
"""
import random
import string
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.engine.rules_engine import run_engine
from app.engine.ai_simulator import score_override_risk
from app.models.audit import AuditLog
from app.models.decision import ArtDecision, DecisionOutcome
from app.models.override import OverrideRequest, RiskBand
from app.models.trade import Trade, TradeStatus
from app.models.user import User
from app.schemas.decision import ArtDecisionOut, TradeCheckResponse
from app.schemas.trade import TradeCreate, TradeOut

router = APIRouter(prefix="/art", tags=["ArT Engine"])


def _generate_ref(prefix: str, length: int = 8) -> str:
    chars = string.ascii_uppercase + string.digits
    return prefix + "".join(random.choices(chars, k=length))


def _trade_to_dict(trade: Trade, trader: User) -> dict:
    return {
        "trader_id": trade.trader_id,
        "trader_seniority": trader.seniority_level.value if trader else "ANALYST",
        "asset_class": trade.asset_class.value,
        "product_type": trade.product_type.value,
        "direction": trade.direction.value,
        "ticker": trade.ticker,
        "quantity": trade.quantity,
        "price": trade.price,
        "notional": trade.notional,
        "account_id": trade.account_id,
        "account_type": trade.account_type.value,
        "account_equity": trade.account_equity,
        "existing_long_market_value": trade.existing_long_market_value,
        "existing_short_market_value": trade.existing_short_market_value,
        "existing_debit_balance": trade.existing_debit_balance,
        "intraday_margin_level": trade.intraday_margin_level,
        "days_since_last_deficit": trade.days_since_last_deficit,
        "deficit_count_30d": trade.deficit_count_30d,
        "is_90day_freeze_active": bool(trade.is_90day_freeze_active),
        "credit_rating": trade.credit_rating,
    }


@router.post("/check", response_model=TradeCheckResponse)
def check_trade(trade_in: TradeCreate, db: Session = Depends(get_db)):
    """
    Primary ArT endpoint. Accepts a trade, runs all compliance checks,
    persists the decision, and returns the outcome with full reasoning.
    """
    trader = db.query(User).filter(User.id == trade_in.trader_id).first()
    if not trader:
        raise HTTPException(status_code=404, detail="Trader not found")

    # Persist the trade
    trade = Trade(
        trade_ref=_generate_ref("TRD-"),
        trader_id=trade_in.trader_id,
        asset_class=trade_in.asset_class,
        product_type=trade_in.product_type,
        direction=trade_in.direction,
        ticker=trade_in.ticker,
        quantity=trade_in.quantity,
        price=trade_in.price,
        notional=trade_in.quantity * trade_in.price,
        account_id=trade_in.account_id,
        account_type=trade_in.account_type,
        account_equity=trade_in.account_equity,
        existing_long_market_value=trade_in.existing_long_market_value,
        existing_short_market_value=trade_in.existing_short_market_value,
        existing_debit_balance=trade_in.existing_debit_balance,
        intraday_margin_level=trade_in.intraday_margin_level,
        days_since_last_deficit=trade_in.days_since_last_deficit,
        deficit_count_30d=trade_in.deficit_count_30d,
        is_90day_freeze_active=int(trade_in.is_90day_freeze_active),
        credit_rating=trade_in.credit_rating,
        status=TradeStatus.PENDING_CHECK,
    )
    db.add(trade)
    db.flush()

    trade_dict = _trade_to_dict(trade, trader)
    trader_dict = {
        "seniority_level": trader.seniority_level.value,
        "role": trader.role.value,
        "desk": trader.desk,
    }

    # Run the engine
    engine_result = run_engine(trade_dict, trader_dict, db)

    # Map outcome
    outcome_map = {
        "CLEAN_PASS": DecisionOutcome.CLEAN_PASS,
        "SOFT_BLOCK": DecisionOutcome.SOFT_BLOCK,
        "HARD_BLOCK": DecisionOutcome.HARD_BLOCK,
        "HARD_BLOCK_WITH_OVERRIDE": DecisionOutcome.HARD_BLOCK_WITH_OVERRIDE,
    }
    decision_outcome = outcome_map[engine_result.outcome]

    # Update trade status
    status_map = {
        DecisionOutcome.CLEAN_PASS: TradeStatus.CLEAN_PASS,
        DecisionOutcome.SOFT_BLOCK: TradeStatus.SOFT_BLOCK,
        DecisionOutcome.HARD_BLOCK: TradeStatus.HARD_BLOCK,
        DecisionOutcome.HARD_BLOCK_WITH_OVERRIDE: TradeStatus.HARD_BLOCK_WITH_OVERRIDE,
    }
    trade.status = status_map[decision_outcome]

    # Persist decision
    decision = ArtDecision(
        decision_ref=_generate_ref("DEC-"),
        trade_id=trade.id,
        outcome=decision_outcome,
        rules_triggered=engine_result.rules_triggered,
        reasoning=engine_result.reasoning,
        reg_t_margin_required=engine_result.reg_t_margin_required,
        reg_t_margin_available=engine_result.reg_t_margin_available,
        intraday_margin_deficit=engine_result.intraday_margin_deficit,
        processing_time_ms=engine_result.processing_time_ms,
    )
    db.add(decision)
    db.flush()

    override_request_id = None

    # If override required, create override request automatically
    if decision_outcome == DecisionOutcome.HARD_BLOCK_WITH_OVERRIDE:
        override_history = _get_override_history(trade_in.trader_id, db)
        risk_result = score_override_risk(
            trade_data={**trade_dict, "trader_seniority": trader.seniority_level.value},
            decision_data={
                "intraday_margin_deficit": engine_result.intraday_margin_deficit,
                "rules_triggered": engine_result.rules_triggered,
            },
            override_history=override_history,
        )

        band_map = {
            "LOW": RiskBand.LOW,
            "MEDIUM": RiskBand.MEDIUM,
            "HIGH": RiskBand.HIGH,
            "CRITICAL": RiskBand.CRITICAL,
        }

        override = OverrideRequest(
            override_ref=_generate_ref("OVR-"),
            decision_id=decision.id,
            trade_id=trade.id,
            requested_by_id=trade_in.trader_id,
            ai_risk_score=risk_result["score"],
            ai_risk_band=band_map[risk_result["band"].value],
            ai_risk_rationale=risk_result["rationale"],
        )
        db.add(override)
        db.flush()
        override_request_id = override.id

    # Audit log entry
    db.add(AuditLog(
        event_type="TRADE_CHECKED",
        entity_type="TRADE",
        entity_id=trade.id,
        user_id=trader.id,
        username=trader.username,
        description=f"ArT pre-trade check: {engine_result.outcome} — {trade.trade_ref}",
        event_metadata={
            "trade_ref": trade.trade_ref,
            "outcome": engine_result.outcome,
            "rules_count": len(engine_result.rules_triggered),
            "asset_class": trade.asset_class.value,
            "notional": trade.notional,
        },
    ))

    db.commit()
    db.refresh(decision)

    return TradeCheckResponse(
        trade=TradeOut.model_validate(trade).model_dump(),
        decision=ArtDecisionOut.model_validate(decision),
        override_request_id=override_request_id,
    )


@router.get("/decisions", response_model=List[ArtDecisionOut])
def list_decisions(
    limit: int = 50,
    outcome: str = None,
    db: Session = Depends(get_db)
):
    q = db.query(ArtDecision).order_by(ArtDecision.created_at.desc())
    if outcome:
        q = q.filter(ArtDecision.outcome == outcome)
    return q.limit(limit).all()


def _get_override_history(trader_id: int, db: Session) -> dict:
    from datetime import timedelta
    cutoff = datetime.utcnow() - timedelta(days=30)
    overrides = (
        db.query(OverrideRequest)
        .filter(OverrideRequest.requested_by_id == trader_id)
        .filter(OverrideRequest.requested_at >= cutoff)
        .all()
    )
    return {
        "approved_30d": sum(1 for o in overrides if o.status.value == "APPROVED"),
        "rejected_30d": sum(1 for o in overrides if o.status.value == "REJECTED"),
        "total_30d": len(overrides),
    }
