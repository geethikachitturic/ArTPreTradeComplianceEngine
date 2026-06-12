"""
FINRA Rule 4210 (2026 amendments) compliance checks.

Key 2026 changes:
- Elimination of pattern day trader (PDT) regime
- New Intraday Margin Level (IML) framework
- Intraday Margin Deficit computation
- 90-day freeze for repeat deficit offenders
- Portfolio margin: accounts < $5M equity face equivalent intraday requirements
"""
from dataclasses import dataclass, field
from typing import List

from app.models.trade import AccountType, AssetClass, ProductType, TradeDirection


# IML-reducing transactions per Rule 4210(a)(18):
# Any transaction that reduces the amount available for withdrawal while meeting maintenance margin
IML_REDUCING_DIRECTIONS = {
    TradeDirection.BUY,
    TradeDirection.SHORT_SELL,
    TradeDirection.SHORT_PUT,
    TradeDirection.SHORT_CALL,
}

# Maintenance margin rates (Rule 4210)
MAINT_MARGIN_LONG = 0.25   # 25% of long market value
MAINT_MARGIN_SHORT = 0.30  # 30% of short market value

# Safe harbour thresholds — Rule 4210(d)(2)(D)
SAFE_HARBOUR_ABSOLUTE = 1_000       # $1,000
SAFE_HARBOUR_EQUITY_PCT = 0.05      # 5% of account equity

# Portfolio margin threshold — Rule 4210(g)(1)(K)
PORTFOLIO_MARGIN_EQUITY_THRESHOLD = 5_000_000

# Deficit severity bands for block escalation
DEFICIT_OVERRIDE_THRESHOLD = 25_000    # $25k+ deficit → Hard Block with Override
DEFICIT_HARD_BLOCK_THRESHOLD = 100_000  # $100k+ deficit → outright Hard Block


@dataclass
class Finra4210Result:
    passed: bool
    rule_code: str
    rule_name: str
    violation_description: str
    block_type: str  # SOFT_BLOCK | HARD_BLOCK | HARD_BLOCK_WITH_OVERRIDE
    intraday_margin_deficit: float = 0.0
    iml_before: float = 0.0
    iml_after: float = 0.0
    details: dict = field(default_factory=dict)


def _compute_iml(account_equity: float, long_market_value: float,
                 short_market_value: float, debit_balance: float) -> float:
    """
    Intraday Margin Level = cash available for withdrawal while maintaining maintenance margin.

    IML = Account Equity - Maintenance Margin Required
    Maintenance Required = (LMV × 25%) + (SMV × 30%)

    A positive IML means the account has headroom.
    A negative IML means the account is already in deficit.
    """
    maintenance_required = (long_market_value * MAINT_MARGIN_LONG) + (short_market_value * MAINT_MARGIN_SHORT)
    net_equity = account_equity - debit_balance
    return net_equity - maintenance_required


