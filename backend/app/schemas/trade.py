from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator

from app.models.trade import (
    AssetClass, ProductType, TradeDirection, AccountType, TradeStatus
)


class TradeCreate(BaseModel):
    trader_id: int
    asset_class: AssetClass
    product_type: ProductType
    direction: TradeDirection
    ticker: str
    quantity: float
    price: float
    account_id: str
    account_type: AccountType
    account_equity: float
    existing_long_market_value: float = 0.0
    existing_short_market_value: float = 0.0
    existing_debit_balance: float = 0.0
    intraday_margin_level: float = 0.0
    days_since_last_deficit: Optional[int] = None
    deficit_count_30d: int = 0
    is_90day_freeze_active: bool = False
    credit_rating: Optional[str] = None


class TradeOut(BaseModel):
    id: int
    trade_ref: str
    trader_id: int
    asset_class: AssetClass
    product_type: ProductType
    direction: TradeDirection
    ticker: str
    quantity: float
    price: float
    notional: float
    account_id: str
    account_type: AccountType
    account_equity: float
    existing_long_market_value: float
    existing_short_market_value: float
    existing_debit_balance: float
    intraday_margin_level: float
    deficit_count_30d: int
    is_90day_freeze_active: int
    credit_rating: Optional[str]
    status: TradeStatus
    trade_date: datetime
    created_at: datetime

    model_config = {"from_attributes": True}
