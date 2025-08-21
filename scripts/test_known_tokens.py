#!/usr/bin/env python3
"""Test with known NIFTY option tokens"""
import asyncio
import aiohttp
import json
from pathlib import Path

# These are example tokens - you'll need real ones
# You can find these from Upstox web platform
KNOWN_TOKENS = {
    'NIFTY_AUG14_24600CE': 'NSE_FO|37843',  # Replace with actual
    'NIFTY_AUG14_24600PE': 'NSE_FO|37844',  # Replace with actual
}

async def test_known_tokens():
    """Test with known instrument tokens"""
    
    token_file = Path("data/access_token.json")
    with open(token_file) as f:
        token_data = json.load(f)
        access_token = token_data.get('access_token')
    
    base_url = "https://api.upstox.com/v2"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }
    
    print("Testing Known Tokens:")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        for name, token in KNOWN_TOKENS.items():
            url = f"{base_url}/market-quote/ltp?symbol={token}"
            
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ {name}: {data}")
                else:
                    print(f"❌ {name}: Failed")

if __name__ == "__main__":
    asyncio.run(test_known_tokens())