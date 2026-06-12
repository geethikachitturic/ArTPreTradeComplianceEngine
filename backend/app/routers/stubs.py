"""
Stub 1 — Trade Generator.
Randomly generates trades with economics designed to trigger Reg T and FINRA 4210 checks.
Fires them against the ArT engine and returns the full decision.
"""
import random
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.trade import (
    AccountType, AssetClass, ProductType, TradeDirection
)
from app.models.user import User, UserRole
from app.routers.art import check_trade
from app.schemas.trade import TradeCreate

router = APIRouter(prefix="/stubs", tags=["Stub 1 — Trade Generator"])

# Realistic ticker / instrument pools
EQUITY_TICKERS = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "JPM", "GS", "BAC", "TSLA", "META", "XOM", "JNJ"]
BOND_ISSUERS = ["T 4.625 2053", "AAPL 3.85 2043", "JPM 5.04 2051", "MSFT 2.921 2052",
                "FORD 9.625 2030", "NFLX 5.875 2028", "HCA 5.5 2047", "MACY 6.7 2034"]
GOVT_TICKERS = ["UST 10Y", "UST 5Y", "UST 30Y", "UST 2Y"]
MUNIS = ["NY MTA 5.0 2040", "CA GO 4.0 2035", "TX TXDOT 3.75 2038"]

CREDIT_RATINGS_IG = ["AAA", "AA+", "AA", "AA-", "A+", "A", "A-", "BBB+", "BBB", "BBB-"]
CREDIT_RATINGS_HY = ["BB+", "BB", "BB-", "B+", "B", "B-", "CCC+", "CCC"]


def _random_trader(db: Session) -> User:
    traders = db.query(User).filter(User.role == UserRole.TRADER, User.is_active == True).all()
    return random.choice(traders) if traders else None