def check_finra_4210(trade_data: dict) -> List[Finra4210Result]:
    """
    Run all FINRA Rule 4210 (2026) checks against a trade.
    Returns a list of violations (empty = clean).
    """
    violations: List[Finra4210Result] = []

    direction = trade_data["direction"]
    account_type = trade_data["account_type"]
    notional = trade_data["notional"]
    account_equity = trade_data["account_equity"]
    long_mv = trade_data.get("existing_long_market_value", 0.0)
    short_mv = trade_data.get("existing_short_market_value", 0.0)
    debit_balance = trade_data.get("existing_debit_balance", 0.0)
    iml_current = trade_data.get("intraday_margin_level", None)
    deficit_count_30d = trade_data.get("deficit_count_30d", 0)
    is_frozen = bool(trade_data.get("is_90day_freeze_active", False))
    days_since_deficit = trade_data.get("days_since_last_deficit", None)

    # Portfolio margin accounts — determine applicable threshold
    is_portfolio_margin = account_type == AccountType.PORTFOLIO_MARGIN
    below_pm_threshold = account_equity < PORTFOLIO_MARGIN_EQUITY_THRESHOLD

    # --- 90-day freeze check (Rule 4210(d)(2)(D)) ---
    if is_frozen:
        # Freeze blocks new short positions and new debit balance increases
        if direction in (TradeDirection.SHORT_SELL, TradeDirection.SHORT_PUT, TradeDirection.SHORT_CALL):
            violations.append(Finra4210Result(
                passed=False,
                rule_code="F4210-FRZ-001",
                rule_name="90-Day Freeze — Short Position Prohibited",
                violation_description=(
                    "Account is subject to a 90-calendar-day restriction under FINRA Rule 4210(d)(2)(D). "
                    "Customer has a history of failing to satisfy intraday margin deficits within 5 business days. "
                    "New short positions are prohibited during the freeze period."
                ),
                block_type="HARD_BLOCK",
                details={
                    "regulation": "FINRA Rule 4210(d)(2)(D)",
                    "freeze_active": True,
                },
            ))
        elif direction == TradeDirection.BUY:
            violations.append(Finra4210Result(
                passed=False,
                rule_code="F4210-FRZ-002",
                rule_name="90-Day Freeze — Debit Balance Increase Warning",
                violation_description=(
                    "Account is subject to a 90-day restriction. Increasing debit balance via margin purchase "
                    "is restricted. Proceed only if trade is for closing positions."
                ),
                block_type="SOFT_BLOCK",
                details={
                    "regulation": "FINRA Rule 4210(d)(2)(D)",
                    "freeze_active": True,
                },
            ))

    # --- IML-reducing transaction checks (Rule 4210(d)(2)(A) and (d)(2)(B)) ---
    if direction in IML_REDUCING_DIRECTIONS:
        # Compute IML before trade
        if iml_current is not None:
            iml_before = iml_current
        else:
            iml_before = _compute_iml(account_equity, long_mv, short_mv, debit_balance)

        # Compute IML after trade — trade increases margin requirement
        if direction == TradeDirection.BUY:
            iml_after = iml_before - (notional * MAINT_MARGIN_LONG)
        elif direction in (TradeDirection.SHORT_SELL, TradeDirection.SHORT_PUT, TradeDirection.SHORT_CALL):
            iml_after = iml_before - (notional * MAINT_MARGIN_SHORT)
        else:
            iml_after = iml_before

        if iml_after < 0:
            deficit = abs(iml_after)
            safe_harbour_limit = min(SAFE_HARBOUR_ABSOLUTE, account_equity * SAFE_HARBOUR_EQUITY_PCT)

            if deficit <= safe_harbour_limit:
                # Safe harbour — minor deficit, soft block with informational warning
                violations.append(Finra4210Result(
                    passed=False,
                    rule_code="F4210-IML-001",
                    rule_name="Intraday Margin Deficit — Safe Harbour Warning",
                    violation_description=(
                        f"Trade creates an intraday margin deficit of ${deficit:,.0f} under FINRA Rule 4210(d)(2). "
                        f"This falls within the safe harbour (lesser of $1,000 or 5% of equity = ${safe_harbour_limit:,.0f}). "
                        f"IML moves from ${iml_before:,.0f} to ${iml_after:,.0f}. "
                        f"Deficit must be satisfied as promptly as possible, no later than 15 business days."
                    ),
                    block_type="SOFT_BLOCK",
                    intraday_margin_deficit=deficit,
                    iml_before=iml_before,
                    iml_after=iml_after,
                    details={
                        "regulation": "FINRA Rule 4210(d)(2)(C)",
                        "safe_harbour_limit": safe_harbour_limit,
                        "satisfaction_deadline": "15 business days",
                        "net_capital_deduction_day": "6th business day if unsatisfied",
                    },
                ))

            elif deficit < DEFICIT_OVERRIDE_THRESHOLD:
                # Moderate deficit — soft block with stronger warning
                violations.append(Finra4210Result(
                    passed=False,
                    rule_code="F4210-IML-002",
                    rule_name="Intraday Margin Deficit — Moderate",
                    violation_description=(
                        f"Trade creates an intraday margin deficit of ${deficit:,.0f}. "
                        f"IML: ${iml_before:,.0f} → ${iml_after:,.0f}. "
                        f"Deficit must be satisfied promptly. Failure to satisfy within 5 business days "
                        f"may result in 90-day freeze restrictions (current deficit count past 30 days: {deficit_count_30d})."
                    ),
                    block_type="SOFT_BLOCK",
                    intraday_margin_deficit=deficit,
                    iml_before=iml_before,
                    iml_after=iml_after,
                    details={
                        "regulation": "FINRA Rule 4210(d)(2)",
                        "deficit_count_30d": deficit_count_30d,
                        "freeze_risk": deficit_count_30d >= 2,
                        "net_capital_deduction_day": "6th business day",
                    },
                ))

            elif deficit < DEFICIT_HARD_BLOCK_THRESHOLD:
                # Large deficit — Hard Block with Override option
                violations.append(Finra4210Result(
                    passed=False,
                    rule_code="F4210-IML-003",
                    rule_name="Intraday Margin Deficit — Large (Override Required)",
                    violation_description=(
                        f"Trade creates a large intraday margin deficit of ${deficit:,.0f} "
                        f"({deficit/account_equity*100:.1f}% of account equity). "
                        f"IML: ${iml_before:,.0f} → ${iml_after:,.0f}. "
                        f"Supervisory override required to proceed. "
                        f"Deficit represents material credit risk under FINRA Rule 4210(d)(2)."
                    ),
                    block_type="HARD_BLOCK_WITH_OVERRIDE",
                    intraday_margin_deficit=deficit,
                    iml_before=iml_before,
                    iml_after=iml_after,
                    details={
                        "regulation": "FINRA Rule 4210(d)(2)",
                        "deficit_pct_of_equity": round(deficit / account_equity, 4) if account_equity else None,
                        "net_capital_impact": "Deduction from net capital on 6th business day (SEC Rule 15c3-1)",
                    },
                ))

            else:
                # Critical deficit — outright Hard Block
                violations.append(Finra4210Result(
                    passed=False,
                    rule_code="F4210-IML-004",
                    rule_name="Intraday Margin Deficit — Critical (Hard Block)",
                    violation_description=(
                        f"Trade creates a critical intraday margin deficit of ${deficit:,.0f} "
                        f"({deficit/account_equity*100:.1f}% of account equity). "
                        f"IML: ${iml_before:,.0f} → ${iml_after:,.0f}. "
                        f"Trade is blocked. Risk to firm capital is unacceptable under FINRA Rule 4210."
                    ),
                    block_type="HARD_BLOCK",
                    intraday_margin_deficit=deficit,
                    iml_before=iml_before,
                    iml_after=iml_after,
                    details={
                        "regulation": "FINRA Rule 4210(d)(2)",
                        "deficit_pct_of_equity": round(deficit / account_equity, 4) if account_equity else None,
                    },
                ))

    # --- Portfolio margin check for accounts < $5M (Rule 4210(g)(1)(K)) ---
    if is_portfolio_margin and below_pm_threshold and direction in IML_REDUCING_DIRECTIONS:
        violations.append(Finra4210Result(
            passed=False,
            rule_code="F4210-PM-001",
            rule_name="Portfolio Margin — Sub-$5M Equity Intraday Check",
            violation_description=(
                f"Portfolio margin account with equity ${account_equity:,.0f} is below the "
                f"$5,000,000 threshold (Rule 4210(g)(1)(K)). Intraday margin must be maintained "
                f"at levels substantially similar to end-of-day requirements. Please verify "
                f"intraday risk is adequately collateralised before proceeding."
            ),
            block_type="SOFT_BLOCK",
            details={
                "regulation": "FINRA Rule 4210(g)(1)(K)",
                "account_equity": account_equity,
                "threshold": PORTFOLIO_MARGIN_EQUITY_THRESHOLD,
            },
        ))

    # --- Pattern day trader removal notice (informational, no block) ---
    # 2026 amendments eliminated PDT regime — this is here for audit completeness
    # No violations generated for PDT-related activity

    return violations
