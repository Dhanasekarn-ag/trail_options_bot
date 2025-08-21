#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import get_settings
from src.upstox_client import UpstoxClient
from src.utils.option_instruments import get_instrument_key

async def test_option_pricing():
    settings = get_settings()
    client = UpstoxClient(
        settings.upstox_api_key,
        settings.upstox_api_secret,
        settings.upstox_redirect_uri
    )
    
    # Test different strikes
    test_cases = [
        (24500, 'CE'),
        (24550, 'CE'),        
        (24600, 'CE'),
        (24650, 'CE'),
        (24700, 'CE'),
        (24750, 'CE'),
        (24800, 'CE'),
        (24850, 'CE'),
        (24900, 'CE'),
        (24950, 'CE'),
        (25000, 'CE'),
        (25050, 'CE'),
        (25100, 'CE'),
        (25150, 'CE'),
        (25200, 'CE'),
        (24500, 'PE'),
        (24550, 'PE'),        
        (24600, 'PE'),
        (24650, 'PE'),
        (24700, 'PE'),
        (24750, 'PE'),
        (24800, 'PE'),
        (24850, 'PE'),
        (24900, 'PE'),
        (24950, 'PE'),
        (25000, 'PE'),
        (25050, 'PE'),
        (25100, 'PE'),
        (25150, 'PE'),
        (25200, 'PE'),
        
    ]
    
    for strike, option_type in test_cases:
        instrument_key = get_instrument_key(strike, option_type)
        if instrument_key:
            price = await client.get_option_ltp(instrument_key)
            print(f"{strike}{option_type}: Rs.{price} (Key: {instrument_key})")
        else:
            print(f"{strike}{option_type}: No key found")

if __name__ == "__main__":
    asyncio.run(test_option_pricing())
    