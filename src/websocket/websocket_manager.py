# ==================== src/websocket/websocket_manager.py (COMPLETE FIXED VERSION) ====================
import logging
import asyncio
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Callable, Optional
import pandas as pd
import numpy as np
from collections import defaultdict, deque
import json
import threading
import pytz



try:
    import upstox_client
    from upstox_client.rest import ApiException
    UPSTOX_SDK_AVAILABLE = True
except ImportError:
    UPSTOX_SDK_AVAILABLE = False
    

class MarketHoursChecker:
    """Check if Indian stock market is open"""
    
    def __init__(self):
        self.ist_timezone = pytz.timezone('Asia/Kolkata')
        self.market_open_time = time(9, 15)  # 9:15 AM
        self.market_close_time = time(15, 30)  # 3:30 PM
    
    def is_market_open(self):
        """Check if market is currently open"""
        current_time = datetime.now(self.ist_timezone)
        current_time_only = current_time.time()
        current_day = current_time.weekday()
        
        # Check if it's a weekday (Monday=0, Sunday=6)
        if current_day >= 5:  # Saturday or Sunday
            return False
        
        # Check if within trading hours
        return self.market_open_time <= current_time_only <= self.market_close_time
    
    def get_market_status(self):
        """Get detailed market status"""
        current_time = datetime.now(self.ist_timezone)
        
        if self.is_market_open():
            return {
                'status': 'OPEN',
                'message': 'Market is open for trading',
                'current_time': current_time.strftime('%H:%M:%S')
            }
        else:
            return {
                'status': 'CLOSED', 
                'message': 'Market is closed',
                'current_time': current_time.strftime('%H:%M:%S'),
                'next_open': 'Tomorrow at 9:15 AM IST'
            }

