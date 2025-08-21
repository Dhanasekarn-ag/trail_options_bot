# ==================== src/strategy/base_strategy.py ====================
from abc import ABC, abstractmethod
from typing import Dict, Optional
import logging
from src.models.order import Order
from src.models.position import Position
from typing import Dict, List, Optional, Tuple

class BaseStrategy(ABC):
    """Base class for all trading strategies"""
    
    def __init__(self, name: str, config: Optional[Dict] = None):
        self.name = name
        self.config = config or {}
        self.is_active = True
        self.logger = logging.getLogger(f"strategy.{name}")
        
        # Strategy metrics
        self.total_trades = 0
        self.winning_trades = 0
        self.total_pnl = 0.0
        
    @abstractmethod
    async def should_enter(self, market_data: Dict) -> Optional[Order]:
        """
        Determine if strategy should enter a position
        
        Args:
            market_data: Dictionary containing market data
            
        Returns:
            Order object if entry signal is found, None otherwise
        """
        pass
    
    @abstractmethod
    async def should_exit(self, position: Position, market_data: Dict) -> Optional[Order]:
        """
        Determine if strategy should exit a position
        
        Args:
            position: Current position
            market_data: Dictionary containing market data
            
        Returns:
            Order object if exit signal is found, None otherwise
        """
        pass
    
    async def on_order_filled(self, order: Order):
        """
        Called when an order is filled
        
        Args:
            order: The filled order
        """
        self.logger.info(f"Order filled: {order.symbol} {order.transaction_type.value} {order.quantity} @ {order.price}")
    
    async def on_error(self, error: Exception):
        """
        Called when an error occurs in strategy execution
        
        Args:
            error: The exception that occurred
        """
        self.logger.error(f"Strategy error: {error}")
    
    def get_performance_metrics(self) -> Dict:
        """Get strategy performance metrics"""
        win_rate = (self.winning_trades / max(1, self.total_trades)) * 100
        
        return {
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'win_rate': win_rate,
            'total_pnl': self.total_pnl,
            'is_active': self.is_active
        }
    
    def activate(self):
        """Activate the strategy"""
        self.is_active = True
        self.logger.info(f"Strategy {self.name} activated")
    
    def deactivate(self):
        """Deactivate the strategy"""
        self.is_active = False
        self.logger.info(f"Strategy {self.name} deactivated")