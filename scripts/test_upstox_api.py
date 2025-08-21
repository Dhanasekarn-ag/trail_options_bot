#!/usr/bin/env python3
"""Test Upstox API directly"""
import asyncio
import aiohttp
import json
from pathlib import Path

async def test_upstox_api():
    """Direct API test"""
    
    # Load access token
    token_file = Path("data/access_token.json")
    if not token_file.exists():
        print("❌ No access token found!")
        return
        
    with open(token_file) as f:
        token_data = json.load(f)
        access_token = token_data.get('access_token')
    
    print("🔍 Testing Upstox API Directly")
    print("=" * 50)
    
    # Test endpoints
    base_url = "https://api.upstox.com/v2"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }
    
    # Test 1: Get profile (verify token works)
    async with aiohttp.ClientSession() as session:
        print("\n1️⃣ Testing Profile API:")
        async with session.get(f"{base_url}/user/profile", headers=headers) as response:
            if response.status == 200:
                print("✅ Token is valid")
            else:
                print(f"❌ Token invalid: {response.status}")
                return
        
        # Test 2: Get NIFTY spot price
        print("\n2️⃣ Testing NIFTY Spot Price:")
        nifty_key = "NSE_INDEX|Nifty 50"
        url = f"{base_url}/market-quote/ltp?symbol={nifty_key}"
        
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                print(f"Response: {json.dumps(data, indent=2)}")
            else:
                print(f"❌ Failed: {response.status}")
        
        # Test 3: Search for NIFTY options
        print("\n3️⃣ Searching for NIFTY Options:")
        search_url = f"{base_url}/option/contract"
        params = {
            'symbol': 'NIFTY',
            'expiry_date': '2025-08-14'  # Adjust date
        }
        
        async with session.get(search_url, headers=headers, params=params) as response:
            text = await response.text()
            print(f"Response: {text[:500]}")  # First 500 chars

if __name__ == "__main__":
    asyncio.run(test_upstox_api())