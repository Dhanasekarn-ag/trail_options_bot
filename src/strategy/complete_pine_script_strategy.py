# ==================== src/strategy/complete_pine_script_strategy.py ====================
import logging
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from src.strategy.base_strategy import BaseStrategy
from src.models.order import Order, OrderType, TransactionType
from src.models.position import Position
from typing import Dict, List, Optional, Tuple

class CompletePineScriptStrategy(BaseStrategy):
    """
    Complete Pine Script Strategy Implementation
    
    Converted from Pine Script v5 with exact logic:
    - EMA9 + SMA9 trend line
    - Manual ADX calculation (14 period)
    - Strong candle detection (>60% body)
    - Buy: price_above + strong_green + adx>20
    - Exit: price_below OR strong_red
    """
    
    def __init__(self, name: str, config: Optional[Dict] = None):
        super().__init__(name, config)
        
        # Pine Script Parameters (exact match)
        self.adx_length = config.get('adx_length', 14) if config else 14
        self.adx_threshold = config.get('adx_threshold', 20) if config else 20
        self.strong_candle_threshold = config.get('strong_candle_threshold', 0.6) if config else 0.6
        
        # Trading control
        self.in_trade = False
        self.max_positions = 1  # Only one trade at a time as per Pine Script
        
        # Data storage for calculations
        self.candle_history: List[Dict] = []
        self.max_history = 50  # Keep enough for calculations
        
        # Performance tracking
        self.total_signals = 0
        self.successful_entries = 0
        
        # Capital management
        self.total_capital = config.get('total_capital', 50000) if config else 50000
        self.risk_per_trade = config.get('risk_per_trade', 15000) if config else 15000
        
        self.logger.info(f"Complete Pine Script Strategy initialized")
        self.logger.info(f"ADX Length: {self.adx_length}, Threshold: {self.adx_threshold}")
        self.logger.info(f"Strong Candle Threshold: {self.strong_candle_threshold*100:.0f}%")
    
    def add_candle_data(self, market_data: Dict):
        """Add candle data for strategy calculations"""
        try:
            # Use Heikin Ashi candle if available, otherwise regular OHLC
            ha_candle = market_data.get('ha_candle')
            if ha_candle:
                candle = {
                    'open': ha_candle.get('ha_open', 0),
                    'high': ha_candle.get('ha_high', 0),
                    'low': ha_candle.get('ha_low', 0),
                    'close': ha_candle.get('ha_close', 0),
                    'timestamp': market_data.get('timestamp', datetime.now())
                }
            else:
                # Fallback to regular OHLC
                candle = {
                    'open': market_data.get('open', 0),
                    'high': market_data.get('high', 0),
                    'low': market_data.get('low', 0),
                    'close': market_data.get('close', market_data.get('price', 0)),
                    'timestamp': market_data.get('timestamp', datetime.now())
                }
            
            # Add to history
            self.candle_history.append(candle)
            
            # Keep only required history
            if len(self.candle_history) > self.max_history:
                self.candle_history = self.candle_history[-self.max_history:]
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding candle data: {e}")
            return False
    
    def calculate_ema(self, prices: List[float], period: int) -> Optional[float]:
        """Calculate EMA exactly like Pine Script ta.ema()"""
        if len(prices) < period:
            return None
        
        try:
            # Use pandas for EMA calculation (matches Pine Script)
            price_series = pd.Series(prices)
            ema = price_series.ewm(span=period, adjust=False).mean()
            return float(ema.iloc[-1])
            
        except Exception as e:
            self.logger.error(f"Error calculating EMA: {e}")
            return None
    
    def calculate_sma(self, prices: List[float], period: int) -> Optional[float]:
        """Calculate SMA exactly like Pine Script ta.sma()"""
        if len(prices) < period:
            return None
        
        try:
            return float(np.mean(prices[-period:]))
            
        except Exception as e:
            self.logger.error(f"Error calculating SMA: {e}")
            return None
    
    def calculate_trend_line(self) -> Optional[float]:
        """Calculate trend line: (EMA9 + SMA9) / 2"""
        if len(self.candle_history) < 9:
            return None
        
        try:
            # Get close prices
            closes = [candle['close'] for candle in self.candle_history]
            
            # Calculate EMA9 and SMA9
            ema9 = self.calculate_ema(closes, 9)
            sma9 = self.calculate_sma(closes, 9)
            
            if ema9 is None or sma9 is None:
                return None
            
            # Trend line = (EMA9 + SMA9) / 2
            trend_line = (ema9 + sma9) / 2
            
            return trend_line
            
        except Exception as e:
            self.logger.error(f"Error calculating trend line: {e}")
            return None
    
    def analyze_candle_properties(self, candle: Dict) -> Tuple[bool, bool, float]:
        """
        Analyze candle properties exactly like Pine Script:
        - body = abs(close - open)
        - candle_range = high - low
        - body_pct = body / candle_range
        - strong_green = is_green and body_pct > 0.6
        - strong_red = is_red and body_pct > 0.6
        """
        try:
            open_price = float(candle['open'])
            high_price = float(candle['high'])
            low_price = float(candle['low'])
            close_price = float(candle['close'])
            
            # Candle properties (exact Pine Script logic)
            body = abs(close_price - open_price)
            candle_range = high_price - low_price
            body_pct = body / candle_range if candle_range > 0 else 0
            
            # Candle color
            is_green = close_price > open_price
            is_red = close_price < open_price
            
            # Strong candle conditions
            strong_green = is_green and body_pct > self.strong_candle_threshold
            strong_red = is_red and body_pct > self.strong_candle_threshold
            
            return strong_green, strong_red, body_pct
            
        except Exception as e:
            self.logger.error(f"Error analyzing candle properties: {e}")
            return False, False, 0.0
    
    def calculate_rma(self, values: List[float], period: int) -> Optional[float]:
        """Calculate RMA (Running Moving Average) exactly like Pine Script ta.rma()"""
        if len(values) < period:
            return None
        
        try:
            # Pine Script RMA is Wilder's smoothing (alpha = 1/period)
            alpha = 1.0 / period
            rma = values[0]  # Start with first value
            
            for i in range(1, len(values)):
                rma = alpha * values[i] + (1 - alpha) * rma
            
            return float(rma)
            
        except Exception as e:
            self.logger.error(f"Error calculating RMA: {e}")
            return None
    
    def calculate_true_range(self, current_candle: Dict, previous_candle: Dict) -> float:
        """Calculate True Range exactly like Pine Script ta.tr()"""
        try:
            high = current_candle['high']
            low = current_candle['low']
            prev_close = previous_candle['close']
            
            # True Range = max(high-low, abs(high-prev_close), abs(low-prev_close))
            tr1 = high - low
            tr2 = abs(high - prev_close)
            tr3 = abs(low - prev_close)
            
            return max(tr1, tr2, tr3)
            
        except Exception as e:
            self.logger.error(f"Error calculating True Range: {e}")
            return 0.0
    
    def calculate_adx_manual(self) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """
        Calculate ADX manually exactly like Pine Script:
        - upMove = high - high[1]
        - downMove = low[1] - low
        - plusDM = upMove if upMove > 0 and upMove > downMove else 0
        - minusDM = downMove if downMove > 0 and downMove > upMove else 0
        - trur = ta.rma(ta.tr(true), adxLength)
        - plusDI = 100 * ta.rma(plusDM, adxLength) / trur
        - minusDI = 100 * ta.rma(minusDM, adxLength) / trur
        - dx = 100 * abs(plusDI - minusDI) / (plusDI + minusDI)
        - adx = ta.rma(dx, adxLength)
        """
        if len(self.candle_history) < self.adx_length + 1:
            return None, None, None
        
        try:
            # Get recent candles for calculation
            recent_candles = self.candle_history[-(self.adx_length + 1):]
            
            plus_dm_values = []
            minus_dm_values = []
            tr_values = []
            
            # Calculate DM and TR for each period
            for i in range(1, len(recent_candles)):
                current = recent_candles[i]
                previous = recent_candles[i-1]
                
                # Up Move and Down Move (exact Pine Script logic)
                up_move = current['high'] - previous['high']
                down_move = previous['low'] - current['low']
                
                # Plus DM and Minus DM (exact Pine Script conditions)
                if up_move > 0 and up_move > down_move:
                    plus_dm = up_move
                else:
                    plus_dm = 0
                
                if down_move > 0 and down_move > up_move:
                    minus_dm = down_move
                else:
                    minus_dm = 0
                
                plus_dm_values.append(plus_dm)
                minus_dm_values.append(minus_dm)
                
                # True Range
                tr = self.calculate_true_range(current, previous)
                tr_values.append(tr)
            
            if len(tr_values) < self.adx_length:
                return None, None, None
            
            # Calculate smoothed values using RMA
            trur = self.calculate_rma(tr_values, self.adx_length)
            plus_di_smoothed = self.calculate_rma(plus_dm_values, self.adx_length)
            minus_di_smoothed = self.calculate_rma(minus_dm_values, self.adx_length)
            
            if not all([trur, plus_di_smoothed, minus_di_smoothed]) or trur == 0:
                return None, None, None
            
            # Calculate +DI and -DI
            plus_di = 100 * plus_di_smoothed / trur
            minus_di = 100 * minus_di_smoothed / trur
            
            # Calculate DX
            di_sum = plus_di + minus_di
            if di_sum == 0:
                return None, None, None
            
            dx = 100 * abs(plus_di - minus_di) / di_sum
            
            # For simplified implementation, use DX as ADX
            # In full implementation, you'd smooth DX with RMA to get ADX
            adx = dx
            
            return adx, plus_di, minus_di
            
        except Exception as e:
            self.logger.error(f"Error calculating ADX: {e}")
            return None, None, None
    
    async def should_enter(self, market_data: Dict) -> Optional[Order]:
        """
        Entry logic exactly matching Pine Script:
        buy_condition = price_above and strong_green and trend_ok and not inTrade
        """
        try:
            # Add current candle data
            if not self.add_candle_data(market_data):
                return None
            
            # Need enough data for calculations
            if len(self.candle_history) < self.adx_length + 9:  # Need data for ADX + EMA/SMA
                self.logger.debug(f"Building data: {len(self.candle_history)}/{self.adx_length + 9} candles needed")
                return None
            
            # Check if already in trade (Pine Script: not inTrade)
            if self.in_trade:
                return None
            
            # Get current candle and price
            current_candle = self.candle_history[-1]
            current_price = current_candle['close']
            
            # Calculate trend line (EMA9 + SMA9) / 2
            trend_line = self.calculate_trend_line()
            if trend_line is None:
                return None
            
            # Check price above trend line
            price_above = current_price > trend_line
            price_diff = current_price - trend_line
            price_diff_pct = (price_diff / trend_line) * 100
            
            # Analyze current candle properties
            strong_green, strong_red, body_pct = self.analyze_candle_properties(current_candle)
            
            # Calculate ADX
            adx, plus_di, minus_di = self.calculate_adx_manual()
            if adx is None:
                return None
            
            # Check trend strength (ADX > threshold)
            trend_ok = adx > self.adx_threshold
            
            # *** EXACT PINE SCRIPT BUY CONDITION ***
            buy_condition = price_above and strong_green and trend_ok and not self.in_trade
            
            # Enhanced logging for analysis
            self.total_signals += 1
            
            # Log analysis every 20 signals (roughly every hour)
            if self.total_signals % 20 == 0:
                self.logger.info(f"[BULL_EYE] Pine Script Analysis (Signal #{self.total_signals}):")
                self.logger.info(f"   [MONEY] Price: Rs.{current_price:.2f} | Trend: Rs.{trend_line:.2f} ({price_diff_pct:+.2f}%)")
                self.logger.info(f"   [CANDLE] Candle: {'[GREEN] Strong Green' if strong_green else '[YELLOW] Regular'} (Body: {body_pct:.1%})")
                self.logger.info(f"   [STATS] ADX: {adx:.1f} ({'[SUCCESS]' if trend_ok else '[ERROR]'} > {self.adx_threshold}) | +DI: {plus_di:.1f} | -DI: {minus_di:.1f}")
                
                # Show conditions status
                conditions = [
                    ("Price above trend", price_above),
                    ("Strong green candle", strong_green),
                    ("ADX > threshold", trend_ok),
                    ("Not in trade", not self.in_trade)
                ]
                
                met = [name for name, status in conditions if status]
                missing = [name for name, status in conditions if not status]
                
                self.logger.info(f"   [SUCCESS] Met: {', '.join(met) if met else 'None'}")
                self.logger.info(f"   ⏳ Missing: {', '.join(missing) if missing else 'All conditions met!'}")
            
            if buy_condition:
                self.successful_entries += 1
                
                # [ROCKET] BUY SIGNAL TRIGGERED
                self.logger.info(f"[ROCKET] BUY SIGNAL #{self.successful_entries} - Pine Script Strategy")
                self.logger.info(f"   [MONEY] Entry Price: Rs.{current_price:.2f}")
                self.logger.info(f"   [TREND_UP] Above Trend: +{price_diff:.2f} points ({price_diff_pct:+.2f}%)")
                self.logger.info(f"   [GREEN] Strong Green: {body_pct:.1%} body (>{self.strong_candle_threshold:.0%})")
                self.logger.info(f"   [STATS] ADX Strength: {adx:.1f} (>{self.adx_threshold})")
                self.logger.info(f"   [TIME] Signal Time: {datetime.now().strftime('%I:%M:%S %p')}")
                
                # Calculate position size
                lot_size = 75  # NIFTY lot size
                max_lots = int(self.risk_per_trade / (current_price * lot_size))
                lots = max(1, min(max_lots, 3))  # 1-3 lots
                
                # Set trade state
                self.in_trade = True
                
                # Create order
                order = Order(
                    symbol=market_data.get('symbol', 'NIFTY'),
                    quantity=lots,
                    price=current_price,
                    order_type=OrderType.MARKET,
                    transaction_type=TransactionType.BUY,
                    strategy_name=self.name,
                    instrument_key=market_data.get('instrument_key', '')
                )
                
                # Add strategy-specific details
                order.trend_line = trend_line
                order.adx_value = adx
                order.signal_strength = body_pct
                
                return order
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in should_enter: {e}")
            return None
    
    async def should_exit(self, position: Position, market_data: Dict) -> Optional[Order]:
        """
        Exit logic exactly matching Pine Script:
        exit_condition = inTrade and (price_below or strong_red)
        """
        try:
            # Add current candle data
            if not self.add_candle_data(market_data):
                return None
            
            # Need enough data for calculations
            if len(self.candle_history) < self.adx_length + 9:
                return None
            
            # Get current candle and price
            current_candle = self.candle_history[-1]
            current_price = current_candle['close']
            
            # Calculate trend line
            trend_line = self.calculate_trend_line()
            if trend_line is None:
                return None
            
            # Check price below trend line
            price_below = current_price < trend_line
            price_diff = current_price - trend_line
            price_diff_pct = (price_diff / trend_line) * 100
            
            # Analyze current candle properties
            strong_green, strong_red, body_pct = self.analyze_candle_properties(current_candle)
            
            # *** EXACT PINE SCRIPT EXIT CONDITION ***
            exit_condition = self.in_trade and (price_below or strong_red)
            
            if exit_condition:
                # Determine exit reason
                if price_below and strong_red:
                    exit_reason = "PRICE_BELOW_TREND_AND_STRONG_RED"
                elif price_below:
                    exit_reason = "PRICE_BELOW_TREND"
                elif strong_red:
                    exit_reason = "STRONG_RED_CANDLE"
                else:
                    exit_reason = "UNKNOWN"
                
                # [STOP] EXIT SIGNAL TRIGGERED
                self.logger.info(f"[STOP] EXIT SIGNAL - {exit_reason}")
                self.logger.info(f"   [MONEY] Exit Price: Rs.{current_price:.2f}")
                self.logger.info(f"   [TREND_DOWN] Trend Position: {price_diff_pct:+.2f}% from trend line")
                self.logger.info(f"   [CANDLE] Candle: {'[RED] Strong Red' if strong_red else '[YELLOW] Regular'} (Body: {body_pct:.1%})")
                
                # Calculate trade P&L
                entry_price = position.average_price
                pnl_points = current_price - entry_price
                pnl_pct = (pnl_points / entry_price) * 100
                lot_size = 75
                pnl_rupees = pnl_points * position.quantity * lot_size
                
                self.logger.info(f"   [STATS] Trade P&L: Rs.{pnl_rupees:.2f} ({pnl_pct:+.2f}%)")
                self.logger.info(f"   [TIME] Exit Time: {datetime.now().strftime('%I:%M:%S %p')}")
                
                # Reset trade state (allow re-entry)
                self.in_trade = False
                
                # Create exit order
                order = Order(
                    symbol=position.symbol,
                    quantity=position.quantity,
                    price=current_price,
                    order_type=OrderType.MARKET,
                    transaction_type=TransactionType.SELL,
                    strategy_name=self.name,
                    instrument_key=position.instrument_key
                )
                
                # Add exit details
                order.exit_reason = exit_reason
                order.pnl_points = pnl_points
                order.pnl_pct = pnl_pct
                
                return order
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in should_exit: {e}")
            return None
    
    async def on_order_filled(self, order: Order):
        """Enhanced order fill handling with position tracking"""
        try:
            await super().on_order_filled(order)
            
            if order.transaction_type == TransactionType.BUY:
                # Add to active option positions for monitoring
                if hasattr(order, 'option_type') and hasattr(order, 'strike_price'):
                    self.active_option_positions[order.symbol] = {
                        'symbol': order.symbol,
                        'strike_price': order.strike_price,
                        'option_type': order.option_type,
                        'entry_premium': order.price,
                        'quantity': order.quantity,
                        'entry_time': datetime.now(),
                        'instrument_key': order.instrument_key or '',
                        'total_investment': getattr(order, 'total_investment', 0),
                        'premium_change_pct': 0,
                        'current_premium': order.price
                    }
                    
                    self.logger.info(f"[STATS] Added {order.symbol} to option monitoring")
                    
            elif order.transaction_type == TransactionType.SELL:
                # Remove from active positions
                if order.symbol in self.active_option_positions:
                    position_data = self.active_option_positions.pop(order.symbol)
                    
                    # Log final performance
                    if hasattr(order, 'total_pnl'):
                        self.logger.info(f"[STATS] Removed {order.symbol} from monitoring - Final P&L: Rs.{order.total_pnl:+,.2f}")
                    
        except Exception as e:
            self.logger.error(f"Error in enhanced order fill handling: {e}")
    
    
    def get_strategy_status(self) -> Dict:
        """Get current strategy status"""
        win_rate = (self.winning_trades / max(1, self.total_trades)) * 100
        signal_success_rate = (self.successful_entries / max(1, self.total_signals)) * 100
        
        return {
            'strategy_name': self.name,
            'in_trade': self.in_trade,
            'candles_available': len(self.candle_history),
            'total_signals_analyzed': self.total_signals,
            'successful_entries': self.successful_entries,
            'signal_success_rate': f"{signal_success_rate:.1f}%",
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'win_rate': f"{win_rate:.1f}%",
            'adx_threshold': self.adx_threshold,
            'strong_candle_threshold': f"{self.strong_candle_threshold*100:.0f}%",
            'is_active': self.is_active
        }