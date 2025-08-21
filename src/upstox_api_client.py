# ==================== src/upstox_client.py (COMPLETELY FIXED) ====================
import requests
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
import asyncio
import aiohttp
from pathlib import Path

class UpstoxClient:
    """Upstox API client with token persistence"""
    
    def __init__(self, api_key: str, api_secret: str, redirect_uri: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.redirect_uri = redirect_uri
        self.access_token = None
        self.base_url = "https://api.upstox.com/v2"
        self.logger = logging.getLogger(__name__)
        
        # Token storage
        self.token_file = Path("data") / "access_token.json"
        self.load_stored_token()
        
        # Headers for API requests
        self.headers = {
            'Authorization': f'Bearer {self.access_token}' if self.access_token else '',
            'Accept': 'application/json'
        }
        
    def save_token(self, token_data: dict):
        """Save access token to file"""
        try:
            # Create data directory if it doesn't exist
            self.token_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Add timestamp
            token_data['saved_at'] = datetime.now().isoformat()
            
            with open(self.token_file, 'w') as f:
                json.dump(token_data, f, indent=2)
                
            self.logger.info("Access token saved successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to save token: {e}")
    
    def load_stored_token(self):
        """Load stored access token"""
        try:
            if self.token_file.exists():
                with open(self.token_file, 'r') as f:
                    token_data = json.load(f)
                    
                self.access_token = token_data.get('access_token')
                
                if self.access_token:
                    saved_at = token_data.get('saved_at')
                    self.logger.info(f"Loaded stored access token from {saved_at}")
                    # Update headers with token
                    self.headers['Authorization'] = f'Bearer {self.access_token}'
                    return True
                    
        except Exception as e:
            self.logger.error(f"Failed to load stored token: {e}")
            
        return False
    
    def get_login_url(self) -> str:
        """Generate login URL for authorization"""
        auth_url = "https://api.upstox.com/v2/login/authorization/dialog"
        params = {
            'response_type': 'code',
            'client_id': self.api_key,
            'redirect_uri': self.redirect_uri
        }
        
        url = f"{auth_url}?response_type={params['response_type']}&client_id={params['client_id']}&redirect_uri={params['redirect_uri']}"
        return url
    
    async def get_access_token(self, auth_code: str) -> bool:
        """Get access token using authorization code"""
        url = f"{self.base_url}/login/authorization/token"
        
        data = {
            'code': auth_code,
            'client_id': self.api_key,
            'client_secret': self.api_secret,
            'redirect_uri': self.redirect_uri,
            'grant_type': 'authorization_code'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data) as response:
                    response.raise_for_status()
                    token_response = await response.json()
                    
                    # Handle both response formats
                    if isinstance(token_response, dict):
                        # Direct response format (what you're getting)
                        if 'access_token' in token_response:
                            self.access_token = token_response.get('access_token')
                            
                            if self.access_token:
                                # Update headers
                                self.headers['Authorization'] = f'Bearer {self.access_token}'
                                # Save token for future use
                                self.save_token(token_response)
                                self.logger.info("Access token obtained and saved successfully")
                                return True
                        
                        # Wrapped response format
                        elif token_response.get('status') == 'success':
                            token_data = token_response.get('data', {})
                            self.access_token = token_data.get('access_token')
                            
                            if self.access_token:
                                # Update headers
                                self.headers['Authorization'] = f'Bearer {self.access_token}'
                                # Save token for future use
                                self.save_token(token_data)
                                self.logger.info("Access token obtained and saved successfully")
                                return True
                    
                    self.logger.error(f"Token request failed: {token_response}")
                    return False
                        
        except Exception as e:
            self.logger.error(f"Error getting access token: {e}")
            return False
    
    async def test_token(self) -> bool:
        """Test if current access token is valid"""
        try:
            profile = await self.get_profile()
            # FIX: Check for successful response properly
            if profile and isinstance(profile, dict):
                return profile.get('status') == 'success'
            return False
        except Exception as e:
            self.logger.debug(f"Token test failed: {e}")
            return False
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """Make authenticated API request"""
        if not self.access_token:
            self.logger.error("No access token available")
            return None
            
        url = f"{self.base_url}{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                if method.upper() == 'GET':
                    async with session.get(url, headers=headers) as response:
                        response.raise_for_status()
                        return await response.json()
                        
                elif method.upper() == 'POST':
                    async with session.post(url, headers=headers, json=data) as response:
                        response.raise_for_status()
                        return await response.json()
                        
                elif method.upper() == 'PUT':
                    async with session.put(url, headers=headers, json=data) as response:
                        response.raise_for_status()
                        return await response.json()
                        
                elif method.upper() == 'DELETE':
                    async with session.delete(url, headers=headers) as response:
                        response.raise_for_status()
                        return await response.json()
            
        except Exception as e:
            self.logger.error(f"API request failed: {e}")
            return None
    
    async def get_profile(self) -> Optional[Dict]:
        """Get user profile information"""
        return await self._make_request('GET', '/user/profile')
    
    async def get_funds(self) -> Optional[Dict]:
        """Get account funds information"""
        return await self._make_request('GET', '/user/funds')
    
    async def get_positions(self) -> Optional[Dict]:
        """Get current positions"""
        return await self._make_request('GET', '/portfolio/long-term-positions')
    
    async def search_instruments(self, query: str) -> Optional[Dict]:
        """Search for trading instruments"""
        endpoint = f"/search/instruments?query={query}"
        return await self._make_request('GET', endpoint)
    
    async def get_market_data(self, instrument_key: str) -> Optional[Dict]:
        """Get market data for an instrument"""
        endpoint = f"/market-quote/quotes?instrument_key={instrument_key}"
        return await self._make_request('GET', endpoint)
    
    async def place_order(self, order_data: Dict) -> Optional[Dict]:
        """Place a trading order"""
        return await self._make_request('POST', '/order/place', order_data)
    
    async def get_order_history(self) -> Optional[Dict]:
        """Get order history"""
        return await self._make_request('GET', '/order/retrieve-all')
    
    async def get_option_ltp(self, instrument_key: str) -> Optional[float]:
        """Get Last Traded Price for an option - WORKING VERSION"""
        try:
            url = f"{self.base_url}/market-quote/ltp"
            params = {'instrument_key': instrument_key}
    
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Accept': 'application/json'
            }
    
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                
                        if data.get('status') == 'success' and 'data' in data:
                            quote_data = data['data']
                    
                            # WORKING: Try different key formats from successful test
                            possible_keys = [
                                instrument_key,  # NSE_FO|12345
                                instrument_key.replace('|', ':'),  # NSE_FO:12345
                                instrument_key.replace('NSE_FO|', 'NSE_FO:'),  # NSE_FO:12345
                            ]
                        
                            # Try exact matches first
                            for key_format in possible_keys:
                                if key_format in quote_data:
                                    ltp = quote_data[key_format].get('last_price', 0)
                                    if ltp > 0:
                                        self.logger.debug(f"LTP for {instrument_key}: {ltp}")
                                        return float(ltp)
                        
                            # Try partial matches (handles Upstox response format variations)
                            for key in quote_data.keys():
                                if any(part in key for part in instrument_key.split('|')):
                                    ltp = quote_data[key].get('last_price', 0)
                                    if ltp > 0:
                                        self.logger.debug(f"LTP for {instrument_key}: {ltp} (matched: {key})")
                                        return float(ltp)
                
                        self.logger.warning(f"No price data for {instrument_key}")
                        return None
                    else:
                        self.logger.error(f"API request failed with status {response.status}")
                        return None
                
        except Exception as e:
            self.logger.error(f"Error fetching option LTP: {e}")
            return None

    async def get_option_quote(self, instrument_key: str) -> Optional[Dict]:
        """Get detailed option quote - ENHANCED VERSION"""
        try:
            url = f"{self.base_url}/market-quote/quotes"
            params = {'instrument_key': instrument_key}
        
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Accept': 'application/json'
            }
        
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                    
                        if data.get('status') == 'success':
                            quote_data = data.get('data', {})
                        
                            # Find the correct key format
                            for key in quote_data.keys():
                                if any(part in key for part in instrument_key.split('|')):
                                    quote = quote_data[key]

                                    # Extract relevant data
                                    result = {
                                        'instrument_key': instrument_key,
                                        'last_price': quote.get('last_price', 0),
                                        'open': quote.get('open_price', 0),
                                        'high': quote.get('high_price', 0),
                                        'low': quote.get('low_price', 0),
                                        'volume': quote.get('volume', 0),
                                        'bid_price': quote.get('depth', {}).get('buy', [{}])[0].get('price', 0),
                                        'ask_price': quote.get('depth', {}).get('sell', [{}])[0].get('price', 0),
                                        'timestamp': quote.get('last_update_time', ''),
                                        'symbol': quote.get('trading_symbol', '')
                                    }
                                
                                    self.logger.debug(f"Quote for {instrument_key}: LTP={result['last_price']}")
                                    return result
                        
                            self.logger.warning(f"No quote data found for {instrument_key}")
                    
                        else:
                            self.logger.error(f"API error getting quote: {data}")
                    else:
                        error_text = await response.text()
                        self.logger.error(f"HTTP {response.status} getting quote: {error_text}")
        
            return None
        
        except Exception as e:
            self.logger.error(f"Error getting option quote for {instrument_key}: {e}")
            return None
        
    async def get_option_quote_full(self, instrument_key: str) -> Optional[Dict]:
        """Get full option quote with all details - ENHANCED VERSION"""
        try:
            # Get both LTP and detailed quote
            ltp_task = self.get_option_ltp(instrument_key)
            quote_task = self.get_option_quote(instrument_key)
        
            ltp, quote = await asyncio.gather(ltp_task, quote_task, return_exceptions=True)
        
            # Handle results
            if isinstance(ltp, Exception):
                self.logger.error(f"Error getting LTP: {ltp}")
                ltp = None
        
            if isinstance(quote, Exception):
                self.logger.error(f"Error getting quote: {quote}")
                quote = {}
        
            # Combine results
            result = quote or {}
            if ltp is not None:
                result['last_price'] = ltp
                    
            return result if result else None
                    
        except Exception as e:
            self.logger.error(f"Error getting full option quote for {instrument_key}: {e}")
            return None

    async def fetch_nearest_expiry_option_contracts(self) -> Dict[str, Dict]:
        """NEW METHOD: Fetch option contracts for nearest expiry"""
        try:
            url = f"{self.base_url}/option/contract"
            params = {'instrument_key': 'NSE_INDEX|Nifty 50'}
        
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Accept': 'application/json'
            }
        
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        if data.get('status') == 'success':
                            # Process contracts same as in OptionChainManager
                            all_contracts = []

                            for contract in data.get('data', []):
                                strike = contract.get('strike_price')
                                option_type = contract.get('instrument_type')
                                instrument_key = contract.get('instrument_key')
                                trading_symbol = contract.get('trading_symbol')
                                expiry = contract.get('expiry')
                            
                                if strike and option_type and instrument_key and expiry:
                                    strike_int = int(float(strike))  # FIXED parsing

                                    all_contracts.append({
                                        'strike_price': strike_int,
                                        'option_type': option_type,
                                        'instrument_key': instrument_key,
                                        'trading_symbol': trading_symbol,
                                        'expiry': expiry,
                                        'expiry_date': datetime.strptime(expiry, '%Y-%m-%d').date()
                                    })
                        
                            # Filter for nearest expiry
                            expiry_dates = sorted(set(contract['expiry_date'] for contract in all_contracts))
                            nearest_expiry = expiry_dates[0]
                        
                            contracts = {}
                            for contract in all_contracts:
                                if contract['expiry_date'] == nearest_expiry:
                                    key = f"{contract['strike_price']}{contract['option_type']}"
                                    contracts[key] = contract
                        
                            self.logger.info(f"Fetched {len(contracts)} nearest expiry option contracts")
                            return contracts

                        else:
                            self.logger.error(f"API error fetching option contracts: {data}")
                    else:
                        error_text = await response.text()
                        self.logger.error(f"HTTP {response.status} fetching option contracts: {error_text}")
        
            return {}

        except Exception as e:
            self.logger.error(f"Error fetching option contracts: {e}")
            return {}