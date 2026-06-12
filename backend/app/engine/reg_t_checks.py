"""
Regulation T (12 CFR Part 220) compliance checks.

Reg T governs initial margin at the point of transaction:
- Equity purchases on margin: customer must provide >= 50% of purchase price
- Short sales: customer must deposit 150% of short sale value
- Fixed income: margin varies by instrument type and credit grade
- Cash accounts: must be paid in full (no margin extension)
"""
from dataclasses import dataclass, field
from typing import List, Optional

from app.models.trade import AccountType, AssetClass, ProductType, TradeDirection


# Reg T margin rates by instrument type
REG_T_INITIAL_MARGIN_RATES = {
    ProductType.STOCK: 0.50,
    ProductType.ETF: 0.50,
    ProductType.EQUITY_OPTION: 0.50,
    ProductType.GOVT_BOND: 0.10,          # US Treasuries: lower risk
    ProductType.MUNICIPAL_BOND: 0.25,
    ProductType.CORP_BOND_IG: 0.30,       # Investment grade corporate
    ProductType.CORP_BOND_HY: 0.50,       # High yield / non-investment grade
}

# Maintenance margin floors (FINRA Rule 4210 ongoing requirement)
MAINTENANCE_MARGIN_LONG = 0.25    # 25% for long equity positions
MAINTENANCE_MARGIN_SHORT = 0.30   # 30% for short equity positions


@dataclass
class RegTResult:
    passed: bool
    rule_code: str
    rule_name: str
    margin_required: float
    margin_available: float
    margin_rate_applied: float
    shortfall: float
    violation_description: str
    block_type: str   # SOFT_BLOCK | HARD_BLOCK | HARD_BLOCK_WITH_OVERRIDE
    details: dict = field(default_factory=dict)


def check_reg_t(trade_data: dict) -> List[RegTResult]:
    """
    Run all applicable Regulation T checks against a trade.
    Returns a list of violations found (empty = clean pass on Reg T).
    """
    violations: List[RegTResult] = []

    direction = trade_data["direction"]
    account_type = trade_data["account_type"]
    product_type = trade_data["product_type"]
    asset_class = trade_data["asset_class"]
    notional = trade_data["notional"]
    account_equity = trade_data["account_equity"]
    existing_debit_balance = trade_data.get("existing_debit_balance", 0.0)

    # Cash accounts must be paid in full — no margin extension permitted
    if account_type == AccountType.CASH:
        if direction in (TradeDirection.BUY, TradeDirection.BUY_TO_COVER):
            if account_equity < notional:
                shortfall = notional - account_equity
                violations.append(RegTResult(
                    passed=False,
                    rule_code="REGT-CA-001",
                    rule_name="Cash Account — Full Payment Required",
                    margin_required=notional,
                    margin_available=account_equity,
                    margin_rate_applied=1.0,
                    shortfall=shortfall,
                    violation_description=(
                        f"Cash account requires full payment. "
                        f"Trade notional ${notional:,.0f} exceeds available cash ${account_equity:,.0f}. "
                        f"Shortfall: ${shortfall:,.0f}."
                    ),
                    block_type="HARD_BLOCK",
                    details={"regulation": "Reg T § 220.8"},
                ))
        return violations  # No further checks for cash accounts

    # Determine applicable initial margin rate
    margin_rate = REG_T_INITIAL_MARGIN_RATES.get(product_type, 0.50)

    # --- Long purchases on margin ---
    if direction == TradeDirection.BUY:
        margin_required = notional * margin_rate
        # Available equity = account equity minus any existing debit
        margin_available = max(0, account_equity - existing_debit_balance)

        if margin_available < margin_required:
            shortfall = margin_required - margin_available
            # Classify severity: near-miss vs outright breach
            coverage_ratio = margin_available / notional if notional > 0 else 0

            if coverage_ratio >= (margin_rate * 0.80):
                # Within 80% of the required rate — borderline, allow override
                block_type = "HARD_BLOCK_WITH_OVERRIDE"
                desc = (
                    f"Regulation T initial margin shortfall. Required {margin_rate*100:.0f}% "
                    f"(${margin_required:,.0f}), available ${margin_available:,.0f} "
                    f"(coverage {coverage_ratio*100:.1f}%). "
                    f"Shortfall ${shortfall:,.0f}. Supervisory override permitted."
                )
            else:
                block_type = "HARD_BLOCK"
                desc = (
                    f"Regulation T initial margin breach. Required {margin_rate*100:.0f}% "
                    f"(${margin_required:,.0f}), available ${margin_available:,.0f} "
                    f"(coverage {coverage_ratio*100:.1f}%). Shortfall ${shortfall:,.0f}. "
                    f"Trade cannot proceed."
                )

            violations.append(RegTResult(
                passed=False,
                rule_code="REGT-LM-001",
                rule_name="Reg T Initial Margin — Long Purchase",
                margin_required=margin_required,
                margin_available=margin_available,
                margin_rate_applied=margin_rate,
                shortfall=shortfall,
                violation_description=desc,
                block_type=block_type,
                details={
                    "regulation": "Reg T § 220.12",
                    "product_type": product_type,
                    "coverage_ratio": round(coverage_ratio, 4),
                },
            ))

        # Maintenance margin check (ongoing, separate from initial)
        total_long_value = trade_data.get("existing_long_market_value", 0) + notional
        maintenance_required = total_long_value * MAINTENANCE_MARGIN_LONG
        net_equity = account_equity - existing_debit_balance
        if net_equity < maintenance_required and net_equity >= 0:
            shortfall = maintenance_required - net_equity
            violations.append(RegTResult(
                passed=False,
                rule_code="REGT-MM-001",
                rule_name="Maintenance Margin Warning — Long Position",
                margin_required=maintenance_required,
                margin_available=net_equity,
                margin_rate_applied=MAINTENANCE_MARGIN_LONG,
                shortfall=shortfall,
                violation_description=(
                    f"Post-trade equity ${net_equity:,.0f} would fall below 25% maintenance margin "
                    f"requirement (${maintenance_required:,.0f}) on combined long position of "
                    f"${total_long_value:,.0f}."
                ),
                block_type="SOFT_BLOCK",
                details={"regulation": "FINRA Rule 4210 maintenance margin"},
            ))

    # --- Short sales ---
    elif direction in (TradeDirection.SHORT_SELL, TradeDirection.SHORT_PUT, TradeDirection.SHORT_CALL):
        # Short sale requires: proceeds (100%) + additional margin (50%) = 150% of notional
        required_collateral = notional * 1.50
        margin_available = account_equity
        shortfall = max(0, required_collateral - margin_available)

        if shortfall > 0:
            coverage = margin_available / required_collateral if required_collateral > 0 else 0
            block_type = "HARD_BLOCK_WITH_OVERRIDE" if coverage >= 0.85 else "HARD_BLOCK"
            violations.append(RegTResult(
                passed=False,
                rule_code="REGT-SS-001",
                rule_name="Reg T Short Sale — 150% Collateral Requirement",
                margin_required=required_collateral,
                margin_available=margin_available,
                margin_rate_applied=1.50,
                shortfall=shortfall,
                violation_description=(
                    f"Short sale requires 150% of notional as collateral "
                    f"(${required_collateral:,.0f}). Available equity: ${margin_available:,.0f}. "
                    f"Shortfall: ${shortfall:,.0f}."
                ),
                block_type=block_type,
                details={
                    "regulation": "Reg T § 220.12 / FINRA Rule 4210(f)(2)",
                    "short_collateral_rate": 1.50,
                    "coverage_ratio": round(coverage, 4),
                },
            ))

    return violations