class CandleAggregator:
    """Aggregates tick data into candles of different timeframes"""
    
    def __init__(self, timeframe_minutes: int = 1):
        self.timeframe_minutes = timeframe_minutes
        self.timeframe_seconds = timeframe_minutes * 60
        self.current_candles: Dict[str, Dict] = {}
        self.completed_candles: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.logger = logging.getLogger(__name__)
        
    def process_tick(self, symbol: str, tick_data: Dict) -> Optional[Dict]:
        """Process a tick and return completed candle if any"""
        try:
            price = float(tick_data.get('ltp', 0))
            volume = int(tick_data.get('volume', 0))
            timestamp = datetime.now()
            
            if price <= 0:
                return None
            
            # Calculate candle start time
            candle_start = self._get_candle_start_time(timestamp)
            candle_key = f"{symbol}_{candle_start.strftime('%Y%m%d_%H%M%S')}"
            
            # Initialize or update current candle
            if symbol not in self.current_candles:
                self.current_candles[symbol] = {
                    'symbol': symbol,
                    'open': price,
                    'high': price,
                    'low': price,
                    'close': price,
                    'volume': volume,
                    'start_time': candle_start,
                    'end_time': candle_start + timedelta(seconds=self.timeframe_seconds),
                    'tick_count': 1
                }
            else:
                current_candle = self.current_candles[symbol]
                
                # Check if we need to close current candle and start new one
                if timestamp >= current_candle['end_time']:
                    # Complete the current candle
                    completed_candle = current_candle.copy()
                    self.completed_candles[symbol].append(completed_candle)
                    
                    # Start new candle
                    self.current_candles[symbol] = {
                        'symbol': symbol,
                        'open': price,
                        'high': price,
                        'low': price,
                        'close': price,
                        'volume': volume,
                        'start_time': candle_start,
                        'end_time': candle_start + timedelta(seconds=self.timeframe_seconds),
                        'tick_count': 1
                    }
                    
                    self.logger.debug(f"Completed {self.timeframe_minutes}min candle for {symbol}: O:{completed_candle['open']:.2f} H:{completed_candle['high']:.2f} L:{completed_candle['low']:.2f} C:{completed_candle['close']:.2f}")
                    return completed_candle
                else:
                    # Update current candle
                    current_candle['high'] = max(current_candle['high'], price)
                    current_candle['low'] = min(current_candle['low'], price)
                    current_candle['close'] = price
                    current_candle['volume'] = volume
                    current_candle['tick_count'] += 1
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error processing tick for {symbol}: {e}")
            return None
    
    def _get_candle_start_time(self, timestamp: datetime) -> datetime:
        """Calculate the start time of the candle for given timestamp"""
        # Round down to nearest timeframe boundary
        minutes = (timestamp.minute // self.timeframe_minutes) * self.timeframe_minutes
        return timestamp.replace(minute=minutes, second=0, microsecond=0)
    
    def get_latest_candles(self, symbol: str, count: int = 10) -> List[Dict]:
        """Get latest completed candles for a symbol"""
        if symbol in self.completed_candles:
            return list(self.completed_candles[symbol])[-count:]
        return []
    
    def get_current_candle(self, symbol: str) -> Optional[Dict]:
        """Get current incomplete candle for a symbol"""
        return self.current_candles.get(symbol)

class HeikinAshiConverter:
    """Converts regular candles to Heikin Ashi candles"""
    
    def __init__(self):
        self.ha_candles: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.logger = logging.getLogger(__name__)
    
    def convert_candle(self, symbol: str, candle: Dict) -> Dict:
        """Convert a regular candle to Heikin Ashi"""
        try:
            open_price = float(candle['open'])
            high_price = float(candle['high'])
            low_price = float(candle['low'])
            close_price = float(candle['close'])
            
            # Get previous HA candle
            prev_ha = None
            if symbol in self.ha_candles and len(self.ha_candles[symbol]) > 0:
                prev_ha = self.ha_candles[symbol][-1]
            
            # Calculate Heikin Ashi values
            if prev_ha is None:
                # First candle
                ha_close = (open_price + high_price + low_price + close_price) / 4
                ha_open = (open_price + close_price) / 2
            else:
                ha_close = (open_price + high_price + low_price + close_price) / 4
                ha_open = (prev_ha['ha_open'] + prev_ha['ha_close']) / 2
            
            ha_high = max(high_price, ha_open, ha_close)
            ha_low = min(low_price, ha_open, ha_close)
            
            ha_candle = {
                'symbol': symbol,
                'timestamp': candle.get('start_time', datetime.now()),
                'ha_open': ha_open,
                'ha_high': ha_high,
                'ha_low': ha_low,
                'ha_close': ha_close,
                'volume': candle.get('volume', 0),
                'original_open': open_price,
                'original_high': high_price,
                'original_low': low_price,
                'original_close': close_price
            }
            
            # Store the HA candle
            self.ha_candles[symbol].append(ha_candle)
            
            self.logger.debug(f"HA Candle for {symbol}: O:{ha_open:.2f} H:{ha_high:.2f} L:{ha_low:.2f} C:{ha_close:.2f}")
            return ha_candle
            
        except Exception as e:
            self.logger.error(f"Error converting to Heikin Ashi for {symbol}: {e}")
            return candle
    
    def get_latest_ha_candles(self, symbol: str, count: int = 10) -> List[Dict]:
        """Get latest Heikin Ashi candles for a symbol"""
        if symbol in self.ha_candles:
            return list(self.ha_candles[symbol])[-count:]
        return []

class WebSocketManager:
    """Enhanced WebSocket Manager with persistent candle storage"""
    
    def __init__(self, api_key: str, access_token: str):
        self.api_key = api_key
        self.access_token = access_token
        self.logger = logging.getLogger(__name__)
        self.market_checker = MarketHoursChecker()
        self.last_market_status_check = datetime.now()
        
        
        # Check if Upstox SDK is available
        if not UPSTOX_SDK_AVAILABLE:
            raise ImportError("upstox-python-sdk is required for websocket functionality. Install with: pip install upstox-python-sdk")
        
        # Initialize components
        self.candle_aggregator = CandleAggregator(timeframe_minutes=1)
        self.ha_converter = HeikinAshiConverter()
        
        # WebSocket connections
        self.market_streamer = None
        self.portfolio_streamer = None
        
        # Callbacks
        self.on_tick_callback: Optional[Callable] = None
        self.on_candle_callback: Optional[Callable] = None
        self.on_ha_candle_callback: Optional[Callable] = None
        self.on_order_update_callback: Optional[Callable] = None
        self.on_error_callback: Optional[Callable] = None
        
        # Subscribed instruments
        self.subscribed_instruments: List[str] = []
        
        # Connection state
        self.is_connected = False
        self.last_data_received = datetime.now()
        self.connection_attempts = 0
        self.max_reconnection_attempts = 5
        
        # Keep existing storage for backward compatibility
        self.latest_candles: Dict[str, List[Dict]] = {}
        self.latest_ha_candles: Dict[str, List[Dict]] = {}
        
         # PERSISTENT CANDLE STORAGE - MOVED HERE TO PREVENT RESET
        self.persistent_candles: Dict[str, List[Dict]] = {}
        self.persistent_ha_candles: Dict[str, List[Dict]] = {}
        self.latest_ticks: Dict[str, Dict] = {}
        
        # Data storage
        self.latest_candles: Dict[str, List[Dict]] = {}
        self.latest_ha_candles: Dict[str, List[Dict]] = {}
        self.latest_ticks: Dict[str, Dict] = {}  # Store latest ticks for monitoring
        
    def set_callbacks(self, on_tick=None, on_candle=None, on_ha_candle=None, 
                     on_order_update=None, on_error=None):
        """Set callback functions for different events"""
        self.on_tick_callback = on_tick
        self.on_candle_callback = on_candle
        self.on_ha_candle_callback = on_ha_candle
        self.on_order_update_callback = on_order_update
        self.on_error_callback = on_error
        
        self.logger.info("WebSocket callbacks configured")
    
    def setup_for_nifty_only(self):
        """Configure websocket for NIFTY only"""
        # Subscribe only to NIFTY
        self.subscribed_instruments = ['NSE_INDEX|Nifty 50']
        self.logger.info("WebSocket configured for NIFTY only")
    
    def subscribe_instruments(self, instruments: List[str]):
        """Subscribe to instrument data"""
        self.subscribed_instruments = instruments
        self.logger.info(f"Subscribed to instruments: {instruments}")

    def start_market_stream(self):
        """Start market data websocket stream"""
        try:
            if not self.subscribed_instruments:
                self.logger.warning("No instruments subscribed for market data")
                return
            
            # Configure Upstox client
            configuration = upstox_client.Configuration()
            configuration.access_token = self.access_token
            
            # Initialize market data streamer
            self.market_streamer = upstox_client.MarketDataStreamerV3(
                upstox_client.ApiClient(configuration),
                self.subscribed_instruments,
                "full"  # Full market data
            )
            
            # Set up event handlers
            self.market_streamer.on("open", self._on_market_open)
            self.market_streamer.on("message", self._on_market_message)
            self.market_streamer.on("error", self._on_market_error)
            self.market_streamer.on("close", self._on_market_close)
            
            # Enable auto-reconnect
            self.market_streamer.auto_reconnect(True, 10, 3)
            
            # Connect
            self.market_streamer.connect()
            self.logger.info("Market data websocket connection initiated")
            
        except Exception as e:
            self.logger.error(f"Failed to start market stream: {e}")
    
    def start_portfolio_stream(self):
        """Start portfolio/order updates websocket stream"""
        try:
            # Configure Upstox client
            configuration = upstox_client.Configuration()
            configuration.access_token = self.access_token
            
            # Initialize portfolio data streamer
            self.portfolio_streamer = upstox_client.PortfolioDataStreamer(
                upstox_client.ApiClient(configuration)
            )
            
            # Set up event handlers
            self.portfolio_streamer.on("open", self._on_portfolio_open)
            self.portfolio_streamer.on("message", self._on_portfolio_message)
            self.portfolio_streamer.on("error", self._on_portfolio_error)
            self.portfolio_streamer.on("close", self._on_portfolio_close)
            
            # Enable auto-reconnect
            self.portfolio_streamer.auto_reconnect(True, 10, 3)
            
            # Connect
            self.portfolio_streamer.connect()
            self.logger.info("Portfolio data websocket connection initiated")
            
        except Exception as e:
            self.logger.error(f"Failed to start portfolio stream: {e}")
    
    def start_all_streams(self):
        """Start all WebSocket streams with enhanced error handling"""
        try:
            self.logger.info("Starting WebSocket streams...")
            self.start_market_stream()
            self.start_portfolio_stream()
            self.is_connected = True
            self.logger.info("WebSocket streams started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start WebSocket streams: {e}")
            if self.on_error_callback:
                asyncio.create_task(self.on_error_callback(f"Failed to start streams: {str(e)}"))
    
    def stop_all_streams(self):
        """Stop all WebSocket streams"""
        try:
            self.logger.info("Stopping WebSocket streams...")
            
            if self.market_streamer:
                try:
                    self.market_streamer.disconnect()
                except Exception as e:
                    self.logger.warning(f"Error stopping market streamer: {e}")
                finally:
                    self.market_streamer = None
                
            if self.portfolio_streamer:
                try:
                    self.portfolio_streamer.disconnect()
                except Exception as e:
                    self.logger.warning(f"Error stopping portfolio streamer: {e}")
                finally:
                    self.portfolio_streamer = None
                        
                self.is_connected = False
                self.logger.info("WebSocket streams stopped")
                
        except Exception as e:
            self.logger.error(f"Error stopping WebSocket streams: {e}")
    
    # Market Data Event Handlers
    def _on_market_open(self):
        """Called when market websocket connection opens"""
        self.logger.info("Websocket connected")
        self.logger.info("Market data websocket connected")
    
    def _on_market_message(self, message):
        """Process incoming market data with MARKET HOURS CHECK"""
        try:
            # 🚨 CRITICAL FIX: CHECK MARKET HOURS FIRST 🚨
            current_time = datetime.now()   
            market_close_time = current_time.replace(hour=15, minute=30, second=0)
            
            # Check market status every 60 seconds to avoid spam
            if (current_time - self.last_market_status_check).total_seconds() > 60:
                market_status = self.market_checker.get_market_status()
                
                if current_time > market_close_time:
                    self.logger.info(f"MARKET CLOSED at {market_status['current_time']} - Ignoring all data feeds")
                    self.logger.info(f"Market will open at 9:15 AM IST tomorrow")
                    return  # EXIT EARLY - DON'T PROCESS ANY DATA
                else:
                    self.logger.debug(f"Market OPEN at {market_status['current_time']} - Processing data")
                
                self.last_market_status_check = current_time
            
            # Only proceed with data processing if market is open
            if not self.market_checker.is_market_open():
                return  # EXIT EARLY
            
            # Continue with existing message processing
            self.last_data_received = datetime.now()
            
            # Parse market data message  
            if isinstance(message, dict):
                feeds = message.get('feeds', {})
            elif isinstance(message, str):
                try:
                    message = json.loads(message)
                    feeds = message.get('feeds', {})
                except json.JSONDecodeError:
                    return
            else:
                return
                
            if feeds:
                for instrument_key, data in feeds.items():
                    # Extract LTPC data from nested structure
                    ltpc_data = None
                    
                    # Method 1: Try direct ltpc access (for regular ticks)
                    if 'ltpc' in data:
                        ltpc_data = data['ltpc']
                    
                    # Method 2: Try nested structure (for full feed)
                    elif 'fullFeed' in data:
                        full_feed = data['fullFeed']
                        if 'indexFF' in full_feed and 'ltpc' in full_feed['indexFF']:
                            ltpc_data = full_feed['indexFF']['ltpc']
                    
                    # Process the LTPC data correctly
                    if ltpc_data and 'ltp' in ltpc_data:
                        # Extract price data
                        current_price = float(ltpc_data.get('ltp', 0))
                        volume = ltpc_data.get('vol', 0)
                        
                        # Get symbol name
                        symbol = self._get_symbol_from_key(instrument_key)
                        
                        # Create tick data
                        tick_data = {
                            'instrument_key': instrument_key,
                            'ltp': current_price,
                            'volume': volume,
                            'timestamp': datetime.now(),
                            'symbol': symbol
                        }
                        
                        # Store latest tick for monitoring
                        self.latest_ticks[symbol] = tick_data
                        
                        # PROCESS CANDLE AGGREGATION (only during market hours)
                        completed_candle = self.candle_aggregator.process_tick(symbol, tick_data)
                        
                        if completed_candle:
                            self.logger.info(f"NEW CANDLE - {symbol}: O:{completed_candle['open']:.2f} H:{completed_candle['high']:.2f} L:{completed_candle['low']:.2f} C:{completed_candle['close']:.2f}")
                            
                            # Store in PERSISTENT storage
                            if symbol not in self.persistent_candles:
                                self.persistent_candles[symbol] = []
                            self.persistent_candles[symbol].append(completed_candle)
                            
                            # Keep only last 100 candles
                            if len(self.persistent_candles[symbol]) > 100:
                                self.persistent_candles[symbol] = self.persistent_candles[symbol][-100:]
                            
                            # Also update latest_candles for compatibility
                            self.latest_candles[symbol] = self.persistent_candles[symbol].copy()
                            
                            # CONVERT TO HEIKIN ASHI
                            ha_candle = self.ha_converter.convert_candle(symbol, completed_candle)
                            
                            self.logger.info(f"HA CANDLE - {symbol}: O:{ha_candle['ha_open']:.2f} H:{ha_candle['ha_high']:.2f} L:{ha_candle['ha_low']:.2f} C:{ha_candle['ha_close']:.2f}")
                            
                            # Store in PERSISTENT HA storage
                            if symbol not in self.persistent_ha_candles:
                                self.persistent_ha_candles[symbol] = []
                            self.persistent_ha_candles[symbol].append(ha_candle)
                            
                            # Keep only last 100 HA candles
                            if len(self.persistent_ha_candles[symbol]) > 100:
                                self.persistent_ha_candles[symbol] = self.persistent_ha_candles[symbol][-100:]
                            
                            # Also update latest_ha_candles for compatibility
                            self.latest_ha_candles[symbol] = self.persistent_ha_candles[symbol].copy()
                            
                            # SHOW CANDLE COUNT PROGRESS
                            candle_count = len(self.persistent_ha_candles[symbol])
                            if candle_count < 15:
                                self.logger.info(f"Building data for {symbol}: {candle_count}/15 HA candles collected")
                            elif candle_count == 15:
                                self.logger.info(f"READY! {symbol} has enough data (15 candles) - Strategy can now analyze!")
                            
                            # TRIGGER STRATEGY EXECUTION (this will be fixed in Step 4)
                            if self.on_ha_candle_callback and candle_count >= 15:
                                # Add candle history to the HA candle
                                ha_candle['candle_history'] = self.persistent_ha_candles[symbol].copy()
                                ha_candle['symbol'] = symbol
                                
                                # Schedule callback (will be improved in Step 4)
                                try:
                                    import asyncio
                                    try:
                                        loop = asyncio.get_running_loop()
                                        # Schedule the callback
                                        task = loop.create_task(self.on_ha_candle_callback(ha_candle))
                                        self.logger.info(f"STRATEGY CALLBACK SCHEDULED for {symbol}")
                                    except RuntimeError:
                                        # No event loop - store for manual processing
                                        self.logger.info(f"No event loop - storing callback for {symbol}")
                                        if not hasattr(self, 'pending_callbacks'):
                                            self.pending_callbacks = []
                                        self.pending_callbacks.append((symbol, ha_candle))
            
                                except Exception as callback_error:
                                        self.logger.error(f"Callback error: {callback_error}")

                    
        except Exception as e:
            self.logger.error(f"Error processing market message: {e}")
                            

    def _safe_async_call(self, callback, data):
        """Safely call async function"""
        try:
            import asyncio
            asyncio.create_task(callback(data))
        except Exception as e:
            self.logger.debug(f"Error in async callback: {e}")
        
    def is_ready_for_trading(self) -> bool:
        """Check if WebSocket is ready for trading"""
        try:
            # Check if connected
            if not self.is_connected:
                return False
            
            # Check if we have recent data (within last 60 seconds)
            if hasattr(self, 'last_data_received'):
                data_age = (datetime.now() - self.last_data_received).total_seconds()
                if data_age > 60:  # More than 1 minute old
                    self.logger.warning(f"Data is {data_age:.0f} seconds old - not ready for trading")
                    return False
            else:
                # No data received yet
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking trading readiness: {e}")
            return False
    
    def _on_market_error(self, error):
        """Called when market websocket encounters an error"""
        self.logger.error(f"Market websocket error: {error}")
    
    def _on_market_close(self, code=None, reason=None):
        """Called when market websocket connection closes"""
        self.logger.warning(f"Market data websocket connection closed - Code: {code}, Reason: {reason}")
    
    # Portfolio Data Event Handlers
    def _on_portfolio_open(self):
        """Called when portfolio websocket connection opens"""
        self.logger.info("Websocket connected")
        self.logger.info("Portfolio data websocket connected")
    
    def _on_portfolio_message(self, message):
        """Process incoming portfolio/order updates"""
        try:
            if self.on_order_update_callback:
                asyncio.create_task(self.on_order_update_callback(message))
        except Exception as e:
            self.logger.error(f"Error processing portfolio message: {e}")
    
    def _on_portfolio_error(self, error):
        """Called when portfolio websocket encounters an error"""
        self.logger.error(f"Portfolio websocket error: {error}")
    
    def _on_portfolio_close(self, code=None, reason=None):
        """Called when portfolio websocket connection closes"""  
        self.logger.warning(f"Portfolio data websocket connection closed - Code: {code}, Reason: {reason}")
    
    def _get_symbol_from_key(self, instrument_key: str) -> str:
        """Convert instrument key to symbol name - ENHANCED VERSION"""
        # Enhanced mapping for your subscribed instruments
        key_to_symbol = {
            'NSE_INDEX|Nifty 50': 'NIFTY',
            'NSE_INDEX|Nifty Bank': 'BANKNIFTY',
            'BSE_INDEX|SENSEX': 'SENSEX',
            'NSE_INDEX|SENSEX': 'SENSEX'  # Alternative mapping
        }
        
        # Log for debugging during market hours
        self.logger.debug(f"Mapping instrument key: {instrument_key}")
        
        # Return mapped symbol or fallback
        mapped_symbol = key_to_symbol.get(instrument_key)
        if mapped_symbol:
            return mapped_symbol
        
        # Fallback logic
        parts = instrument_key.split('|')
        if len(parts) > 1:
            return parts[1].replace(' ', '_').upper()  # Convert "Nifty 50" to "NIFTY_50"
        return instrument_key
    
    def get_latest_candles(self, symbol: str, count: int = 50) -> List[Dict]:
        """Get latest candles from persistent storage"""
        if symbol in self.persistent_candles:
            return self.persistent_candles[symbol][-count:]
        return []

    
    def get_latest_ha_candles(self, symbol: str, count: int = 50) -> List[Dict]:
        """Get latest Heikin Ashi candles from persistent storage"""
        if symbol in self.persistent_ha_candles:
            return self.persistent_ha_candles[symbol][-count:]
        return []
    
    def get_connection_status(self) -> Dict:
        """Get current connection status"""
        return {
            'is_connected': self.is_connected,
            'last_data_received': self.last_data_received,
            'connection_attempts': self.connection_attempts,
            'subscribed_instruments': getattr(self, 'subscribed_instruments', []),
            'latest_ticks': self.latest_ticks
        }
    
    def get_current_candle(self, symbol: str) -> Optional[Dict]:
        """Get current incomplete candle for a symbol"""
        return self.candle_aggregator.get_current_candle(symbol)
    
    def get_current_ha_candles(self, symbol: str, count: int = 15) -> List[Dict]:
        """Get latest HA candles for strategy analysis - uses persistent storage"""
        if symbol in self.persistent_ha_candles:
            return self.persistent_ha_candles[symbol][-count:]
        return []
    
    def restore_candle_history(self, symbol: str, candles: List[Dict], ha_candles: List[Dict]):
        """Restore candle history after reconnection"""
        if candles:
            self.persistent_candles[symbol] = candles
            self.latest_candles[symbol] = candles.copy()
            
        if ha_candles:
            self.persistent_ha_candles[symbol] = ha_candles
            self.latest_ha_candles[symbol] = ha_candles.copy()
            
        self.logger.info(f"Restored {len(ha_candles)} HA candles for {symbol}")

    # Also update the HeikinAshiConverter to handle persistent storage
    def _restore_ha_converter_state(self):
        """Restore HA converter state after reconnection"""
        for symbol, ha_candles in self.persistent_ha_candles.items():
            if ha_candles and hasattr(self.ha_converter, 'ha_candles'):
                # Restore the last few candles to maintain HA calculation continuity
                self.ha_converter.ha_candles[symbol] = deque(ha_candles[-5:], maxlen=100)