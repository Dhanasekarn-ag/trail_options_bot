#!/usr/bin/env python3
"""Test real option prices"""
import asyncio
import aiohttp
import json
from pathlib import Path

async def test_real_price():
    """Test fetching real option price"""
    
    # Load token
    token_file = Path("data/access_token.json")
    with open(token_file) as f:
        token_data = json.load(f)
        access_token = token_data.get('access_token')
    
    # Test with the key you found
    instrument_key = "NSE_FO|44492"  # NIFTY 24600 CE
    
    base_url = "https://api.upstox.com/v2"
    url = f"{base_url}/market-quote/ltp?symbol={instrument_key}"
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }
    
    print(f"Testing: NIFTY 24600 CE")
    print(f"Key: {instrument_key}")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ Response: {json.dumps(data, indent=2)}")
                
                # Extract price
                if 'data' in data and instrument_key in data['data']:
                    ltp = data['data'][instrument_key].get('last_price', 0)
                    print(f"\n💰 Current Price: Rs.{ltp}")
            else:
                print(f"❌ Failed: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_real_price())