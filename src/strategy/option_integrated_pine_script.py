# ==================== src/strategy/option_integrated_pine_script.py (FIXED) ====================
import logging
import numpy as np
import pandas as pd
import aiohttp
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from src.strategy.complete_pine_script_strategy import CompletePineScriptStrategy
from src.models.order import Order, OrderType, TransactionType
from src.models.position import Position 

class OptionIntegratedPineScript(CompletePineScriptStrategy):
    """
    Pine Script Strategy with REAL Option Trading Integration - FIXED VERSION
    
    Features:
    - Real-time option chain data from Upstox
    - ATM/OTM strike selection based on NIFTY spot price
    - Live option premium pricing
    - Uptrend → CE options, Downtrend → PE options
    - Proper bid-ask spread handling
    - FIXED: No Unicode emojis in logging
    """
    
    def __init__(self, name: str, config: Optional[Dict] = None):
        super().__init__(name, config)
        
        # Option trading configuration
        self.option_trading_enabled = config.get('option_trading_enabled', True) if config else True
        self.strike_selection_mode = config.get('strike_selection_mode', 'ATM')  # ATM, OTM, ITM
        self.max_option_premium = config.get('max_option_premium', 200)  # Max Rs.200 per share
        self.min_option_premium = config.get('min_option_premium', 10)   # Min Rs.10 per share
        
        # Strike interval (NIFTY options are in 50-point intervals)
        self.strike_interval = 50
        
        # Option expiry management
        self.preferred_expiry = 'weekly'  # weekly, monthly
        self.min_days_to_expiry = 1       # Avoid same-day expiry
        self.max_days_to_expiry = 7       # Prefer weekly options
        
        # Option chain cache (5-minute cache)
        self.option_chain_cache = {}
        self.cache_duration = 300  # 5 minutes
        
        # Upstox client reference (will be set by trading bot)
        self.upstox_client = None
        
        # Advanced features configuration
        self.enable_premium_monitoring = config.get('enable_premium_monitoring', True) if config else True
        self.monitoring_interval = config.get('monitoring_interval', 30) if config else 30  # seconds
        self.last_monitoring_time = datetime.now()
    
        # Enhanced exit parameters
        self.profit_target_pct = config.get('profit_target_pct', 50) if config else 50    # 50% profit target
        self.stop_loss_pct = config.get('stop_loss_pct', 30) if config else 30           # 30% stop loss
        self.trailing_stop_enabled = config.get('trailing_stop_enabled', True) if config else True
        self.trail_activation_pct = config.get('trail_activation_pct', 25) if config else 25  # Start trailing at 25% profit
        self.trail_step_pct = config.get('trail_step_pct', 10) if config else 10         # Trail by 10%
    
        # Position tracking for advanced features
        self.active_option_positions = {}  # Enhanced position tracking
        self.position_monitoring_data = {}  # Real-time monitoring data
    
        # Performance tracking
        self.total_premium_monitored = 0
        self.monitoring_updates = 0
        self.last_monitoring_time = datetime.now()
        
        # FIXED: Use plain text instead of emojis in logs
        self.logger.info("Advanced Features Enabled:")
        self.logger.info(f"  Premium Monitoring: {self.enable_premium_monitoring}")
        self.logger.info(f"  Profit Target: {self.profit_target_pct}%")
        self.logger.info(f"  Stop Loss: {self.stop_loss_pct}%")
        self.logger.info(f"  Trailing Stop: {self.trailing_stop_enabled}")
        
        self.logger.info(f"Option Integration enabled: {self.option_trading_enabled}")
        self.logger.info(f"Strike Selection: {self.strike_selection_mode}")
        self.logger.info(f"Premium Range: Rs.{self.min_option_premium}-{self.max_option_premium}")
    
    # OVERRIDE the parent should_exit method
    async def should_exit(self, position: Position, market_data: Dict) -> Optional[Order]:
        """
        ENHANCED EXIT: Combines Pine Script logic + Advanced Option features
        
        This OVERRIDES the parent class method to add option-specific exits
        while keeping all the original Pine Script exit logic intact.
        """
        try:
            # === STEP 1: CALL PARENT PINE SCRIPT EXIT LOGIC ===
            # This runs your original Pine Script exit conditions
            pine_script_exit = await super().should_exit(position, market_data)
            
            if pine_script_exit:
                # Pine Script triggered an exit - use it!
                exit_reason = getattr(pine_script_exit, 'exit_reason', 'PINE_SCRIPT_EXIT')
                self.logger.info(f"PINE SCRIPT EXIT TRIGGERED: {exit_reason}")
                
                return pine_script_exit
            
            # === STEP 2: ADVANCED OPTION EXIT LOGIC ===
            # Only check advanced exits if Pine Script didn't trigger
            return await self.should_exit_option(position, market_data)
            
        except Exception as e:
            self.logger.error(f"Error in enhanced should_exit: {e}")
            return None
    
    def set_upstox_client(self, client):
        """Set Upstox client for option data fetching"""
        self.upstox_client = client
        self.logger.info("Upstox client configured for option trading")
    
    async def calculate_option_strike(self, spot_price: float, option_type: str, selection_mode: str = None) -> int:
        """Calculate option strike based on spot price - WORKING VERSION"""
        try:
            # Get available strikes from option chain
            option_chain = await self.option_chain_manager.get_option_chain("NIFTY", 10)
        
            if not option_chain or 'strikes' not in option_chain:
                self.logger.error("Could not get option chain for strike calculation")
                return int(round(spot_price / 50) * 50)  # Fallback to nearest 50
        
            available_strikes = sorted(option_chain['strikes'].keys())
            atm_strike = min(available_strikes, key=lambda x: abs(x - spot_price))
        
            mode = selection_mode or self.strike_selection_mode
        
            if mode == 'ATM':
                selected_strike = atm_strike
            elif mode == 'OTM':
                if option_type == 'CE':
                    # CE OTM: Strike above current price
                    selected_strike = atm_strike + 50
                else:  # PE
                    # PE OTM: Strike below current price
                    selected_strike = atm_strike - 50
            elif mode == 'ITM':
                if option_type == 'CE':
                    # CE ITM: Strike below current price
                    selected_strike = atm_strike - 50
                else:  # PE
                    # PE ITM: Strike above current price
                    selected_strike = atm_strike + 50
            else:
                selected_strike = atm_strike
        
            # Ensure the selected strike exists in available strikes
            if selected_strike not in available_strikes:
                selected_strike = min(available_strikes, key=lambda x: abs(x - selected_strike))
        
            self.logger.debug(f"Calculated strike for {option_type}: {selected_strike} (mode: {mode}, ATM: {atm_strike})")
            return selected_strike
        
        except Exception as e:
            self.logger.error(f"Error calculating option strike: {e}")
            return int(round(spot_price / 50) * 50)  # Fallback
    
    def get_option_symbol(self, strike: int, option_type: str, expiry_date: str = None) -> str:
        """Generate option symbol format: NIFTY24AUG25000CE"""
        try:
            if not expiry_date:
                expiry_date = self.get_nearest_expiry()
            
            # Parse expiry date
            expiry_dt = datetime.strptime(expiry_date, '%Y-%m-%d')
            
            # Format: NIFTY + YY + MMM + DDDD + CE/PE
            year = expiry_dt.strftime('%y')
            month = expiry_dt.strftime('%b').upper()
            day = expiry_dt.day
            
            symbol = f"NIFTY{year}{month}{strike}{option_type}"
            return symbol
            
        except Exception as e:
            self.logger.error(f"Error generating option symbol: {e}")
            return f"NIFTY{strike}{option_type}"
    
    async def get_nearest_expiry(self) -> str:
        """Get nearest expiry date - WORKING VERSION"""
        try:
            # Use the new option chain manager
            option_chain = await self.option_chain_manager.get_option_chain("NIFTY", 1)
            if option_chain and 'expiry_date' in option_chain:
                expiry_date = option_chain['expiry_date']
                # Convert to string format if it's a date object
                if hasattr(expiry_date, 'strftime'):
                    return expiry_date.strftime('%Y-%m-%d')
                return str(expiry_date)
        
            return None
        
        except Exception as e:
            self.logger.error(f"Error getting nearest expiry: {e}")
            return None
    
    async def get_option_instrument_key(self, strike: int, option_type: str) -> Optional[str]:
        """Get option instrument key - WORKING VERSION"""
        try:
            # Get option chain to find the instrument key
            option_chain = await self.option_chain_manager.get_option_chain("NIFTY", 5)
        
            if option_chain and 'strikes' in option_chain:
                if strike in option_chain['strikes']:
                    strike_data = option_chain['strikes'][strike]
                
                    if option_type.upper() == 'CE' and 'ce' in strike_data:
                        instrument_key = strike_data['ce'].get('instrument_key')
                        if instrument_key:
                            self.logger.debug(f"Found {strike}CE instrument key: {instrument_key}")
                            return instrument_key
                
                    elif option_type.upper() == 'PE' and 'pe' in strike_data:
                        instrument_key = strike_data['pe'].get('instrument_key')
                        if instrument_key:
                            self.logger.debug(f"Found {strike}PE instrument key: {instrument_key}")
                            return instrument_key
        
            self.logger.warning(f"Could not find instrument key for {strike}{option_type}")
            return None
        
        except Exception as e:
            self.logger.error(f"Error getting instrument key for {strike}{option_type}: {e}")
            return None
    
    async def fetch_option_ltp(self, strike: int, option_type: str, retries: int = 2) -> Optional[float]:
        """Fetch option LTP - WORKING VERSION"""
        try:
            # Get option chain to find the instrument key
            option_chain = await self.option_chain_manager.get_option_chain("NIFTY", 5)
        
            if option_chain and 'strikes' in option_chain:
                if strike in option_chain['strikes']:
                    strike_data = option_chain['strikes'][strike]
                
                    if option_type.upper() == 'CE' and 'ce' in strike_data:
                        ltp = strike_data['ce'].get('ltp')
                        if ltp is not None:
                            self.logger.debug(f"Fetched {strike}CE LTP: {ltp}")
                            return float(ltp)
                
                    elif option_type.upper() == 'PE' and 'pe' in strike_data:
                        ltp = strike_data['pe'].get('ltp')
                        if ltp is not None:
                            self.logger.debug(f"Fetched {strike}PE LTP: {ltp}")
                            return float(ltp)
        
            self.logger.warning(f"Could not fetch LTP for {strike}{option_type}")
            return None
        
        except Exception as e:
            self.logger.error(f"Error fetching option LTP for {strike}{option_type}: {e}")
            return None
    
    async def get_option_quote_detailed(self, strike: int, option_type: str) -> Dict:
        """Get detailed option quote including bid-ask spread"""
        try:
            if not self.upstox_client:
                return {}
            
            instrument_key = await self.get_option_instrument_key(strike, option_type)
            if not instrument_key:
                return {}
            
            # Fetch detailed quote
            url = f"https://api.upstox.com/v2/market-quote/quotes"
            headers = {
                'Authorization': f'Bearer {self.upstox_client.access_token}',
                'Accept': 'application/json'
            }
            
            params = {'symbol': instrument_key}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if 'data' in data:
                            quote_data = data['data']
                            
                            if quote_data:
                                actual_key = list(quote_data.keys())[0]
                                option_data = quote_data[actual_key]
                                
                                # Extract bid-ask data
                                depth = option_data.get('depth', {})
                                buy_orders = depth.get('buy', [])
                                sell_orders = depth.get('sell', [])
                                
                                bid_price = buy_orders[0].get('price', 0) if buy_orders else 0
                                ask_price = sell_orders[0].get('price', 0) if sell_orders else 0
                                ltp = option_data.get('last_price', 0)
                                
                                return {
                                    'strike': strike,
                                    'option_type': option_type,
                                    'ltp': ltp,
                                    'bid': bid_price,
                                    'ask': ask_price,
                                    'spread': ask_price - bid_price if (ask_price and bid_price) else 0,
                                    'volume': option_data.get('volume', 0),
                                    'oi': option_data.get('oi', 0),
                                    'instrument_key': instrument_key
                                }
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Error getting detailed quote: {e}")
            return {}
    
    async def validate_option_premium(self, strike: int, option_type: str, expected_premium: float) -> bool:
        """Validate option premium - WORKING VERSION"""
        try:
            current_premium = await self.fetch_option_ltp(strike, option_type)
            
            if current_premium is None:
                self.logger.warning(f"Could not validate premium for {strike}{option_type} - no current price")
                return False
            
            # Allow 10% tolerance
            tolerance = 0.10
            min_premium = expected_premium * (1 - tolerance)
            max_premium = expected_premium * (1 + tolerance)
            
            is_valid = min_premium <= current_premium <= max_premium
            
            if not is_valid:
                self.logger.warning(f"Premium validation failed for {strike}{option_type}: "
                                    f"expected {expected_premium:.2f}, got {current_premium:.2f}")
            else:
                self.logger.debug(f"Premium validated for {strike}{option_type}: {current_premium:.2f}")
            
            return is_valid
            
        except Exception as e:
            self.logger.error(f"Error validating option premium: {e}")
            return False
        
    
    async def should_enter(self, market_data: Dict) -> Optional[Order]:
        """
        Enhanced entry logic with REAL option trading
        
        Process:
        1. Run Pine Script analysis on NIFTY spot
        2. If signal detected, determine option type (CE/PE)
        3. Calculate appropriate strike (ATM/OTM)
        4. Fetch real option premium from Upstox
        5. Validate premium and liquidity
        6. Create option order
        """
        try:
            # First, run the standard Pine Script analysis on NIFTY spot
            if not self.add_candle_data(market_data):
                return None
            
            # Need enough data for calculations (23 candles)
            if len(self.candle_history) < self.adx_length + 9:
                return None
            
            # Check if already in trade
            if self.in_trade:
                return None
            
            # Get current NIFTY spot price
            current_candle = self.candle_history[-1]
            spot_price = current_candle['close']
            
            # Calculate Pine Script indicators
            trend_line = self.calculate_trend_line()
            if trend_line is None:
                return None
            
            # Analyze candle and trend
            strong_green, strong_red, body_pct = self.analyze_candle_properties(current_candle)
            adx, plus_di, minus_di = self.calculate_adx_manual()
            
            if adx is None:
                return None
            
            # Determine market direction and option type
            price_above_trend = spot_price > trend_line
            trend_strength_ok = adx > self.adx_threshold
            
            option_type = None
            signal_direction = None
            
            # *** PINE SCRIPT SIGNAL DETECTION ***
            if price_above_trend and strong_green and trend_strength_ok:
                option_type = 'CE'  # Call option for uptrend
                signal_direction = 'BULLISH'
                
            elif not price_above_trend and strong_red and trend_strength_ok:
                option_type = 'PE'  # Put option for downtrend  
                signal_direction = 'BEARISH'
            
            if not option_type:
                return None
            
            # *** OPTION TRADING LOGIC ***
            if self.option_trading_enabled:
                return await self.create_option_order(
                    spot_price=spot_price,
                    option_type=option_type,
                    signal_direction=signal_direction,
                    signal_strength=body_pct,
                    trend_line=trend_line,
                    adx_value=adx,
                    market_data=market_data
                )
            else:
                # Fallback to spot trading
                return await self.create_spot_order(spot_price, option_type, market_data)
            
        except Exception as e:
            self.logger.error(f"Error in enhanced should_enter: {e}")
            return None
    
    async def create_option_order(self, spot_price: float, option_type: str, signal_direction: str,
                            signal_strength: float, trend_line: float, adx_value: float,
                            market_data: Dict) -> Optional[Order]:
        """
        Create option order with real market data - ENHANCED VERSION
        """
        try:
            # Calculate optimal strike using the new method
            strike_price = await self.calculate_option_strike(spot_price, option_type)
        
            self.logger.info(f"OPTION SIGNAL: {signal_direction} - {option_type} Strategy")
            self.logger.info(f"   NIFTY Spot: Rs.{spot_price:.2f}")
            self.logger.info(f"   Trend Line: Rs.{trend_line:.2f} ({'+' if spot_price > trend_line else '-'}{abs(spot_price-trend_line):.2f})")
            self.logger.info(f"   Target Strike: {strike_price}{option_type}")
        
            # Fetch REAL option premium using the new method
            self.logger.info(f"Fetching real market price for {strike_price}{option_type}...")
            option_premium = await self.fetch_option_ltp(strike_price, option_type)
        
            if option_premium is None:
                self.logger.error(f"Could not fetch option premium for {strike_price}{option_type}")
                return None
        
            # Validate premium
            if not self.validate_option_premium(option_premium, strike_price, spot_price):
                self.logger.warning(f"Option premium Rs.{option_premium:.2f} failed validation")
                return None
        
            # Get detailed quote for bid-ask analysis
            detailed_quote = await self.get_option_quote_detailed(strike_price, option_type)
        
            if detailed_quote:
                spread = detailed_quote.get('spread', 0)
                bid = detailed_quote.get('bid', 0)
                ask = detailed_quote.get('ask', 0)
            
                self.logger.info(f"Option Quote: LTP=Rs.{option_premium:.2f}, Bid=Rs.{bid:.2f}, Ask=Rs.{ask:.2f}, Spread=Rs.{spread:.2f}")
            
                # Check liquidity (spread should be reasonable)
                if spread > option_premium * 0.1:  # Spread > 10% of premium
                    self.logger.warning(f"Wide spread ({spread:.2f}) for {strike_price}{option_type}")
        
            # Calculate position size
            lot_size = 75  # NIFTY lot size
            max_lots = int(self.risk_per_trade / (option_premium * lot_size))
            lots = max(1, min(max_lots, 3))  # 1-3 lots
        
            total_investment = option_premium * lot_size * lots

            self.logger.info(f"OPTION ORDER DETAILS:")
            self.logger.info(f"   Symbol: NIFTY {strike_price}{option_type}")
            self.logger.info(f"   Premium: Rs.{option_premium:.2f} per share")
            self.logger.info(f"   Quantity: {lots} lots ({lots * lot_size} shares)")
            self.logger.info(f"   Investment: Rs.{total_investment:,.2f}")
        
            # Create option order
            option_symbol = self.get_option_symbol(strike_price, option_type)
            instrument_key = await self.get_option_instrument_key(strike_price, option_type)
        
            order = Order(
                symbol=option_symbol,
                quantity=lots,
                price=option_premium,
                order_type=OrderType.MARKET,
                transaction_type=TransactionType.BUY,
                strategy_name=self.name,
                instrument_key=instrument_key
            )
        
            # Add option-specific details
            order.option_type = option_type
            order.strike_price = strike_price
            order.spot_price = spot_price
            order.signal_direction = signal_direction
            order.trend_line = trend_line
            order.adx_value = adx_value
            order.signal_strength = signal_strength
            order.total_investment = total_investment
            order.lot_size = lot_size
        
            # Add market data for tracking
            if detailed_quote:
                order.bid_price = detailed_quote.get('bid', 0)
                order.ask_price = detailed_quote.get('ask', 0)
                order.spread = detailed_quote.get('spread', 0)
                order.volume = detailed_quote.get('volume', 0)
                order.open_interest = detailed_quote.get('oi', 0)
        
            # Set trade state
            self.in_trade = True
        
            self.logger.info(f"OPTION ORDER CREATED: {option_symbol} @ Rs.{option_premium:.2f}")
        
            return order
        
        except Exception as e:
            self.logger.error(f"Error creating option order: {e}")
            return None
    
    async def create_spot_order(self, spot_price: float, direction: str, market_data: Dict) -> Optional[Order]:
        """Fallback spot trading if option trading is disabled"""
        try:
            lots = 1
            order = Order(
                symbol="NIFTY_SPOT",
                quantity=lots,
                price=spot_price,
                order_type=OrderType.MARKET,
                transaction_type=TransactionType.BUY,
                strategy_name=self.name,
                instrument_key=market_data.get('instrument_key', '')
            )
            
            self.in_trade = True
            return order
            
        except Exception as e:
            self.logger.error(f"Error creating spot order: {e}")
            return None
        
    async def monitor_option_prices(self):
        """
        ADVANCED FEATURE: Real-time Option Premium Monitoring
        
        Features:
        - Live premium tracking for all active positions
        - P&L calculation and alerts
        - Performance metrics
        - Risk monitoring
        """
        try:
            current_time = datetime.now()
    
            # Check if it's time to monitor (every 30 seconds by default)
            if (current_time - self.last_monitoring_time).total_seconds() < self.monitoring_interval:
                return
            
            # Only monitor during market hours
            if not self.is_market_open():
                return
            
            # Monitor each active option position
            if not self.active_option_positions:
                return
            
            self.logger.info(f"Monitoring {len(self.active_option_positions)} option positions...")
            
            for position_key, position_data in self.active_option_positions.items():
                try:
                    await self._monitor_single_position(position_data)
                    
                except Exception as e:
                    self.logger.error(f"Error monitoring position {position_key}: {e}")
            
            # Update monitoring statistics
            self.monitoring_updates += 1
            self.last_monitoring_time = current_time
            
            # Send periodic monitoring report (every 10 monitoring cycles ≈ 5 minutes)
            if self.monitoring_updates % 10 == 0:
                await self._send_monitoring_report()
                
        except Exception as e:
            self.logger.error(f"Error in option price monitoring: {e}")
    
    async def _monitor_single_position(self, position_data: Dict):
        """Monitor a single option position with detailed tracking"""
        try:
            strike = position_data['strike_price']
            option_type = position_data['option_type']
            entry_premium = position_data['entry_premium']
            quantity = position_data['quantity']
            entry_time = position_data['entry_time']
            symbol = position_data['symbol']
            
            # Fetch current premium
            current_premium = await self.fetch_option_ltp(strike, option_type)
            
            if current_premium is None:
                self.logger.warning(f"Could not fetch current premium for {symbol}")
                return
            
            # Calculate P&L metrics
            premium_change = current_premium - entry_premium
            premium_change_pct = (premium_change / entry_premium) * 100
            
            # Calculate position P&L
            lot_size = 75
            total_pnl = premium_change * quantity * lot_size
            total_investment = entry_premium * quantity * lot_size
            
            # Calculate time metrics
            time_held = datetime.now() - entry_time
            hours_held = time_held.total_seconds() / 3600
            
            # Update position data
            position_data.update({
                'current_premium': current_premium,
                'premium_change': premium_change,
                'premium_change_pct': premium_change_pct,
                'total_pnl': total_pnl,
                'hours_held': hours_held,
                'last_updated': datetime.now()
            })
            
            # Store in monitoring data
            self.position_monitoring_data[symbol] = position_data.copy()
            
            # Log detailed monitoring info
            self.logger.info(f"{symbol}: Rs.{current_premium:.2f} | "
                           f"P&L: Rs.{total_pnl:+,.2f} ({premium_change_pct:+.2f}%) | "
                           f"Time: {hours_held:.1f}h")
            
            # Check for alert conditions
            await self._check_monitoring_alerts(position_data)
            
            # Update global tracking
            self.total_premium_monitored += current_premium
            
        except Exception as e:
            self.logger.error(f"Error monitoring single position: {e}")
    
    async def _check_monitoring_alerts(self, position_data: Dict):
        """Check for alert conditions during monitoring"""
        try:
            premium_change_pct = position_data['premium_change_pct']
            symbol = position_data['symbol']
            total_pnl = position_data['total_pnl']
            
            # Profit milestone alerts
            if premium_change_pct >= 50 and not position_data.get('alert_50_sent'):
                await self._send_milestone_alert(symbol, "50% PROFIT!", total_pnl, premium_change_pct)
                position_data['alert_50_sent'] = True
                
            elif premium_change_pct >= 25 and not position_data.get('alert_25_sent'):
                await self._send_milestone_alert(symbol, "25% Profit", total_pnl, premium_change_pct)
                position_data['alert_25_sent'] = True
            
            # Loss warning alerts  
            elif premium_change_pct <= -20 and not position_data.get('alert_loss_20_sent'):
                await self._send_milestone_alert(symbol, "WARNING: 20% Loss", total_pnl, premium_change_pct)
                position_data['alert_loss_20_sent'] = True
                
        except Exception as e:
            self.logger.error(f"Error checking monitoring alerts: {e}")
    
    async def _send_milestone_alert(self, symbol: str, milestone: str, pnl: float, pct: float):
        """Send milestone alert via Telegram"""
        try:
            message = f"""Position Alert - {milestone}

Option: {symbol}
P&L: Rs.{pnl:+,.2f} ({pct:+.2f}%)
Time: {datetime.now().strftime('%I:%M:%S %p')}

{"Great performance!" if pnl > 0 else "Monitor closely"}"""
            
            # Send via notification system (if available)
            if hasattr(self, 'notifier') and self.notifier:
                await self.notifier.send_message(message)
            else:
                self.logger.info(f"Alert: {milestone} for {symbol}")
                
        except Exception as e:
            self.logger.error(f"Error sending milestone alert: {e}")
    
    async def _send_monitoring_report(self):
        """Send comprehensive monitoring report"""
        try:
            if not self.position_monitoring_data:
                return
            
            total_positions = len(self.position_monitoring_data)
            total_pnl = sum(pos['total_pnl'] for pos in self.position_monitoring_data.values())
            
            profitable_positions = len([pos for pos in self.position_monitoring_data.values() 
                                      if pos['total_pnl'] > 0])
            
            message = f"""Option Monitoring Report

Active Positions: {total_positions}
Total P&L: Rs.{total_pnl:+,.2f}
Profitable: {profitable_positions}/{total_positions}

Position Details:"""
            
            for symbol, data in self.position_monitoring_data.items():
                message += f"\n   • {symbol}: Rs.{data['total_pnl']:+,.2f} ({data['premium_change_pct']:+.1f}%)"
            
            message += f"\n\nMonitoring: Every {self.monitoring_interval}s"
            message += f"\nReport Time: {datetime.now().strftime('%I:%M %p')}"
            
            self.logger.info(f"Monitoring Report: {total_positions} positions, Rs.{total_pnl:+,.2f} P&L")
            
        except Exception as e:
            self.logger.error(f"Error sending monitoring report: {e}")
    
    # ==================== ENHANCED EXIT STRATEGY ====================
    
    async def should_exit_option(self, position, market_data: Dict) -> Optional[Order]:
        """Advanced option-specific exit strategies"""
        try:
            # Get position data for enhanced tracking
            symbol = position.symbol
            position_data = self.active_option_positions.get(symbol)
            
            if not position_data:
                # No position data - can't do advanced exits
                return None
            
            # Fetch current option premium
            current_premium = await self.fetch_option_ltp(
                position_data['strike_price'], 
                position_data['option_type']
            )
            
            if current_premium is None:
                self.logger.warning(f"Could not fetch current premium for {symbol}")
                return None
            
            # Calculate current P&L
            entry_premium = position_data['entry_premium']
            premium_change_pct = ((current_premium - entry_premium) / entry_premium) * 100
            
            # Update position data
            position_data['current_premium'] = current_premium
            position_data['premium_change_pct'] = premium_change_pct
            
            # === ADVANCED EXIT CONDITIONS ===
            
            # 1. PROFIT TARGET EXIT (50% by default)
            if premium_change_pct >= self.profit_target_pct:
                self.logger.info(f"PROFIT TARGET HIT: {premium_change_pct:.2f}% >= {self.profit_target_pct}%")
                return self._create_option_exit_order(position, current_premium, 
                                                    f"PROFIT_TARGET_{self.profit_target_pct}%")
            
            # 2. STOP LOSS EXIT (30% by default)
            if premium_change_pct <= -self.stop_loss_pct:
                self.logger.info(f"STOP LOSS HIT: {premium_change_pct:.2f}% <= -{self.stop_loss_pct}%")
                return self._create_option_exit_order(position, current_premium, 
                                                    f"STOP_LOSS_{self.stop_loss_pct}%")
            
            # 3. TRAILING STOP EXIT
            if self.trailing_stop_enabled:
                trailing_exit = await self._check_trailing_stop(position_data, current_premium, position)
                if trailing_exit:
                    return trailing_exit
            
            # 4. TIME-BASED EXIT
            time_exit = await self._check_time_based_exit(position_data, current_premium, position)
            if time_exit:
                return time_exit
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in should_exit_option: {e}")
            return None
    
    async def _check_trailing_stop(self, position_data: Dict, current_premium: float, position) -> Optional[Order]:
        """Check trailing stop conditions"""
        try:
            premium_change_pct = position_data['premium_change_pct']
            symbol = position_data['symbol']
            
            # Only activate trailing stop after reaching activation threshold
            if premium_change_pct < self.trail_activation_pct:
                return None
            
            # Get or initialize trailing stop level
            if 'trailing_stop_level' not in position_data:
                # Initialize trailing stop at current profit minus trail step
                position_data['trailing_stop_level'] = premium_change_pct - self.trail_step_pct
                position_data['highest_profit_pct'] = premium_change_pct
                self.logger.info(f"TRAILING STOP ACTIVATED at {position_data['trailing_stop_level']:.1f}%")
                return None
            
            # Update trailing stop if profit increased
            if premium_change_pct > position_data['highest_profit_pct']:
                old_level = position_data['trailing_stop_level']
                position_data['highest_profit_pct'] = premium_change_pct
                position_data['trailing_stop_level'] = premium_change_pct - self.trail_step_pct
                self.logger.info(f"TRAILING STOP UPDATED: {old_level:.1f}% -> {position_data['trailing_stop_level']:.1f}%")
            
            # Check if trailing stop hit
            if premium_change_pct <= position_data['trailing_stop_level']:
                self.logger.info(f"TRAILING STOP HIT: {premium_change_pct:.2f}% <= {position_data['trailing_stop_level']:.1f}%")
                return self._create_option_exit_order(position, current_premium, 
                                                    f"TRAILING_STOP_{position_data['trailing_stop_level']:.1f}%")
                
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking trailing stop: {e}")
            return None
    
    async def _check_time_based_exit(self, position_data: Dict, current_premium: float, position) -> Optional[Order]:
        """Check time-based exit conditions"""
        try:
            entry_time = position_data['entry_time']
            current_time = datetime.now()
            hours_held = (current_time - entry_time).total_seconds() / 3600
            
            # Exit if held for more than 4 hours without significant profit
            if hours_held >= 4 and position_data['premium_change_pct'] < 10:
                self.logger.info(f"TIME EXIT: {hours_held:.1f}h with {position_data['premium_change_pct']:.1f}% profit")
                return self._create_option_exit_order(position, current_premium, "TIME_BASED_4H")
            
            # Exit if held for more than 6 hours regardless of P&L
            if hours_held >= 6:
                self.logger.info(f"MAX TIME EXIT: {hours_held:.1f}h - force exit")
                return self._create_option_exit_order(position, current_premium, "MAX_TIME_6H")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking time-based exit: {e}")
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
                        'premium_change_pct': 0,
                        'current_premium': order.price
                    }
                    
                    self.logger.info(f"Added {order.symbol} to advanced monitoring")
                    
            elif order.transaction_type == TransactionType.SELL:
                # Position already removed in _create_option_exit_order
                self.logger.info(f"Removed {order.symbol} from monitoring")
                
        except Exception as e:
            self.logger.error(f"Error in enhanced order fill handling: {e}")
    
    async def _check_greeks_based_exit(self, position_data: Dict, current_premium: float, market_data: Dict) -> Optional[Order]:
        """Check Greeks-based exit conditions (advanced)"""
        try:
            # Check if it's close to market close (theta decay accelerates)
            current_time = datetime.now()
            market_close = current_time.replace(hour=15, minute=20)  # 3:20 PM auto square-off
            minutes_to_close = (market_close - current_time).total_seconds() / 60
            
            # Force exit if less than 10 minutes to close
            if minutes_to_close <= 10 and minutes_to_close > 0:
                self.logger.info(f"MARKET CLOSE EXIT: {minutes_to_close:.0f} minutes to auto square-off")
                return self._create_option_exit_order(
                    self._get_position_from_data(position_data), 
                    current_premium, 
                    "MARKET_CLOSE_10MIN"
                )
            
            # Exit if premium dropped below minimum viable level
            if current_premium < 5:  # Below Rs.5 per share
                self.logger.info(f"MINIMUM PREMIUM EXIT: Rs.{current_premium:.2f} < Rs.5")
                return self._create_option_exit_order(
                    self._get_position_from_data(position_data), 
                    current_premium, 
                    "MINIMUM_PREMIUM"
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking Greeks-based exit: {e}")
            return None
    
    async def _check_volatility_exit(self, position_data: Dict, current_premium: float, market_data: Dict) -> Optional[Order]:
        """Check volatility-based exit conditions"""
        try:
            # Get NIFTY spot price movement
            if 'ha_candle' in market_data:
                current_spot = market_data['ha_candle'].get('ha_close', 0)
                
                # Check if NIFTY moved significantly against our position
                option_type = position_data['option_type']
                strike_price = position_data['strike_price']
                
                if option_type == 'CE':
                    # For CE, exit if NIFTY moved significantly below strike
                    if current_spot < strike_price - 100:  # 100 points below strike
                        self.logger.info(f"VOLATILITY EXIT (CE): NIFTY {current_spot:.2f} too far below strike {strike_price}")
                        return self._create_option_exit_order(
                            self._get_position_from_data(position_data), 
                            current_premium, 
                            "VOLATILITY_ADVERSE_MOVE"
                        )
                        
                elif option_type == 'PE':
                    # For PE, exit if NIFTY moved significantly above strike
                    if current_spot > strike_price + 100:  # 100 points above strike
                        self.logger.info(f"VOLATILITY EXIT (PE): NIFTY {current_spot:.2f} too far above strike {strike_price}")
                        return self._create_option_exit_order(
                            self._get_position_from_data(position_data), 
                            current_premium, 
                            "VOLATILITY_ADVERSE_MOVE"
                        )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking volatility exit: {e}")
            return None
    
    def _create_option_exit_order(self, position, current_premium: float, exit_reason: str) -> Order:
        """Create enhanced option exit order"""
        try:
            order = Order(
                symbol=position.symbol,
                quantity=position.quantity,
                price=current_premium,
                order_type=OrderType.MARKET,
                transaction_type=TransactionType.SELL,
                strategy_name=self.name,
                instrument_key=position.instrument_key
            )
            
            # Add enhanced exit details
            order.exit_reason = exit_reason
            order.current_premium = current_premium
            order.exit_time = datetime.now()
            
            self.logger.info(f"ADVANCED EXIT: {exit_reason} - {position.symbol} @ Rs.{current_premium:.2f}")
            
            # Calculate P&L for the order
            if hasattr(position, 'average_price'):
                pnl_per_share = current_premium - position.average_price
                total_pnl = pnl_per_share * position.quantity * 75
                order.total_pnl = total_pnl
                order.pnl_pct = (pnl_per_share / position.average_price) * 100
            
            return order
            
        except Exception as e:
            self.logger.error(f"Error creating option exit order: {e}")
            return None
    
    def _get_position_from_data(self, position_data: Dict):
        """Convert position data to Position object for exit order creation"""
        class MockPosition:
            def __init__(self, data):
                self.symbol = data['symbol']
                self.quantity = data['quantity']
                self.average_price = data['entry_premium']
                self.instrument_key = data.get('instrument_key', '')
        
        return MockPosition(position_data)
    
    def is_market_open(self) -> bool:
        """Check if market is open for monitoring"""
        current_time = datetime.now()
        market_open = current_time.replace(hour=9, minute=15)
        market_close = current_time.replace(hour=15, minute=30)
        
        # Check if it's a weekday
        if current_time.weekday() >= 5:  # Saturday or Sunday
            return False
        
        return market_open <= current_time <= market_close