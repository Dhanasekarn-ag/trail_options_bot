#!/usr/bin/env python3
"""Find correct option instrument format"""
import asyncio
import aiohttp
import json
from pathlib import Path
from datetime import datetime, timedelta

async def find_option_format():
    """Find the correct option instrument key format"""
    
    # Load access token
    token_file = Path("data/access_token.json")
    with open(token_file) as f:
        token_data = json.load(f)
        access_token = token_data.get('access_token')
    
    print("🔍 Finding NIFTY Option Format")
    print("=" * 50)
    
    base_url = "https://api.upstox.com/v2"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }
    
    async with aiohttp.ClientSession() as session:
        # Test different possible formats
        test_formats = [
            "NSE_FO|64803",  # Possible token ID format
            "NSE_FO|NIFTY24600CE",  # Simple format
            "NSE_FO|NIFTY-24600-CE",  # Hyphenated
            "NSE_FO|NIFTY 24600 CE",  # Spaced
            "NSE_FO|NIFTY25814-24600CE",  # Date format
            "NSE_FO|NIFTY2425-24600CE",  # Year-week format
            "NSE_FO|35036",  # Numeric token
            "NFO|NIFTY|24600|CE|14AUG25",  # Alternative format
        ]
        
        print("\n1️⃣ Testing different formats for LTP:")
        for format_key in test_formats:
            url = f"{base_url}/market-quote/ltp?symbol={format_key}"
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'data' in data and format_key in data['data']:
                        print(f"✅ FOUND: {format_key}")
                        print(f"   Data: {data['data'][format_key]}")
                    else:
                        print(f"❌ {format_key}")
                else:
                    print(f"❌ {format_key} - Status: {response.status}")
        
        # Try option chain endpoint
        print("\n2️⃣ Trying Option Chain endpoint:")
        option_url = f"{base_url}/option/chain"
        params = {
            'symbol': 'NSE_INDEX|Nifty 50',
            'expiry_date': '2025-08-14'
        }
        
        async with session.get(option_url, headers=headers, params=params) as response:
            text = await response.text()
            print(f"Response: {text[:500]}")
        
        # Try instruments master
        print("\n3️⃣ Getting Instruments List:")
        instruments_url = f"{base_url}/instruments/master"
        
        async with session.get(instruments_url, headers=headers) as response:
            if response.status == 200:
                print("✅ Got instruments master")
                text = await response.text()
                
                # Search for NIFTY options in the response
                lines = text.split('\n')[:100]  # First 100 lines
                
                print("\nSearching for NIFTY option examples:")
                for line in lines:
                    if 'NIFTY' in line and ('CE' in line or 'PE' in line):
                        print(f"  Found: {line[:150]}")
                        break
        
        # Try market quote with multiple symbols
        print("\n4️⃣ Testing Market Quote:")
        quote_url = f"{base_url}/market-quote/quotes"
        
        # Try with index
        params = {'symbol': 'NSE_INDEX|Nifty 50'}
        async with session.get(quote_url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                print(f"NIFTY Index quote works: {data.get('status')}")

async def search_options():
    """Search for options using different methods"""
    
    token_file = Path("data/access_token.json")
    with open(token_file) as f:
        token_data = json.load(f)
        access_token = token_data.get('access_token')
    
    print("\n🔍 Searching for NIFTY Options")
    print("=" * 50)
    
    base_url = "https://api.upstox.com/v2"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
        'Api-Version': '2.0'  # Try with version header
    }
    
    async with aiohttp.ClientSession() as session:
        # Method 1: Search instruments
        print("\n1️⃣ Search Instruments:")
        search_url = f"{base_url}/instruments/search"
        
        for query in ['NIFTY24600CE', 'NIFTY 24600', 'NIFTY CE']:
            params = {'q': query}
            async with session.get(search_url, headers=headers, params=params) as response:
                print(f"\nSearching for '{query}':")
                if response.status == 200:
                    data = await response.json()
                    if 'data' in data:
                        results = data['data'][:3]  # First 3 results
                        for r in results:
                            print(f"  Found: {r.get('trading_symbol')} - {r.get('instrument_key')}")
                else:
                    print(f"  Status: {response.status}")

if __name__ == "__main__":
    asyncio.run(find_option_format())
    asyncio.run(search_options())