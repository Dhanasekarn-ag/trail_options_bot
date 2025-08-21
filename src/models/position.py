# ==================== src/models/position.py ====================
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Position:
    """Trading position model"""
    symbol: str
    quantity: int
    average_price: float
    current_price: float
    pnl: float
    unrealized_pnl: float
    instrument_key: str
    
    # Optional fields
    entry_time: Optional[datetime] = None
    strategy_name: Optional[str] = "default"
    option_type: Optional[str] = None  # CE or PE
    strike_price: Optional[float] = None
    expiry: Optional[str] = None
    entry_greeks: Optional[dict] = None
    
    def __post_init__(self):
        if self.entry_time is None:
            self.entry_time = datetime.now()
    
    def update_current_price(self, new_price: float):
        """Update current price and calculate unrealized P&L"""
        self.current_price = new_price
        self.unrealized_pnl = (new_price - self.average_price) * self.quantity
    
    def get_pnl_percentage(self) -> float:
        """Get P&L as percentage"""
        if self.average_price == 0:
            return 0.0
        return ((self.current_price - self.average_price) / self.average_price) * 100
