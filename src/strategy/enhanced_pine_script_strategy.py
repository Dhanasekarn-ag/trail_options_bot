#trading bot 

# ==================== src/strategy/enhanced_pine_script_strategy.py ====================
import logging
import numpy as np
from datetime import datetime, time
from typing import Dict, List, Optional, Union
from src.strategy.base_strategy import BaseStrategy
from src.models.order import Order, OrderType, TransactionType
from src.models.position import Position
from src.utils.option_instruments import get_instrument_key

class EnhancedPineScriptStrategy(BaseStrategy):
    """Enhanced Pine Script Strategy with Options Integration and Greeks Analysis"""
    
    def __init__(self, name: str, config: Dict):
        super().__init__(name, config)
        self.logger = logging.getLogger(__name__)
        
        # Strategy configuration
        self.strategy_id = config.get('strategy_id', 'Enhanced_Pine_Script')
        self.trading_mode = config.get('trading_mode', 'BIDIRECTIONAL')
        
        # INITIALIZE POSITION TRACKING PROPERLY
        self.position_count = 0
        self.used_capital = 0
        self.active_positions = {}  # Track positions by key
        self.max_positions = config.get('max_positions', 6)
        
        # Technical indicators parameters
        self.adx_length = config.get('adx_length', 14)
        self.adx_threshold = config.get('adx_threshold', 20)
        self.strong_candle_threshold = config.get('strong_candle_threshold', 0.60)
        
        # Option preferences
        self.prefer_atm_for_trends = config.get('prefer_atm_for_trends', True)
        self.use_itm_for_strong_signals = config.get('use_itm_for_strong_signals', True)
        self.itm_points = config.get('itm_points', 100)
        
        # Greeks risk management
        self.max_theta_risk = config.get('max_theta_risk', 25)
        self.min_delta_threshold = config.get('min_delta_threshold', 0.3)
        self.max_vega_exposure = config.get('max_vega_exposure', 50)
        
        # Capital management
        self.total_capital = config.get('total_capital', 50000)
        self.max_risk_pct = config.get('max_risk_pct', 0.80)
        self.risk_per_trade = config.get('risk_per_trade', 40000)
        self.max_daily_loss = config.get('max_daily_loss', 3000)
        self.max_consecutive_losses = config.get('max_consecutive_losses', 3)
        
        # State tracking
        self.ha_candles_history: List[Dict] = []
        self.in_trade = False
        self.consecutive_losses = 0
        self.daily_pnl = 0.0
        
        # Option chain manager will be set by trading bot
        self.option_chain_manager = None
        
        # Expected performance metrics
        self.expected_metrics = {
            'expected_win_rate': 67.0,
            'expected_monthly_return': 4.0,
            'expected_avg_profit': 890.0,
            'max_drawdown_target': 15.0
        }
        
        # Load all configuration
        self.load_configuration(config)
        
         # Performance tracking for reports
        self.trades_today = []
        self.daily_pnl = 0.0
        self.consecutive_losses = 0
        
        # Heikin Ashi candle history
        self.ha_candles_history = []
        
            
        self.logger.info(f"Enhanced Pine Script Strategy initialized: {self.trading_mode} mode")

        self.logger.info(f"Strategy initialized: {self.trading_mode} mode")
        self.logger.info(f"Capital: Rs.{self.total_capital:,} | Max per trade: Rs.{self.max_risk_per_trade:,}")

    
    def load_configuration(self, config: Dict):
        """Load all configuration parameters"""
        # Strategy parameters
        self.strategy_id = config.get('strategy_id', 'Enhanced_NIFTY')
        self.trading_mode = config.get('trading_mode', 'BIDIRECTIONAL')
        
        # Technical indicators
        self.adx_length = config.get('adx_length', 14)
        self.adx_threshold = config.get('adx_threshold', 20)
        self.strong_candle_threshold = config.get('strong_candle_threshold', 0.60)
        
        # Capital management
        self.total_capital = config.get('total_capital', 50000)
        self.max_risk_per_trade = config.get('max_risk_per_trade', 40000)
        
        # Symbol configuration
        self.allowed_symbols = config.get('allowed_symbols', ['NIFTY'])
        self.lot_sizes = config.get('lot_sizes', {'NIFTY': 75, 'BANKNIFTY': 35, 'SENSEX': 20})
        
        # Strike selection
        self.strike_selection = config.get('strike_selection', 'ATM')
        self.strike_interval = config.get('strike_interval', 50)
        
        # Risk management
        self.initial_stop_loss = config.get('initial_stop_loss', 0.30)
        self.initial_target = config.get('initial_target', 0.50)
        self.trailing_stops = config.get('trailing_stops', [])
        
        # Time management
        self.trading_start_time = config.get('trading_start_time', '09:30')
        self.no_entry_after = config.get('no_entry_after', '15:10')
        self.auto_square_off_time = config.get('auto_square_off_time', '15:20')
        
        # Greeks parameters
        self.max_theta_risk = config.get('max_theta_risk', 25)
        self.min_delta_threshold = config.get('min_delta_threshold', 0.3)
        self.max_vega_exposure = config.get('max_vega_exposure', 50)
    
    
    def get_lot_size(self, symbol: str) -> int:
        """Get correct lot size for symbol"""
        base_symbol = symbol.replace('_CE', '').replace('_PE', '')
        return self.lot_sizes.get(base_symbol, 75)
    
    def calculate_strike_price(self, spot_price: float, option_type: str) -> int:
        """Calculate exact strike price"""
        # Round to nearest strike interval
        base_strike = round(spot_price / self.strike_interval) * self.strike_interval
        
        if self.strike_selection == 'ATM':
            return base_strike
        elif self.strike_selection == 'ITM':
            if option_type == 'CE':
                return base_strike - self.strike_interval  # ITM for CE
            else:  # PE
                return base_strike + self.strike_interval  # ITM for PE
        elif self.strike_selection == 'OTM':
            if option_type == 'CE':
                return base_strike + self.strike_interval  # OTM for CE
            else:  # PE
                return base_strike - self.strike_interval  # OTM for PE
        
        return base_strike
    
    def get_strike_symbol(self, symbol: str, strike: int, option_type: str) -> str:
        """Get formatted strike symbol like 24450CE"""
        return f"{strike}{option_type}"
    
    def check_time_filters(self) -> Dict:
        """Check if current time allows trading"""
        current_time = datetime.now().time()
        
        # Parse time strings
        trading_start = datetime.strptime(self.trading_start_time, '%H:%M').time()
        no_entry_after = datetime.strptime(self.no_entry_after, '%H:%M').time()
        square_off_time = datetime.strptime(self.auto_square_off_time, '%H:%M').time()
        
        return {
            'can_trade': trading_start <= current_time <= no_entry_after,
            'should_square_off': current_time >= square_off_time,
            'time_to_square_off': current_time >= datetime.strptime('15:15', '%H:%M').time()  # Warning time
        }
    
    def set_option_chain_manager(self, manager):
        """Set option chain manager for option selection"""
        self.option_chain_manager = manager
        self.logger.info("Option chain manager configured")
    
    async def should_enter(self, market_data: Dict) -> Optional[Order]:
        """Enhanced entry logic with options integration"""
        try:
            # Check if symbol is allowed
            symbol = market_data.get('symbol', 'UNKNOWN')
            if symbol not in self.allowed_symbols:
                return None
            
            current_positions = len(self.active_positions)
            
            if current_positions >= self.max_positions:
                self.logger.info(f"Max positions ({self.max_positions}) reached. Current: {current_positions}")
                self.logger.info(f"Active positions: {list(self.active_positions.keys())}")
                return None
            
            # Check time filters
            time_status = self.check_time_filters()
            if not time_status['can_trade']:
                self.logger.debug(f"Outside trading hours. Current time: {datetime.now().time()}")
                return None
            
            # Check position limits
            if self.position_count >= self.max_positions:
                self.logger.info(f"Max positions ({self.max_positions}) reached")
                return None
            
            # Check capital availability
            available_capital = self.total_capital - self.used_capital
            if available_capital < self.max_risk_per_trade:
                self.logger.warning(f"Insufficient capital. Available: Rs.{available_capital:.2f}")
                return None
            
            
            # Update HA candles history
            ha_candle = market_data.get('ha_candle')
            ha_candles_history = market_data.get('ha_candles_history', [])
            
            if ha_candles_history:
                self.ha_candles_history = ha_candles_history
            elif ha_candle:
                self.ha_candles_history.append(ha_candle)
            
            # Check if we have enough data
            if len(self.ha_candles_history) < self.adx_length + 1:
                #self.logger.debug(f"Insufficient data: {len(self.ha_candles_history)}/{self.adx_length + 1} candles")
                return None
            
            # Risk management checks
            #if not self._risk_management_check():
            #    return None
            
            # Check if already in trade (for single position strategies)
            #if self.trading_mode != 'BIDIRECTIONAL' and self.in_trade:
            #    return None
            
            # Get current market conditions
            current_price = market_data.get('current_price', 0)
            #symbol = market_data.get('symbol', 'NIFTY')
            
            # Calculate technical indicators
            trend_line = self.calculate_trend_line(self.ha_candles_history)
            if trend_line is None:
                return None
            
            # Get latest candle for analysis
            latest_candle = self.ha_candles_history[-1]
            
            # Analyze candle strength
            strong_green, strong_red, body_pct = self.analyze_candle_strength(latest_candle)
            
            # Calculate ADX
            adx, plus_di, minus_di = self.calculate_adx(self.ha_candles_history)
            if adx is None:
                return None
            
            # Entry conditions
            price_above_trend = current_price > trend_line
            trend_strength_ok = adx > self.adx_threshold
            
            # Determine entry signal
            entry_signal = None
            option_type = None
            
            if self.trading_mode == 'BIDIRECTIONAL':
                # Bidirectional strategy - can trade both CE and PE
                if price_above_trend and strong_green and trend_strength_ok:
                    entry_signal = 'BUY_CE'
                    option_type = 'CE'
                elif not price_above_trend and strong_red and trend_strength_ok:
                    entry_signal = 'BUY_PE'
                    option_type = 'PE'
            
            if entry_signal:
                self.logger.info(f"ENTRY SIGNAL: {entry_signal} - Price: {current_price:.2f}, Trend: {trend_line:.2f}, ADX: {adx:.1f}")
                
                # Create order with proper strike calculation
                order = await self._create_option_order(
                    symbol=symbol,
                    option_type = option_type,
                    current_price=current_price,
                    signal_strength=body_pct,
                    market_data=market_data
                )
                
                if order:
                     # ADD TO POSITION TRACKING
                    position_key = f"{symbol}_{order.option_type}_{datetime.now().strftime('%H%M%S')}"
                    self.active_positions[position_key] = {
                        'symbol': symbol,
                        'option_type': getattr(order, 'option_type', 'CE'),
                        'quantity': order.quantity,
                        'entry_time': datetime.now(),
                        'entry_price': order.price
                    }
                    # UPDATE COUNTERS
                    self.position_count = len(self.active_positions)
                    investment = getattr(order, 'total_investment', order.price * order.quantity * 75)
                    self.used_capital += investment
                    
                    self.logger.info(f"Position added: {position_key}")
                    self.logger.info(f"Active positions: {self.position_count}/{self.max_positions}")
                    
                    return order
        except Exception as e:
            self.logger.error(f"Error in should_enter: {e}")
            return None
    
    async def should_exit(self, position: Position, market_data: Dict) -> Optional[Order]:
        """Enhanced exit logic with trailing stop loss"""
        try:
            current_price = market_data.get('current_price', 0)
            
            # Check for auto square-off time
            time_status = self.check_time_filters()
            if time_status['should_square_off']:
                self.logger.info("AUTO SQUARE-OFF TIME - Closing position")
                return self._create_exit_order(position, current_price, "AUTO_SQUARE_OFF")
          
            
            
            # Update HA candles for exit analysis
            #ha_candles_history = market_data.get('ha_candles_history', [])
            #if ha_candles_history:
            #    self.ha_candles_history = ha_candles_history
            
            # Calculate current P&L
            entry_price = position.average_price
            current_pnl_pct = ((current_price - entry_price) / entry_price) * 100
            
            # Get position details
            option_type = getattr(position, 'option_type', 'CE')
            trailing_stop = getattr(position, 'trailing_stop', -self.initial_stop_loss * 100)
            
            # Check stop loss
            if current_pnl_pct <= trailing_stop:
                self.logger.info(f"STOP LOSS HIT at {current_pnl_pct:.2f}%")
                return self._create_exit_order(position, current_price, "STOP_LOSS")
            
            # Check and update trailing stop
            for level in self.trailing_stops:
                profit_trigger = level['profit'] * 100  # Convert to percentage
                trail_to = level['trail_to'] * 100
                
                if current_pnl_pct >= profit_trigger:
                    if trailing_stop < trail_to:
                        position.trailing_stop = trail_to
                        self.logger.info(f"TRAILING STOP updated to {trail_to:.0f}% at {current_pnl_pct:.2f}% profit")
            
            # Check technical exit conditions
            if len(self.ha_candles_history) >= 3:
                trend_line = self.calculate_trend_line(self.ha_candles_history)
                if trend_line:
                    latest_candle = self.ha_candles_history[-1]
                    strong_green, strong_red, _ = self.analyze_candle_strength(latest_candle)
                    
                    # Exit CE on strong red candle below trend
                    if option_type == 'CE' and strong_red and current_price < trend_line:
                        return self._create_exit_order(position, current_price, "TREND_REVERSAL")
                    # Exit PE on strong green candle above trend
                    elif option_type == 'PE' and strong_green and current_price > trend_line:
                        return self._create_exit_order(position, current_price, "TREND_REVERSAL")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in should_exit: {e}")
            return None
            
            
            
            
            
            # Exit conditions
            exit_reason = None
            
            # 1. Profit target (10% profit)
            if current_pnl_pct >= 10.0:
                exit_reason = "PROFIT_TARGET"
            
            # 2. Stop loss (5% loss)
            elif current_pnl_pct <= -5.0:
                exit_reason = "STOP_LOSS"
            
            # 3. Time-based exit (if held for more than 4 hours)
            elif time_in_trade >= 4.0:
                exit_reason = "TIME_EXIT"
            
            # 4. Technical exit - trend reversal
            elif len(self.ha_candles_history) >= 3:
                trend_line = self.calculate_trend_line(self.ha_candles_history)
                if trend_line:
                    latest_candle = self.ha_candles_history[-1]
                    strong_green, strong_red, _ = self.analyze_candle_strength(latest_candle)
                    
                    # Exit CE on strong red candle below trend
                    if option_type == 'CE' and strong_red and current_price < trend_line:
                        exit_reason = "TREND_REVERSAL"
                    # Exit PE on strong green candle above trend
                    elif option_type == 'PE' and strong_green and current_price > trend_line:
                        exit_reason = "TREND_REVERSAL"
            
            if exit_reason:
                self.logger.info(f"[ALERT] EXIT SIGNAL: {exit_reason} - P&L: {current_pnl_pct:.2f}% ({option_type})")
                
                # Create exit order
                order = Order(
                    symbol=position.symbol,
                    quantity=position.quantity,
                    price=current_price,
                    order_type=OrderType.MARKET,
                    transaction_type=TransactionType.SELL,
                    strategy_name=self.name
                )
                
                # Add option details to order
                order.option_type = option_type
                order.exit_reason = exit_reason
                order.pnl_pct = current_pnl_pct
                
                # Update state
                self.in_trade = False
                
                return order
            
            return None
            
            #except Exception as e:
            #    self.logger.error(f"Error in should_exit: {e}")
            #    return None
    
    
    def _create_exit_order(self, position: Position, current_price: float, exit_reason: str) -> Order:
        """Create exit order with proper details"""
        self.logger.info(f"EXIT SIGNAL: {exit_reason} - Option: {position.option_type}")
        
        # Create exit order
        order = Order(
            symbol=position.symbol,
            quantity=position.quantity,
            price=current_price,
            order_type=OrderType.MARKET,
            transaction_type=TransactionType.SELL,
            strategy_name=self.name
        )
        
        # Add details
        order.option_type = getattr(position, 'option_type', 'CE')
        #order.strike_symbol = getattr(position, 'strike_symbol', '')
        order.exit_reason = exit_reason
        order.entry_price = position.average_price
        
         # REMOVE FROM POSITION TRACKING
        position_symbol = position.symbol
        keys_to_remove = []
        
        for key, pos_data in self.active_positions.items():
            if pos_data['symbol'] == position_symbol:
                keys_to_remove.append(key)
        
        # Remove positions
        for key in keys_to_remove:
            if key in self.active_positions:
                removed_pos = self.active_positions.pop(key)
                
                # UPDATE COUNTERS
                self.position_count = len(self.active_positions)
                
                # Release capital
                lot_size = 75
                released_capital = removed_pos['entry_price'] * removed_pos['quantity'] * lot_size
                self.used_capital = max(0, self.used_capital - released_capital)
                
                self.logger.info(f"Position removed: {key}")
                self.logger.info(f"Active positions: {self.position_count}/{self.max_positions}")
        
        return order
        
        
        # Update position count
        self.position_count = max(0, self.position_count - 1)
        
        # Release capital
        lot_size = self.get_lot_size(position.symbol)
        released_capital = position.average_price * position.quantity * lot_size
        self.used_capital = max(0, self.used_capital - released_capital)
        
        return order
    
    
    
    
    def calculate_trend_line(self, ha_candles: List[Dict]) -> Optional[float]:
        """Calculate trend line using moving average - FIXED VERSION"""
        try:
            if len(ha_candles) < self.adx_length:
                return None
            
            # Get closing prices
            closes = []
            for candle in ha_candles[-self.adx_length:]:
                close_price = candle.get('ha_close', 0)
                if close_price and close_price > 0:
                    closes.append(float(close_price))
            
            if len(closes) < self.adx_length:
                return None
            
            # Simple moving average as trend line
            trend_line = sum(closes) / len(closes)
            return trend_line
            
        except Exception as e:
            self.logger.error(f"Error calculating trend line: {e}")
            return None
    
    def analyze_candle_strength(self, candle: Dict) -> tuple:
        """Analyze candle strength for entry signals"""
        try:
            ha_open = float(candle.get('ha_open', 0))
            ha_high = float(candle.get('ha_high', 0))
            ha_low = float(candle.get('ha_low', 0))
            ha_close = float(candle.get('ha_close', 0))
            
            if not all([ha_open, ha_high, ha_low, ha_close]):
                return False, False, 0.0
            
            # Calculate body percentage
            candle_range = ha_high - ha_low
            if candle_range == 0:
                return False, False, 0.0
            
            body_size = abs(ha_close - ha_open)
            body_pct = body_size / candle_range
            
            # Determine candle color and strength
            is_green = ha_close > ha_open
            is_red = ha_close < ha_open
            
            strong_green = is_green and body_pct >= self.strong_candle_threshold
            strong_red = is_red and body_pct >= self.strong_candle_threshold
            
            return strong_green, strong_red, body_pct
            
        except Exception as e:
            self.logger.error(f"Error analyzing candle strength: {e}")
            return False, False, 0.0
    
    def calculate_adx(self, ha_candles: List[Dict]) -> tuple:
        """Calculate ADX (Average Directional Index)"""
        try:
            if len(ha_candles) < self.adx_length + 1:
                return None, None, None
            
            # Get recent candles for ADX calculation
            recent_candles = ha_candles[-(self.adx_length + 1):]
            
            highs = [float(c.get('ha_high', 0)) for c in recent_candles]
            lows = [float(c.get('ha_low', 0)) for c in recent_candles]
            closes = [float(c.get('ha_close', 0)) for c in recent_candles]
            
            # Calculate True Range (TR)
            tr_values = []
            for i in range(1, len(highs)):
                high_low = highs[i] - lows[i]
                high_close_prev = abs(highs[i] - closes[i-1])
                low_close_prev = abs(lows[i] - closes[i-1])
                tr = max(high_low, high_close_prev, low_close_prev)
                tr_values.append(tr)
            
            if not tr_values:
                return None, None, None
            
            # Calculate +DI and -DI
            plus_dm_values = []
            minus_dm_values = []
            
            for i in range(1, len(highs)):
                plus_dm = max(highs[i] - highs[i-1], 0) if highs[i] - highs[i-1] > lows[i-1] - lows[i] else 0
                minus_dm = max(lows[i-1] - lows[i], 0) if lows[i-1] - lows[i] > highs[i] - highs[i-1] else 0
                
                plus_dm_values.append(plus_dm)
                minus_dm_values.append(minus_dm)
            
            # Smooth the values (simple average for now)
            avg_tr = sum(tr_values) / len(tr_values)
            avg_plus_dm = sum(plus_dm_values) / len(plus_dm_values)
            avg_minus_dm = sum(minus_dm_values) / len(minus_dm_values)
            
            if avg_tr == 0:
                return None, None, None
            
            # Calculate DI values
            plus_di = (avg_plus_dm / avg_tr) * 100
            minus_di = (avg_minus_dm / avg_tr) * 100
            
            # Calculate ADX
            dx = abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10) * 100
            
            # For simplicity, use DX as ADX (normally ADX is smoothed DX)
            adx = dx
            
            return adx, plus_di, minus_di
            
        except Exception as e:
            self.logger.error(f"Error calculating ADX: {e}")
            return None, None, None
    
    #async def _create_option_order(self, symbol: str, option_type: str, current_price: float, 
    #                             signal_strength: float, market_data: Dict) -> Optional[Order]:
        #"""Create option order with enhanced selection logic"""
        #try:
            # For paper trading, create a synthetic option order
            # In real implementation, this would use option chain manager
            
            # Calculate position size based on risk management
            #risk_amount = min(self.risk_per_trade, self.total_capital * self.max_risk_pct)

                # Assume option premium based on ATM/ITM selection
            #if self.use_itm_for_strong_signals and signal_strength > 0.7:
                # ITM option - higher premium but better delta
            #    option_premium = current_price * 0.02  # ~2% of underlying
            #    strike_offset = self.itm_points if option_type == 'CE' else -self.itm_points
            #else:
                # ATM option - balanced premium and delta
            #    option_premium = current_price * 0.015  # ~1.5% of underlying
            #    strike_offset = 0
            
            # Calculate quantity (number of lots)
            #lot_size = 75  # NIFTY lot size
            
            # FIX: Ensure minimum 1 lot
            #if option_premium > 0:
            #    shares_affordable = int(risk_amount / option_premium)
            #    lots = max(1, shares_affordable // lot_size)  # Ensure at least 1 lot
            #else:
            #    lots = 1  # Default to 1 lot if premium calculation fails    
                        
            # Limit to maximum lots based on capital
            #max_lots = max(1, int(self.total_capital / (option_premium * lot_size)))
            #lots = min(lots, max_lots, 3)  # Cap at 3 lots max
            
            # Ensure lots is never 0
            #lots = max(1, lots)
        
            # Create order
            #order = Order(
            #    symbol=f"{symbol}_{option_type}",
            #    quantity=lots,
            #    price=option_premium,
            #    order_type=OrderType.MARKET,
            #    transaction_type=TransactionType.BUY,
            #    strategy_name=self.name
            #    )
            
            # Add option-specific details
            #order.option_type = option_type
            #order.strike_price = current_price + strike_offset
            #order.expiry = "Weekly"
            #order.strategy_mode = self.trading_mode
            
            # Add synthetic Greeks for paper trading
            #order.greeks = self._calculate_synthetic_greeks(option_type, current_price, option_premium)
            
            #self.logger.info(f"Created {option_type} order: {lots} lots @ Rs.{option_premium:.2f}")    
        
            #return order
            
        #except Exception as e:
            #self.logger.error(f"Error creating option order: {e}")
            #return None
    
    
    async def _create_option_order(self, symbol: str, option_type: str, current_price: float, 
                                 signal_strength: float, market_data: Dict) -> Optional[Order]:
        """Create option order with proper calculations"""
        try:
            # Calculate strike price
            strike_price = self.calculate_strike_price(current_price, option_type)
            strike_symbol = self.get_strike_symbol(symbol, strike_price, option_type)
            
            # Get lot size
            lot_size = self.get_lot_size(symbol)
            
            # Estimate option premium (simplified - in real trading, fetch from market)
            if symbol == "NIFTY":
                base_premium = 120  # Average NIFTY option premium
            else:
                base_premium = 150
            
            # Adjust for moneyness
            if self.strike_selection == 'ITM':
                option_premium = base_premium * 1.3
            elif self.strike_selection == 'OTM':
                option_premium = base_premium * 0.7
            else:  # ATM
                option_premium = base_premium
            
            # Calculate investment
            lots = 1  # Start with 1 lot
            total_investment = option_premium * lot_size * lots
            
            # Check if investment exceeds limit
            if total_investment > self.max_risk_per_trade:
                self.logger.warning(f"Investment Rs.{total_investment:.2f} exceeds limit Rs.{self.max_risk_per_trade}")
                return None
            
            # Create order
            order = Order(
                symbol=f"{symbol}_{option_type}",
                quantity=lots,
                price=option_premium,
                order_type=OrderType.MARKET,
                transaction_type=TransactionType.BUY,
                strategy_name=self.name
            )
            
            # Add complete option details
            order.option_type = option_type
            order.strike_price = strike_price
            order.strike_symbol = strike_symbol  # e.g., "24450CE"
            order.expiry = "Weekly"
            order.lot_size = lot_size
            order.total_investment = total_investment
            
            # Update used capital
            self.used_capital += total_investment
            
            self.logger.info(f"Created {strike_symbol} order: {lots} lot @ Rs.{option_premium:.2f}")
            self.logger.info(f"Investment: Rs.{total_investment:.2f} | Available: Rs.{self.total_capital - self.used_capital:.2f}")
            
            # Update daily trades
            self.trades_today.append({
                'time': datetime.now(),
                'symbol': strike_symbol,
                'type': option_type,
                'action': 'BUY',
                'price': option_premium,
                'quantity': lots,
                'investment': total_investment
            })
            
            return order
            
        except Exception as e:
            self.logger.error(f"Error creating option order: {e}")
            return None
    
    def get_realistic_option_premium(self, strike_price: int, option_type: str, 
                                   spot_price: float, time_to_expiry: float = 0.1) -> float:
        """Calculate realistic option premium based on market conditions"""
        
        try:
            # Calculate intrinsic value
            if option_type == 'CE':
                intrinsic_value = max(0, spot_price - strike_price)
            else:  # PE
                intrinsic_value = max(0, strike_price - spot_price)
            
            # Calculate time value (simplified Black-Scholes approximation)
            volatility = 0.20  # 20% implied volatility (typical for NIFTY)
            
            # Simplified time value calculation
            time_value = spot_price * volatility * (time_to_expiry ** 0.5) * 0.4
            
            # Adjust based on moneyness
            moneyness_factor = abs(spot_price - strike_price) / spot_price
            
            if moneyness_factor < 0.01:  # ATM
                time_value *= 1.0
            elif moneyness_factor < 0.02:  # Near ATM
                time_value *= 0.8
            else:  # Far OTM/ITM
                time_value *= 0.5
            
            # Total premium = Intrinsic + Time value
            total_premium = intrinsic_value + time_value
            
            # Ensure minimum premium (options can't be too cheap)
            total_premium = max(total_premium, 5.0)  # Minimum Rs.5
            
            # Round to realistic values
            return round(total_premium, 2)
            
        except Exception as e:
            self.logger.error(f"Error calculating realistic premium: {e}")
            return 50.0  # Default fallback

    async def fixed_create_option_order(self, symbol: str, option_type: str, 
                                      current_price: float, signal_strength: float, 
                                      market_data: Dict) -> Optional[Order]:
        """FIXED: Create order with realistic pricing"""
        
        try:
            # Calculate strike price
            strike_price = self.calculate_strike_price(current_price, option_type)
            strike_symbol = self.get_strike_symbol(symbol, strike_price, option_type)
            
            # [SUCCESS] GET REALISTIC PREMIUM INSTEAD OF FIXED Rs.120
            option_premium = self.get_realistic_option_premium(
                strike_price, option_type, current_price
            )
            
            # Log the realistic pricing
            self.logger.info(f"Realistic premium for {strike_symbol}: Rs.{option_premium:.2f} "
                           f"(Spot: {current_price:.2f}, Strike: {strike_price})")
            
            # Get lot size
            lot_size = self.get_lot_size(symbol)
            
            # Calculate investment
            lots = 1  # Start with 1 lot
            total_investment = option_premium * lot_size * lots
            
            # Check if investment exceeds limit
            if total_investment > self.max_risk_per_trade:
                self.logger.warning(f"Investment Rs.{total_investment:.2f} exceeds limit")
                return None
            
            # Create order with REALISTIC pricing
            order = Order(
                symbol=f"{symbol}_{option_type}",
                quantity=lots,
                price=option_premium,  # [SUCCESS] REALISTIC PRICE
                order_type=OrderType.MARKET,
                transaction_type=TransactionType.BUY,
                strategy_name=self.name
            )
            
            # Add complete option details
            order.option_type = option_type
            order.strike_price = strike_price
            order.strike_symbol = strike_symbol
            order.lot_size = lot_size
            order.total_investment = total_investment
            
            self.logger.info(f"Created {strike_symbol} order: {lots} lot @ Rs.{option_premium:.2f}")
            
            return order
            
        except Exception as e:
            self.logger.error(f"Error creating option order: {e}")
            return None     
    
    
    def _calculate_synthetic_greeks(self, option_type: str, spot_price: float, premium: float) -> Dict:
        """Calculate synthetic Greeks for paper trading"""
        try:
            # Synthetic Greeks based on typical option behavior
            if option_type == 'CE':
                delta = 0.5  # Neutral delta for ATM CE
                theta = -premium * 0.1  # 10% daily decay
                vega = premium * 0.2   # 20% sensitivity to volatility
            else:  # PE
                delta = -0.5  # Negative delta for PE
                theta = -premium * 0.1
                vega = premium * 0.2
            
            # Risk score based on Greeks
            risk_score = "MODERATE"
            if abs(theta) > self.max_theta_risk:
                risk_score = "HIGH"
            elif abs(delta) < self.min_delta_threshold:
                risk_score = "LOW"
            
            return {
                'delta': delta,
                'theta': theta,
                'vega': vega,
                'gamma': 0.01,  # Placeholder
                'risk_score': risk_score
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating synthetic Greeks: {e}")
            return {}
    
    def _risk_management_check(self) -> bool:
        """Check risk management conditions"""
        try:
            # Check daily loss limit
            if self.daily_pnl <= -self.max_daily_loss:
                self.logger.warning(f"Daily loss limit reached: {self.daily_pnl}")
                return False
            
            # Check consecutive losses
            if self.consecutive_losses >= self.max_consecutive_losses:
                self.logger.warning(f"Max consecutive losses reached: {self.consecutive_losses}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in risk management check: {e}")
            return False
    
    async def on_order_filled(self, order: Order):
        """Handle order fill events"""
        try:
            if order.transaction_type == TransactionType.BUY:
                self.logger.info(f"Entry order filled: {order.symbol} @ Rs.{order.price:.2f}")
            else:
                self.logger.info(f"Exit order filled: {order.symbol} @ Rs.{order.price:.2f}")
                
                # Update consecutive losses if it's a loss
                if hasattr(order, 'pnl_pct') and order.pnl_pct < 0:
                    self.consecutive_losses += 1
                else:
                    self.consecutive_losses = 0  # Reset on profitable trade
            
        except Exception as e:
            self.logger.error(f"Error handling order fill: {e}")
    
    def get_strategy_status(self) -> Dict:
        """Get current strategy status"""
        return {
            'strategy_name': self.name,
            'trading_mode': self.trading_mode,
            'in_trade': self.in_trade,
            'candles_count': len(self.ha_candles_history),
            'consecutive_losses': self.consecutive_losses,
            'daily_pnl': self.daily_pnl,
            'is_active': self.is_active,
            'expected_win_rate': self.expected_metrics['expected_win_rate']
        }
        
    async def _get_real_market_premium(self, strike: int, option_type: str, symbol: str) -> float:
        """Get option premium - with fallback"""
        try:
            # Get instrument key
            instrument_key = get_instrument_key(strike, option_type)

            if not instrument_key:
                self.logger.error(f"No instrument key found for {strike}{option_type}")
                return None
        
            self.logger.info(f"Fetching price for {strike}{option_type} using key: {instrument_key}")
        
            # Fetch LTP from Upstox
            base_url = "https://api.upstox.com/v2"
            url = f"{base_url}/market-quote/ltp?symbol={instrument_key}"
        
            headers = {
                'Authorization': f'Bearer {self.upstox_client.access_token}',
                'Accept': 'application/json'
            }
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                    
                        # Parse response
                        if 'data' in data and instrument_key in data['data']:
                            ltp = data['data'][instrument_key].get('last_price', 0)
                        
                            if ltp > 0:
                                self.logger.info(f"[SUCCESS] REAL PRICE for {strike}{option_type}: Rs.{ltp}")
                                return float(ltp)
        
            self.logger.error(f"Failed to get real price for {strike}{option_type}")
            return None
        
        except Exception as e:
            self.logger.error(f"Error fetching real premium: {e}")
            return None
        
    async def _create_realistic_option_order(self, symbol: str, option_type: str, current_price: float, 
                                       signal_strength: float, market_data: Dict) -> Optional[Order]:
        """[SUCCESS] FIXED Create order with REALISTIC market-based pricing"""
        try:
            strike_price = self.calculate_strike_price(current_price, option_type)
            strike_symbol = self.get_strike_symbol(symbol, strike_price, option_type)
        
            # [SUCCESS] USE ULTRA REALISTIC MARKET-BASED PRICING
            #option_premium = self._get_market_based_premium(strike_price, option_type, current_price)
            option_premium = await self._get_real_market_premium(strike_price, option_type, symbol)
            
            if option_premium is None:
                # Fallback to simulated price
                self.logger.warning(f"Using simulated price for {strike_symbol}")
                option_premium = self._get_market_based_premium(strike_price, option_type, current_price)
            
            # [SUCCESS] LOG REALISTIC PRICING DETAILS
            distance = strike_price - current_price if option_type == 'CE' else current_price - strike_price
            moneyness = "ITM" if distance < 0 else "ATM" if abs(distance) < 25 else "OTM"
        
            self.logger.info(f"[MONEY] REALISTIC premium for {strike_symbol}: Rs.{option_premium:.2f}")
            self.logger.info(f"   [STATS] Spot: {current_price:.2f} | Strike: {strike_price} | Distance: {distance:+.0f} points ({moneyness})")
        
            lot_size = self.get_lot_size(symbol)
            lots = 1
            total_investment = option_premium * lot_size * lots
        
            if total_investment > self.max_risk_per_trade:
                self.logger.warning(f"Investment Rs.{total_investment:.2f} exceeds limit Rs.{self.max_risk_per_trade}")
                return None
        
            order = Order(
                symbol=f"{symbol}_{option_type}",
                quantity=lots,
                price=option_premium,  # [SUCCESS] NOW REALISTIC!
                order_type=OrderType.MARKET,
                transaction_type=TransactionType.BUY,
                strategy_name=self.name
            )
        
            order.option_type = option_type
            order.strike_price = strike_price
            order.strike_symbol = strike_symbol
            order.lot_size = lot_size
            order.total_investment = total_investment

            self.logger.info(f"[SUCCESS] Created {strike_symbol} order: {lots} lot @ Rs.{option_premium:.2f} (Investment: Rs.{total_investment:,.2f})")

            return order
        
        except Exception as e:
            self.logger.error(f"Error creating realistic option order: {e}")
            return None