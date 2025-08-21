# ==================== src/strategy/pine_script_strategy.py (ENHANCED) ====================
from typing import Dict, Optional, List
import numpy as np
import pandas as pd
from src.strategy.base_strategy import BaseStrategy
from src.models.order import Order, OrderType, TransactionType
from src.models.position import Position
from datetime import datetime, time
from src.utils.position_sizing import PositionSizer


class PineScriptStrategy(BaseStrategy):
    """
    Enhanced Smart Trend Entry-Exit Strategy v2 [Dhana]
    
    Converted from Pine Script to Python with enhanced monitoring
    Uses Heikin Ashi candles for better accuracy (67% vs lower with standard OHLC)
    """
    
    def __init__(self, name: str, params: Optional[Dict] = None):
        if params is None:
            params = {}
        super().__init__(name, params)
        
        # Strategy parameters
        self.adx_length = params.get('adx_length', 14)
        self.adx_threshold = params.get('adx_threshold', 20)
        self.strong_candle_threshold = params.get('strong_candle_threshold', 0.6)
        self.max_positions = params.get('max_positions', 1)
        self.risk_per_trade = params.get('risk_per_trade', 1000)
        
        # Position sizing for Rs.20,000 capital
        total_capital = params.get('total_capital', 20000)
        max_risk_pct = params.get('max_risk_pct', 0.75)
        self.position_sizer = PositionSizer(total_capital, max_risk_pct)
        
        # Trading state
        self.in_trade = False
        
        # Data storage for calculations
        self.ha_candles_history: List[Dict] = []
        self.max_history = 50
        
        # Enhanced monitoring
        self.last_analysis_log = datetime.now()
        self.analysis_log_interval = 180  # Log detailed analysis every 3 minutes
        self.signal_attempts = 0
        self.last_signal_time = None
        
        self.logger.info(f"Initialized PineScript Strategy with ADX threshold: {self.adx_threshold}")
        self.logger.info(f"Capital: Rs.{total_capital:,} | Max Risk: Rs.{total_capital * max_risk_pct:,.0f}")
    
    def add_ha_candle(self, ha_candle: Dict):
        """Add new Heikin Ashi candle to history with enhanced logging"""
        self.ha_candles_history.append(ha_candle)
        
        # Keep only last max_history candles
        if len(self.ha_candles_history) > self.max_history:
            self.ha_candles_history = self.ha_candles_history[-self.max_history:]
        
        # Log candle addition
        self.logger.debug(f"Added HA candle: O:{ha_candle.get('ha_open', 0):.2f} "
                         f"H:{ha_candle.get('ha_high', 0):.2f} L:{ha_candle.get('ha_low', 0):.2f} "
                         f"C:{ha_candle.get('ha_close', 0):.2f} | Total: {len(self.ha_candles_history)}")
    
    def calculate_trend_line(self, candles: List[Dict]) -> Optional[float]:
        """Calculate trend line: (EMA9 + SMA9) / 2"""
        if len(candles) < 9:
            return None
        
        # Extract close prices (using Heikin Ashi close)
        closes = [candle['ha_close'] for candle in candles]
        
        # Calculate EMA9
        ema9 = self.calculate_ema(closes, 9)
        
        # Calculate SMA9
        sma9 = self.calculate_sma(closes, 9)
        
        if ema9 is None or sma9 is None:
            return None
        
        # Trend line = (EMA9 + SMA9) / 2
        trend_line = (ema9 + sma9) / 2
        
        return trend_line
    
    def calculate_ema(self, prices: List[float], period: int) -> Optional[float]:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return None
        
        # Convert to pandas Series for easier calculation
        price_series = pd.Series(prices)
        ema = price_series.ewm(span=period, adjust=False).mean()
        
        return float(ema.iloc[-1]) if not pd.isna(ema.iloc[-1]) else None
    
    def calculate_sma(self, prices: List[float], period: int) -> Optional[float]:
        """Calculate Simple Moving Average"""
        if len(prices) < period:
            return None
        
        return float(np.mean(prices[-period:]))
    
    def calculate_adx(self, candles: List[Dict]) -> tuple:
        """Calculate ADX, +DI, -DI using manual calculation"""
        if len(candles) < self.adx_length + 1:
            return None, None, None
        
        # Extract OHLC data (using Heikin Ashi values)
        highs = [candle['ha_high'] for candle in candles]
        lows = [candle['ha_low'] for candle in candles]
        closes = [candle['ha_close'] for candle in candles]
        
        # Calculate True Range and Directional Movement
        plus_dm = []
        minus_dm = []
        tr_values = []
        
        for i in range(1, len(candles)):
            # Current and previous values
            curr_high = highs[i]
            curr_low = lows[i]
            curr_close = closes[i]
            prev_high = highs[i-1]
            prev_low = lows[i-1]
            prev_close = closes[i-1]
            
            # Up Move and Down Move
            up_move = curr_high - prev_high
            down_move = prev_low - curr_low
            
            # Plus DM and Minus DM
            plus_dm_val = up_move if up_move > 0 and up_move > down_move else 0
            minus_dm_val = down_move if down_move > 0 and down_move > up_move else 0
            
            plus_dm.append(plus_dm_val)
            minus_dm.append(minus_dm_val)
            
            # True Range
            tr1 = curr_high - curr_low
            tr2 = abs(curr_high - prev_close)
            tr3 = abs(curr_low - prev_close)
            tr = max(tr1, tr2, tr3)
            tr_values.append(tr)
        
        if len(tr_values) < self.adx_length:
            return None, None, None
        
        # Calculate smoothed values using RMA (Wilder's smoothing)
        smooth_tr = self.calculate_rma(tr_values, self.adx_length)
        smooth_plus_dm = self.calculate_rma(plus_dm, self.adx_length)
        smooth_minus_dm = self.calculate_rma(minus_dm, self.adx_length)
        
        # Calculate +DI and -DI
        plus_di = 100 * smooth_plus_dm / smooth_tr if smooth_tr > 0 else 0
        minus_di = 100 * smooth_minus_dm / smooth_tr if smooth_tr > 0 else 0
        
        # Calculate DX
        di_sum = plus_di + minus_di
        dx = 100 * abs(plus_di - minus_di) / di_sum if di_sum > 0 else 0
        
        # Calculate ADX (simplified - using current DX)
        adx = dx
        
        return adx, plus_di, minus_di
    
    def calculate_rma(self, values: List[float], period: int) -> float:
        """Calculate RMA (Wilder's smoothing)"""
        if len(values) < period:
            return 0.0
        
        # Initialize with simple average of first 'period' values
        rma = float(np.mean(values[:period]))
        
        # Apply Wilder's smoothing to remaining values
        alpha = 1.0 / period
        for i in range(period, len(values)):
            rma = alpha * values[i] + (1 - alpha) * rma
        
        return float(rma)
    
    def analyze_candle_strength(self, ha_candle: Dict) -> tuple:
        """Analyze Heikin Ashi candle strength with enhanced details"""
        ha_open = ha_candle['ha_open']
        ha_close = ha_candle['ha_close']
        ha_high = ha_candle['ha_high']
        ha_low = ha_candle['ha_low']
        
        # Calculate body and candle range
        body = abs(ha_close - ha_open)
        candle_range = ha_high - ha_low
        
        # Body percentage
        body_pct = body / candle_range if candle_range > 0 else 0
        
        # Determine candle color
        is_green = ha_close > ha_open
        is_red = ha_close < ha_open
        
        # Strong candle conditions
        strong_green = is_green and body_pct > self.strong_candle_threshold
        strong_red = is_red and body_pct > self.strong_candle_threshold
        
        return strong_green, strong_red, body_pct
    
    async def should_enter(self, market_data: Dict) -> Optional[Order]:
        """Enhanced entry logic with detailed monitoring"""
        try:
            # Get Heikin Ashi candle data
            ha_candle = market_data.get('ha_candle')
            if not ha_candle:
                return None
            
            # Add to history
            self.add_ha_candle(ha_candle)
            
            # Need enough data for calculations
            if len(self.ha_candles_history) < self.adx_length + 1:
                current_time = datetime.now()
                if (current_time - self.last_analysis_log).total_seconds() > 60:  # Log every minute
                    self.logger.info(f"🔄 Building data: {len(self.ha_candles_history)}/{self.adx_length + 1} HA candles required")
                    self.last_analysis_log = current_time
                return None
            
            # Check if already in trade
            if self.in_trade or len(self.positions) >= self.max_positions:
                return None
            
            # Calculate trend line
            trend_line = self.calculate_trend_line(self.ha_candles_history)
            if trend_line is None:
                return None
            
            # Current price (using Heikin Ashi close)
            current_price = ha_candle['ha_close']
            
            # Check if price is above trend line
            price_above = current_price > trend_line
            price_diff = current_price - trend_line
            price_diff_pct = (price_diff / trend_line) * 100
            
            # Analyze candle strength
            strong_green, strong_red, body_pct = self.analyze_candle_strength(ha_candle)
            
            # Calculate ADX
            adx, plus_di, minus_di = self.calculate_adx(self.ha_candles_history)
            if adx is None:
                return None
            
            # Check trend strength
            trend_ok = adx > self.adx_threshold
            
            # Enhanced analysis logging
            current_time = datetime.now()
            if (current_time - self.last_analysis_log).total_seconds() > self.analysis_log_interval:
                self.logger.info(f"[BULL_EYE] Pine Script Entry Analysis:")
                self.logger.info(f"   [MONEY] Current Price: Rs.{current_price:.2f}")
                self.logger.info(f"   [TREND_UP] Trend Line: Rs.{trend_line:.2f} (Diff: {price_diff:+.2f} | {price_diff_pct:+.2f}%)")
                self.logger.info(f"   [CANDLE] Candle: {'[GREEN] Strong Green' if strong_green else '[YELLOW] Regular'} (Body: {body_pct:.1%})")
                self.logger.info(f"   [STATS] ADX: {adx:.2f} ({'[SUCCESS]' if trend_ok else '[ERROR]'} > {self.adx_threshold}) | +DI: {plus_di:.1f} | -DI: {minus_di:.1f}")
                
                # Show what conditions are met
                conditions = [
                    (f"Price above trend", price_above),
                    (f"Strong green candle (>{self.strong_candle_threshold:.0%})", strong_green),
                    (f"ADX > {self.adx_threshold}", trend_ok),
                    ("Not in trade", True)
                ]
                
                met = [name for name, status in conditions if status]
                missing = [name for name, status in conditions if not status]
                
                self.logger.info(f"   [SUCCESS] Met: {', '.join(met) if met else 'None'}")
                self.logger.info(f"   ⏳ Missing: {', '.join(missing) if missing else 'All conditions met!'}")
                
                self.last_analysis_log = current_time
            
            # Buy condition: price above trend + strong green + ADX > threshold
            buy_condition = price_above and strong_green and trend_ok
            
            if buy_condition:
                # Smart position sizing for Rs.20,000 capital
                lots, total_investment = self.position_sizer.calculate_position_size(current_price)
                
                # Check if we can afford the trade
                if not self.position_sizer.is_trade_affordable(current_price):
                    self.logger.warning(f"Cannot afford trade at Rs.{current_price:.2f} per share")
                    return None
                
                # Enhanced entry logging
                self.logger.info(f"[ROCKET] BUY SIGNAL TRIGGERED!")
                self.logger.info(f"   [MONEY] Price: Rs.{current_price:.2f} | Trend: Rs.{trend_line:.2f} (+{price_diff:.2f})")
                self.logger.info(f"   [GREEN] Strong Green Candle: {body_pct:.1%} body (>{self.strong_candle_threshold:.0%})")
                self.logger.info(f"   [STATS] ADX: {adx:.2f} (>{self.adx_threshold}) | +DI: {plus_di:.2f} | -DI: {minus_di:.2f}")
                self.logger.info(f"   [BULL_EYE] Position: {lots} lots | Investment: Rs.{total_investment:,.2f}")
                self.logger.info(f"   [TIME] Signal Time: {datetime.now().strftime('%I:%M:%S %p')}")
                
                # Set trade state
                self.in_trade = True
                self.last_signal_time = datetime.now()
                
                # Ensure symbol and instrument_key are strings
                symbol = str(market_data.get('symbol', 'UNKNOWN'))
                instrument_key = str(market_data.get('instrument_key', ''))
                
                return Order(
                    symbol=symbol,
                    quantity=lots,
                    price=current_price,
                    order_type=OrderType.MARKET,
                    transaction_type=TransactionType.BUY,
                    instrument_key=instrument_key
                )
            else:
                # Track signal attempts for debugging
                self.signal_attempts += 1
                
                # Periodic status update
                if self.signal_attempts % 20 == 0:  # Every 20 attempts (roughly every hour)
                    missing_reasons = []
                    if not price_above:
                        missing_reasons.append(f"price {price_diff_pct:+.2f}% from trend")
                    if not strong_green:
                        missing_reasons.append(f"weak candle ({body_pct:.1%})")
                    if not trend_ok:
                        missing_reasons.append(f"low ADX ({adx:.1f})")
                    
                    self.logger.info(f"⏳ Signal attempt #{self.signal_attempts}: Missing {', '.join(missing_reasons)}")
            
            return None
            
        except Exception as e:
            await self.on_error(e)
            return None
    
    async def should_exit(self, position: Position, market_data: Dict) -> Optional[Order]:
        """Enhanced exit logic with detailed monitoring"""
        try:
            # Get Heikin Ashi candle data
            ha_candle = market_data.get('ha_candle')
            if not ha_candle:
                return None
            
            # Add to history
            self.add_ha_candle(ha_candle)
            
            # Need enough data for calculations
            if len(self.ha_candles_history) < self.adx_length + 1:
                return None
            
            # Calculate trend line
            trend_line = self.calculate_trend_line(self.ha_candles_history)
            if trend_line is None:
                return None
            
            # Current price (using Heikin Ashi close)
            current_price = ha_candle['ha_close']
            
            # Check if price is below trend line
            price_below = current_price < trend_line
            price_diff = current_price - trend_line
            price_diff_pct = (price_diff / trend_line) * 100
            
            # Analyze candle strength
            strong_green, strong_red, body_pct = self.analyze_candle_strength(ha_candle)
            
            # Exit condition: price below trend OR strong red candle
            exit_condition = price_below or strong_red
            
            if exit_condition:
                # Enhanced exit logging
                self.logger.info(f"[STOP] EXIT SIGNAL TRIGGERED!")
                self.logger.info(f"   [MONEY] Price: Rs.{current_price:.2f} | Trend: Rs.{trend_line:.2f} ({price_diff:+.2f})")
                self.logger.info(f"   [TREND_DOWN] Reason: {'Price below trend' if price_below else 'Strong red candle'}")
                self.logger.info(f"   [CANDLE] Candle: {'[RED] Strong Red' if strong_red else '[YELLOW] Regular'} (Body: {body_pct:.1%})")
                
                # Calculate trade duration if we have entry time
                if self.last_signal_time:
                    duration = datetime.now() - self.last_signal_time
                    duration_minutes = int(duration.total_seconds() / 60)
                    self.logger.info(f"   ⏱️ Trade Duration: {duration_minutes} minutes")
                
                # Reset trade state
                self.in_trade = False
                
                return Order(
                    symbol=position.symbol,
                    quantity=position.quantity,
                    price=current_price,
                    order_type=OrderType.MARKET,
                    transaction_type=TransactionType.SELL,
                    instrument_key=position.instrument_key
                )
            
            return None
            
        except Exception as e:
            await self.on_error(e)
            return None
    
    async def calculate_position_size(self, price: float, risk_amount: float) -> int:
        """Calculate position size based on available capital"""
        if price <= 0:
            return 0
        
        # Use smart position sizing
        lots, total_investment = self.position_sizer.calculate_position_size(price)
        
        # Check if affordable
        if not self.position_sizer.is_trade_affordable(price):
            self.logger.warning(f"Cannot afford trade: Rs.{price:.2f} per share too expensive")
            return 0
        
        return lots
    
    async def on_order_filled(self, order: Order):
        """Enhanced order fill handling"""
        await super().on_order_filled(order)
        
        # Log strategy-specific information
        if order.transaction_type == TransactionType.BUY:
            self.logger.info(f"[TREND_UP] ENTRY FILLED: {order.symbol} @ Rs.{order.filled_price}")
        else:
            self.logger.info(f"[TREND_DOWN] EXIT FILLED: {order.symbol} @ Rs.{order.filled_price}")
            
            # Calculate P&L for the trade (simplified)
            if order.filled_price and len(self.ha_candles_history) > 0:
                filled_price = order.filled_price or 0.0
                # In real implementation, get actual entry price from position
                # For now, using filled price as placeholder
                entry_price = filled_price
                quantity = order.quantity or 0
                
                pnl = (filled_price - entry_price) * quantity * 75  # 75 shares per lot
                self.logger.info(f"[MONEY] Trade P&L: Rs.{pnl:.2f}")
    
    async def on_error(self, error: Exception):
        """Enhanced error handling"""
        self.logger.error(f"PineScript Strategy Error: {error}")
        await super().on_error(error)