#!/usr/bin/env python3
import asyncio
import aiohttp
import json
from pathlib import Path

async def debug_option_api():
    """Debug the exact API call"""
    
    # Load access token
    token_file = Path("data/access_token.json")
    with open(token_file) as f:
        token_data = json.load(f)
        access_token = token_data.get('access_token')
    
    print("🔍 Debugging Option API Calls")
    print("=" * 50)
    
    # Test with exact instrument key
    instrument_key = "NSE_FO|44492"  # NIFTY 24600 CE
    
    base_url = "https://api.upstox.com/v2"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }
    
    # Method 1: LTP endpoint with 'symbol' parameter
    print("\n1️⃣ Testing LTP endpoint with 'symbol':")
    url1 = f"{base_url}/market-quote/ltp?symbol={instrument_key}"
    print(f"URL: {url1}")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url1, headers=headers) as response:
            print(f"Status: {response.status}")
            text = await response.text()
            print(f"Response: {text[:500]}")
            
            if response.status == 200:
                data = json.loads(text)
                if 'data' in data:
                    print(f"\n✅ Success! Data structure:")
                    print(json.dumps(data, indent=2))
    
    # Method 2: LTP endpoint with 'instrument_key' parameter
    print("\n2️⃣ Testing LTP endpoint with 'instrument_key':")
    url2 = f"{base_url}/market-quote/ltp?instrument_key={instrument_key}"
    print(f"URL: {url2}")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url2, headers=headers) as response:
            print(f"Status: {response.status}")
            if response.status == 200:
                data = await response.json()
                print(f"Response: {json.dumps(data, indent=2)}")
    
    # Method 3: Quotes endpoint
    print("\n3️⃣ Testing Quotes endpoint:")
    url3 = f"{base_url}/market-quote/quotes?symbol={instrument_key}"
    print(f"URL: {url3}")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url3, headers=headers) as response:
            print(f"Status: {response.status}")
            if response.status == 200:
                data = await response.json()
                print(f"Response: {json.dumps(data, indent=2)[:500]}")
    
    # Method 4: Try URL encoding
    print("\n4️⃣ Testing with URL encoding:")
    import urllib.parse
    encoded_key = urllib.parse.quote(instrument_key)
    url4 = f"{base_url}/market-quote/ltp?symbol={encoded_key}"
    print(f"URL: {url4}")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url4, headers=headers) as response:
            print(f"Status: {response.status}")
            if response.status == 200:
                data = await response.json()
                print(f"Response: {json.dumps(data, indent=2)}")

if __name__ == "__main__":
    asyncio.run(debug_option_api())