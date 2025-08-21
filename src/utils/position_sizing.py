# ==================== src/utils/position_sizing.py ====================
import logging
from typing import Tuple

class PositionSizer:
    """Smart position sizing for multi-strategy trading"""
    
    def __init__(self, total_capital: float, max_risk_pct: float = 0.75):
        self.total_capital = total_capital
        self.max_risk_pct = max_risk_pct
        self.max_risk_amount = total_capital * max_risk_pct
        self.lot_size = 75  # NIFTY lot size
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"Position Sizer initialized: Capital Rs.{total_capital:,} | Max Risk: Rs.{self.max_risk_amount:,.0f}")
    
    def calculate_position_size(self, current_price: float) -> Tuple[int, float]:
        """Calculate optimal position size based on current price"""
        
        # Calculate maximum affordable lots
        max_lots_by_capital = int(self.max_risk_amount / (current_price * self.lot_size))
        
        # Conservative approach: start with smaller position
        conservative_lots = max(1, max_lots_by_capital // 2)
        
        # Ensure we don't exceed limits
        final_lots = min(conservative_lots, 4)  # Max 4 lots per trade
        final_lots = max(1, final_lots)  # Minimum 1 lot
        
        # Calculate total investment
        total_investment = final_lots * self.lot_size * current_price
        
        self.logger.debug(f"Position sizing: Price Rs.{current_price:.2f} → {final_lots} lots (Rs.{total_investment:,.2f})")
        
        return final_lots, total_investment
    
    def is_trade_affordable(self, current_price: float) -> bool:
        """Check if trade is affordable with current capital"""
        min_investment = 1 * self.lot_size * current_price
        return min_investment <= self.max_risk_amount
    
    def get_remaining_capital(self, used_capital: float) -> float:
        """Get remaining available capital"""
        return self.max_risk_amount - used_capital