def _build_scenario(scenario_type: str, trader: User) -> TradeCreate:
    """Build a trade with specific economics to exercise particular rule paths."""

    # Base account parameters
    account_id = f"ACC-{random.randint(10000, 99999)}"

    if scenario_type == "clean_equity_buy":
        notional = random.uniform(50_000, 500_000)
        equity = notional * random.uniform(0.65, 1.20)  # Well above 50% Reg T
        qty = random.randint(100, 5000)
        price = notional / qty
        return TradeCreate(
            trader_id=trader.id,
            asset_class=AssetClass.EQUITY,
            product_type=ProductType.STOCK,
            direction=TradeDirection.BUY,
            ticker=random.choice(EQUITY_TICKERS),
            quantity=qty, price=round(price, 2),
            account_id=account_id,
            account_type=AccountType.MARGIN,
            account_equity=round(equity, 2),
            existing_long_market_value=round(notional * 0.5, 2),
            intraday_margin_level=round(equity * 0.3, 2),
        )

    elif scenario_type == "soft_block_iml":
        notional = random.uniform(100_000, 300_000)
        # IML just goes slightly negative — safe harbour deficit
        equity = notional * 0.55
        iml = random.uniform(-800, -50)  # small deficit within safe harbour
        qty = random.randint(500, 3000)
        price = notional / qty
        return TradeCreate(
            trader_id=trader.id,
            asset_class=AssetClass.EQUITY,
            product_type=ProductType.STOCK,
            direction=TradeDirection.BUY,
            ticker=random.choice(EQUITY_TICKERS),
            quantity=qty, price=round(price, 2),
            account_id=account_id,
            account_type=AccountType.MARGIN,
            account_equity=round(equity, 2),
            existing_long_market_value=round(notional * 0.8, 2),
            intraday_margin_level=round(iml, 2),
            deficit_count_30d=random.randint(0, 1),
        )

    elif scenario_type == "hard_block_reg_t":
        notional = random.uniform(1_000_000, 5_000_000)
        # Equity is well below 50% — clear Reg T breach
        equity = notional * random.uniform(0.15, 0.35)
        qty = random.randint(5000, 50000)
        price = notional / qty
        return TradeCreate(
            trader_id=trader.id,
            asset_class=AssetClass.EQUITY,
            product_type=ProductType.STOCK,
            direction=TradeDirection.BUY,
            ticker=random.choice(EQUITY_TICKERS),
            quantity=qty, price=round(price, 2),
            account_id=account_id,
            account_type=AccountType.MARGIN,
            account_equity=round(equity, 2),
            existing_long_market_value=round(notional * 0.3, 2),
            existing_debit_balance=round(equity * 0.4, 2),
            intraday_margin_level=round(-notional * 0.15, 2),
        )

    elif scenario_type == "override_large_deficit":
        notional = random.uniform(2_000_000, 10_000_000)
        equity = notional * random.uniform(0.50, 0.70)
        # IML deficit in $25k-$100k range → Hard Block with Override
        iml_current = random.uniform(equity * 0.10, equity * 0.20)
        qty = random.randint(10000, 100000)
        price = notional / qty
        return TradeCreate(
            trader_id=trader.id,
            asset_class=AssetClass.EQUITY,
            product_type=random.choice([ProductType.STOCK, ProductType.ETF]),
            direction=TradeDirection.BUY,
            ticker=random.choice(EQUITY_TICKERS),
            quantity=qty, price=round(price, 2),
            account_id=account_id,
            account_type=AccountType.MARGIN,
            account_equity=round(equity, 2),
            existing_long_market_value=round(notional * 0.6, 2),
            existing_debit_balance=round(equity * 0.3, 2),
            intraday_margin_level=round(iml_current, 2),
            deficit_count_30d=random.randint(1, 3),
        )

    elif scenario_type == "short_sale":
        notional = random.uniform(500_000, 3_000_000)
        equity = notional * random.uniform(0.80, 1.60)
        qty = random.randint(1000, 20000)
        price = notional / qty
        return TradeCreate(
            trader_id=trader.id,
            asset_class=AssetClass.EQUITY,
            product_type=ProductType.STOCK,
            direction=TradeDirection.SHORT_SELL,
            ticker=random.choice(EQUITY_TICKERS),
            quantity=qty, price=round(price, 2),
            account_id=account_id,
            account_type=AccountType.MARGIN,
            account_equity=round(equity, 2),
            existing_short_market_value=round(notional * 0.3, 2),
            intraday_margin_level=round(equity * 0.2, 2),
        )

    elif scenario_type == "frozen_account_short":
        notional = random.uniform(100_000, 1_000_000)
        equity = notional * 0.80
        qty = random.randint(500, 5000)
        price = notional / qty
        return TradeCreate(
            trader_id=trader.id,
            asset_class=AssetClass.EQUITY,
            product_type=ProductType.STOCK,
            direction=TradeDirection.SHORT_SELL,
            ticker=random.choice(EQUITY_TICKERS),
            quantity=qty, price=round(price, 2),
            account_id=account_id,
            account_type=AccountType.MARGIN,
            account_equity=round(equity, 2),
            is_90day_freeze_active=True,
            deficit_count_30d=4,
            days_since_last_deficit=3,
        )

    elif scenario_type == "fi_corp_bond_ig":
        notional = random.uniform(500_000, 5_000_000)
        equity = notional * random.uniform(0.35, 0.70)
        qty = random.randint(500, 5000)  # bond face value units
        price = notional / qty
        return TradeCreate(
            trader_id=trader.id,
            asset_class=AssetClass.FIXED_INCOME,
            product_type=ProductType.CORP_BOND_IG,
            direction=TradeDirection.BUY,
            ticker=random.choice(BOND_ISSUERS[:4]),
            quantity=qty, price=round(price, 2),
            account_id=account_id,
            account_type=AccountType.MARGIN,
            account_equity=round(equity, 2),
            credit_rating=random.choice(CREDIT_RATINGS_IG),
            intraday_margin_level=round(equity * 0.15, 2),
        )

    elif scenario_type == "fi_corp_bond_hy":
        notional = random.uniform(1_000_000, 8_000_000)
        # Insufficient margin for 50% HY requirement
        equity = notional * random.uniform(0.20, 0.45)
        qty = random.randint(1000, 8000)
        price = notional / qty
        return TradeCreate(
            trader_id=trader.id,
            asset_class=AssetClass.FIXED_INCOME,
            product_type=ProductType.CORP_BOND_HY,
            direction=TradeDirection.BUY,
            ticker=random.choice(BOND_ISSUERS[4:]),
            quantity=qty, price=round(price, 2),
            account_id=account_id,
            account_type=AccountType.MARGIN,
            account_equity=round(equity, 2),
            credit_rating=random.choice(CREDIT_RATINGS_HY),
            intraday_margin_level=round(equity * 0.1, 2),
        )

    elif scenario_type == "fi_govt_bond":
        notional = random.uniform(5_000_000, 50_000_000)
        equity = notional * random.uniform(0.12, 0.30)  # Govts only need 10%
        qty = random.randint(5000, 50000)
        price = notional / qty
        return TradeCreate(
            trader_id=trader.id,
            asset_class=AssetClass.FIXED_INCOME,
            product_type=ProductType.GOVT_BOND,
            direction=TradeDirection.BUY,
            ticker=random.choice(GOVT_TICKERS),
            quantity=qty, price=round(price, 2),
            account_id=account_id,
            account_type=AccountType.MARGIN,
            account_equity=round(equity, 2),
            credit_rating="AAA",
            intraday_margin_level=round(equity * 0.5, 2),
        )

    else:
        # Fallback: random clean equity
        return _build_scenario("clean_equity_buy", trader)


