#!/usr/bin/env python3
import asyncio
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import get_settings
from src.upstox_client import UpstoxClient

async def test():
    settings = get_settings()
    client = UpstoxClient(
        settings.upstox_api_key,
        settings.upstox_api_secret,
        settings.upstox_redirect_uri
    )
    
    test_cases = [
        ("NSE_FO|44492", "NIFTY 24600 CE"),
        ("NSE_FO|44502", "NIFTY 24600 PE"),
        ("NSE_FO|44493", "NIFTY 24650 CE"),
    ]
    
    print("Testing Fixed API Methods")
    print("=" * 50)
    
    for instrument_key, description in test_cases:
        print(f"\n{description}:")
        
        # Test LTP
        ltp = await client.get_option_ltp(instrument_key)
        if ltp:
            print(f"  ✅ LTP: Rs.{ltp}")
        else:
            print(f"  ❌ Failed to get LTP")
        
        # Test full quote
        quote = await client.get_option_quote_full(instrument_key)
        if quote:
            print(f"  📊 Full Quote:")
            print(f"     Open: {quote['open']}, High: {quote['high']}, Low: {quote['low']}, Close: {quote['close']}")
            print(f"     Bid: {quote['bid']}, Ask: {quote['ask']}")
            print(f"     Volume: {quote['volume']}, OI: {quote['oi']}")

if __name__ == "__main__":
    asyncio.run(test())