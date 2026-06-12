import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class AssetClass(str, enum.Enum):
    EQUITY = "EQUITY"
    FIXED_INCOME = "FIXED_INCOME"


class ProductType(str, enum.Enum):
    # Equity
    STOCK = "STOCK"
    ETF = "ETF"
    EQUITY_OPTION = "EQUITY_OPTION"
    # Fixed Income
    GOVT_BOND = "GOVT_BOND"
    CORP_BOND_IG = "CORP_BOND_IG"       # Investment Grade
    CORP_BOND_HY = "CORP_BOND_HY"       # High Yield / Non-IG
    MUNICIPAL_BOND = "MUNICIPAL_BOND"


class TradeDirection(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"
    SHORT_SELL = "SHORT_SELL"
    BUY_TO_COVER = "BUY_TO_COVER"
    SHORT_PUT = "SHORT_PUT"
    SHORT_CALL = "SHORT_CALL"


class AccountType(str, enum.Enum):
    CASH = "CASH"
    MARGIN = "MARGIN"
    PORTFOLIO_MARGIN = "PORTFOLIO_MARGIN"


class TradeStatus(str, enum.Enum):
    PENDING_CHECK = "PENDING_CHECK"
    CLEAN_PASS = "CLEAN_PASS"
    SOFT_BLOCK = "SOFT_BLOCK"
    HARD_BLOCK = "HARD_BLOCK"
    HARD_BLOCK_WITH_OVERRIDE = "HARD_BLOCK_WITH_OVERRIDE"
    OVERRIDE_APPROVED = "OVERRIDE_APPROVED"
    OVERRIDE_REJECTED = "OVERRIDE_REJECTED"


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    trade_ref = Column(String(20), unique=True, nullable=False, index=True)
    trader_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    asset_class = Column(Enum(AssetClass), nullable=False)
    product_type = Column(Enum(ProductType), nullable=False)
    direction = Column(Enum(TradeDirection), nullable=False)

    ticker = Column(String(20), nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    notional = Column(Float, nullable=False)

    account_id = Column(String(20), nullable=False)
    account_type = Column(Enum(AccountType), nullable=False)
    account_equity = Column(Float, nullable=False)
    existing_long_market_value = Column(Float, default=0.0, nullable=False)
    existing_short_market_value = Column(Float, default=0.0, nullable=False)
    existing_debit_balance = Column(Float, default=0.0, nullable=False)
    intraday_margin_level = Column(Float, default=0.0, nullable=False)
    days_since_last_deficit = Column(Integer, default=None, nullable=True)
    deficit_count_30d = Column(Integer, default=0, nullable=False)
    is_90day_freeze_active = Column(Integer, default=0, nullable=False)

    credit_rating = Column(String(10), nullable=True)

    status = Column(Enum(TradeStatus), default=TradeStatus.PENDING_CHECK, nullable=False)
    trade_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    trader = relationship("User", back_populates="trades", foreign_keys=[trader_id])
    decision = relationship("ArtDecision", back_populates="trade", uselist=False)
