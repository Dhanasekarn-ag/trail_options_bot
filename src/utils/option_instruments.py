# ==================== src/utils/option_instruments_live.py ====================
from datetime import datetime, timedelta
import aiohttp
import logging

class OptionInstrumentManager:
    """Manage NIFTY option instrument keys from Upstox"""
    
    def __init__(self, upstox_client):
        self.upstox_client = upstox_client
        self.logger = logging.getLogger(__name__)
        self.instrument_cache = {}
        
    async def get_nifty_option_instruments(self):
        """Fetch NIFTY option instruments from Upstox master API"""
        try:
            url = "https://api.upstox.com/v2/market-quote/instruments"
            headers = {
                'Authorization': f'Bearer {self.upstox_client.access_token}',
                'Accept': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Filter NIFTY options
                        nifty_options = []
                        if 'data' in data:
                            for instrument in data['data']:
                                if (instrument.get('name', '').startswith('NIFTY') and 
                                    instrument.get('instrument_type') == 'OPTIDX'):
                                    nifty_options.append(instrument)
                        
                        self.logger.info(f"Loaded {len(nifty_options)} NIFTY option instruments")
                        return nifty_options
            
            return []
            
        except Exception as e:
            self.logger.error(f"Error fetching option instruments: {e}")
            return []
    
    def find_option_instrument_key(self, strike: int, option_type: str, expiry: str = None):
        """Find exact instrument key for option"""
        try:
            # Search in cached instruments
            for instrument in self.instrument_cache:
                if (instrument.get('strike_price') == strike and 
                    instrument.get('option_type') == option_type):
                    return instrument.get('instrument_key')
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding instrument key: {e}")
            return None