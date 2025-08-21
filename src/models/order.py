# ==================== src/models/order.py ====================
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    STOP_LOSS_MARKET = "STOP_LOSS_MARKET"

class TransactionType(Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderStatus(Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

@dataclass
class Order:
    """Trading order model"""
    symbol: str
    quantity: int
    price: float
    order_type: OrderType
    transaction_type: TransactionType
    strategy_name: str = "default"
    
    # Optional fields
    order_id: Optional[str] = None
    instrument_key: Optional[str] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_price: Optional[float] = None
    filled_quantity: Optional[int] = None
    timestamp: Optional[datetime] = None
    
    # Option-specific fields
    option_type: Optional[str] = None  # CE or PE
    strike_price: Optional[float] = None
    expiry: Optional[str] = None
    strategy_mode: Optional[str] = None
    greeks: Optional[dict] = None
    exit_reason: Optional[str] = None
    pnl_pct: Optional[float] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
