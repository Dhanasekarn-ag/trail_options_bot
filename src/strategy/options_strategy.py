# ==================== src/strategy/options_strategy.py ====================
from typing import Dict, Optional
import numpy as np
import pandas as pd
try:
    import pandas_ta as ta
except ImportError:
    ta = None
from src.strategy.base_strategy import BaseStrategy
from src.models.order import Order, OrderType, TransactionType
from src.models.position import Position

class OptionsStrategy(BaseStrategy):
    """
    Options trading strategy template
    
    This is where you'll implement your actual trading strategy
    """
    
    def __init__(self, name: str, params: Dict = None):
        super().__init__(name, params)
        
        # Strategy parameters (you can customize these)
        self.entry_time = params.get('entry_time', '09:30')
        self.exit_time = params.get('exit_time', '15:15')
        self.profit_target = params.get('profit_target', 0.20)  # 20% profit
        self.stop_loss = params.get('stop_loss', 0.50)  # 50% loss
        self.max_positions = params.get('max_positions', 1)
        
        # Technical indicators
        self.price_history = []
        self.rsi_period = params.get('rsi_period', 14)
        
    async def should_enter(self, market_data: Dict) -> Optional[Order]:
        """
        Entry logic - implement your strategy here
        
        Example conditions:
        - Time-based entry
        - Technical indicators
        - Market conditions
        """
        try:
            current_time = market_data.get('timestamp')
            price = market_data.get('price', 0)
            symbol = market_data.get('symbol', '')
            
            # Check if we already have max positions
            if len(self.positions) >= self.max_positions:
                return None
            
            # Update price history for technical analysis
            self.price_history.append(price)
            if len(self.price_history) > 100:  # Keep last 100 prices
                self.price_history = self.price_history[-100:]
            
            # Add your entry conditions here
            # Example: Simple time-based entry with RSI
            if current_time and current_time.strftime('%H:%M') == self.entry_time:
                # Check RSI for oversold condition
                if len(self.price_history) >= self.rsi_period:
                    rsi = self.calculate_rsi(self.price_history, self.rsi_period)
                    
                    # Enter long if RSI < 30 (oversold)
                    if rsi < 30:
                        quantity = await self.calculate_position_size(price, self.params.get('risk_per_trade', 1000))
                        
                        return Order(
                            symbol=symbol,
                            quantity=quantity,
                            price=price,
                            order_type=OrderType.MARKET,
                            transaction_type=TransactionType.BUY,
                            instrument_key=market_data.get('instrument_key')
                        )
            
            # Add more sophisticated entry logic here
            # Example indicators you can implement:
            # - Moving average crossovers
            # - Bollinger Bands
            # - MACD
            # - Support/resistance levels
            # - Volume analysis
            
            return None
            
        except Exception as e:
            await self.on_error(e)
            return None
    
    async def should_exit(self, position: Position, market_data: Dict) -> Optional[Order]:
        """
        Exit logic - implement your exit strategy here
        """
        try:
            current_price = market_data.get('price', 0)
            current_time = market_data.get('timestamp')
            
            if current_price <= 0:
                return None
            
            # Calculate P&L percentage
            entry_price = position.average_price
            pnl_pct = (current_price - entry_price) / entry_price
            
            # Profit target
            if pnl_pct >= self.profit_target:
                self.logger.info(f"Profit target hit: {pnl_pct:.2%}")
                return Order(
                    symbol=position.symbol,
                    quantity=position.quantity,
                    price=current_price,
                    order_type=OrderType.MARKET,
                    transaction_type=TransactionType.SELL,
                    instrument_key=position.instrument_key
                )
            
            # Stop loss
            if pnl_pct <= -self.stop_loss:
                self.logger.info(f"Stop loss hit: {pnl_pct:.2%}")
                return Order(
                    symbol=position.symbol,
                    quantity=position.quantity,
                    price=current_price,
                    order_type=OrderType.MARKET,
                    transaction_type=TransactionType.SELL,
                    instrument_key=position.instrument_key
                )
            
            # Time-based exit
            if current_time and current_time.strftime('%H:%M') >= self.exit_time:
                self.logger.info("Time-based exit")
                return Order(
                    symbol=position.symbol,
                    quantity=position.quantity,
                    price=current_price,
                    order_type=OrderType.MARKET,
                    transaction_type=TransactionType.SELL,
                    instrument_key=position.instrument_key
                )
            
            # RSI-based exit (if overbought)
            if len(self.price_history) >= self.rsi_period:
                rsi = self.calculate_rsi(self.price_history, self.rsi_period)
                if rsi > 70:  # Overbought
                    self.logger.info(f"RSI overbought exit: {rsi:.2f}")
                    return Order(
                        symbol=position.symbol,
                        quantity=position.quantity,
                        price=current_price,
                        order_type=OrderType.MARKET,
                        transaction_type=TransactionType.SELL,
                        instrument_key=position.instrument_key
                    )
            
            # Add more exit conditions here
            # Example:
            # - Trailing stop loss
            # - Technical indicator reversals
            # - Market volatility changes
            
            return None
            
        except Exception as e:
            await self.on_error(e)
            return None
    
    def calculate_rsi(self, prices: list, period: int = 14) -> float:
        """Calculate RSI indicator using pandas"""
        if len(prices) < period + 1:
            return 50  # Neutral RSI
        
        # Convert to pandas Series
        price_series = pd.Series(prices)
        
        # Use pandas-ta if available, otherwise manual calculation
        if ta is not None:
            rsi_result = ta.rsi(price_series, length=period)
            return rsi_result.iloc[-1] if not rsi_result.isna().iloc[-1] else 50
        else:
            # Manual RSI calculation
            deltas = price_series.diff()
            gains = deltas.where(deltas > 0, 0)
            losses = -deltas.where(deltas < 0, 0)
            
            avg_gain = gains.rolling(window=period).mean()
            avg_loss = losses.rolling(window=period).mean()
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
    
    def calculate_moving_average(self, prices: list, period: int) -> float:
        """Calculate simple moving average"""
        if len(prices) < period:
            return 0
        
        return np.mean(prices[-period:])
    
    def calculate_bollinger_bands(self, prices: list, period: int = 20, std_dev: int = 2):
        """Calculate Bollinger Bands"""
        if len(prices) < period:
            return None, None, None
        
        price_series = pd.Series(prices)
        
        if ta is not None:
            bb_result = ta.bbands(price_series, length=period, std=std_dev)
            if bb_result is not None:
                return (
                    bb_result.iloc[-1, 0],  # Lower band
                    bb_result.iloc[-1, 1],  # Middle band (SMA)
                    bb_result.iloc[-1, 2]   # Upper band
                )
        
        # Manual calculation
        sma = price_series.rolling(period).mean().iloc[-1]
        std = price_series.rolling(period).std().iloc[-1]
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        return lower_band, sma, upper_band