_SCENARIO_WEIGHTS = [
    ("clean_equity_buy", 20),
    ("soft_block_iml", 15),
    ("hard_block_reg_t", 15),
    ("override_large_deficit", 15),
    ("short_sale", 10),
    ("frozen_account_short", 10),
    ("fi_corp_bond_ig", 5),
    ("fi_corp_bond_hy", 5),
    ("fi_govt_bond", 5),
]

_SCENARIOS = [s for s, _ in _SCENARIO_WEIGHTS]
_WEIGHTS = [w for _, w in _SCENARIO_WEIGHTS]


@router.post("/generate-trade")
def generate_single_trade(scenario: str = None, trader_id: int = None, db: Session = Depends(get_db)):
    """Generate and check a single random trade."""
    trader = db.query(User).filter(User.id == trader_id).first() if trader_id else _random_trader(db)
    if not trader:
        return {"error": "No traders found. Run seed data first."}

    chosen_scenario = scenario if scenario in _SCENARIOS else random.choices(_SCENARIOS, weights=_WEIGHTS, k=1)[0]
    trade_in = _build_scenario(chosen_scenario, trader)
    result = check_trade(trade_in, db)
    return {**result.model_dump(), "scenario": chosen_scenario}


@router.post("/generate-batch")
def generate_batch(count: int = 10, db: Session = Depends(get_db)):
    """Generate and check multiple trades, covering a spread of scenarios."""
    count = min(count, 50)
    results = []
    traders = db.query(User).filter(User.role == UserRole.TRADER, User.is_active == True).all()
    if not traders:
        return {"error": "No traders found. Run seed data first."}

    for _ in range(count):
        trader = random.choice(traders)
        scenario = random.choices(_SCENARIOS, weights=_WEIGHTS, k=1)[0]
        trade_in = _build_scenario(scenario, trader)
        try:
            result = check_trade(trade_in, db)
            results.append({**result.model_dump(), "scenario": scenario})
        except Exception as e:
            results.append({"error": str(e), "scenario": scenario})

    return {"count": len(results), "results": results}


@router.get("/scenarios")
def list_scenarios():
    """Return available scenario types for the UI dropdown."""
    return {
        "scenarios": [
            {"key": s, "label": s.replace("_", " ").title(), "weight": w}
            for s, w in _SCENARIO_WEIGHTS
        ]
    }
