# ==================== quick_diagnostic.py (SUPER SIMPLE) ====================
"""
Ultra-simple diagnostic to understand what Upstox APIs are available
Run this first to see what works
"""

import asyncio
import aiohttp
import json
from pathlib import Path

def get_token():
    """Get token from bot data"""
    try:
        token_file = Path("data") / "access_token.json"
        with open(token_file, 'r') as f:
            data = json.load(f)
            return data.get('access_token')
    except:
        return None

async def test_basic_apis(token):
    """Test basic Upstox APIs to see what works"""
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json'
    }
    
    print("🔍 Testing Basic Upstox APIs...")
    print("=" * 40)
    
    # Test 1: User profile (should always work)
    try:
        url = "https://api.upstox.com/v2/user/profile"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    user = data.get('data', {}).get('user_name', 'Unknown')
                    print(f"✅ User Profile API: {user}")
                else:
                    print(f"❌ User Profile API: {response.status}")
    except Exception as e:
        print(f"❌ User Profile API: {e}")
    
    # Test 2: NIFTY spot price (basic market data)
    try:
        url = "https://api.upstox.com/v2/market-quote/ltp"
        params = {'instrument_key': 'NSE_INDEX|Nifty 50'}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('status') == 'success':
                        # Find NIFTY data in response
                        nifty_data = None
                        for key, value in data.get('data', {}).items():
                            if 'Nifty' in key:
                                nifty_data = value
                                break
                        
                        if nifty_data:
                            price = nifty_data.get('last_price', 0)
                            print(f"✅ NIFTY Spot Price: Rs.{price:.2f}")
                        else:
                            print(f"⚠️ NIFTY data format: {list(data.get('data', {}).keys())}")
                    else:
                        print(f"❌ NIFTY API error: {data}")
                else:
                    print(f"❌ NIFTY API: HTTP {response.status}")
    except Exception as e:
        print(f"❌ NIFTY API: {e}")
    
    # Test 3: Try different option API endpoints
    option_endpoints = [
        "/option/chain",
        "/option/contract", 
        "/market-quote/option-chain",
        "/pc-option-chain"
    ]
    
    print(f"\n🧪 Testing Option API Endpoints...")
    
    for endpoint in option_endpoints:
        try:
            url = f"https://api.upstox.com/v2{endpoint}"
            
            # Try different parameter combinations
            param_sets = [
                {'instrument_key': 'NSE_INDEX|Nifty 50'},
                {'symbol': 'NIFTY'},
                {'underlying_key': 'NSE_INDEX|Nifty 50'},
                {'instrument_key': 'NSE_INDEX|Nifty 50', 'expiry': '2025-08-21'}
            ]
            
            for i, params in enumerate(param_sets):
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get('status') == 'success':
                                print(f"✅ {endpoint} (params {i+1}): SUCCESS")
                                # Show sample data structure
                                sample_data = data.get('data', [])
                                if isinstance(sample_data, list) and sample_data:
                                    print(f"   Sample keys: {list(sample_data[0].keys())}")
                                elif isinstance(sample_data, dict):
                                    print(f"   Data keys: {list(sample_data.keys())}")
                                break
                        elif response.status == 400:
                            error_text = await response.text()
                            if "Required request parameter" in error_text:
                                continue  # Try next param set
                            else:
                                print(f"❌ {endpoint}: {error_text[:100]}")
                                break
                        else:
                            print(f"❌ {endpoint}: HTTP {response.status}")
                            break
            else:
                print(f"❌ {endpoint}: All parameter combinations failed")
                
        except Exception as e:
            print(f"❌ {endpoint}: {e}")
    
    # Test 4: Download instruments file (this should always work)
    try:
        print(f"\n📥 Testing Instruments Download...")
        url = "https://assets.upstox.com/market-quote/instruments/exchange/complete.json"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    instruments = await response.json()
                    
                    # Count NIFTY options
                    nifty_options = [i for i in instruments if i.get('name') == 'NIFTY' and i.get('instrument_type') in ['CE', 'PE']]
                    
                    print(f"✅ Instruments Download: {len(nifty_options)} NIFTY options found")
                    
                    if nifty_options:
                        sample = nifty_options[0]
                        print(f"   Sample: {sample.get('strike_price')}{sample.get('instrument_type')} -> {sample.get('instrument_key')}")
                        return nifty_options[:5]  # Return first 5 for testing
                else:
                    print(f"❌ Instruments Download: HTTP {response.status}")
    except Exception as e:
        print(f"❌ Instruments Download: {e}")
    
    return []

async def test_option_ltp(token, sample_options):
    """Test LTP fetching with sample options"""
    if not sample_options:
        print("\n❌ No sample options to test")
        return
    
    print(f"\n💰 Testing Option LTP Fetching...")
    print("=" * 40)
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json'
    }
    
    for option in sample_options:
        try:
            strike = option.get('strike_price')
            option_type = option.get('instrument_type')
            instrument_key = option.get('instrument_key')
            
            print(f"\n🧪 Testing {strike}{option_type}:")
            print(f"   Key: {instrument_key}")
            
            url = "https://api.upstox.com/v2/market-quote/ltp"
            params = {'instrument_key': instrument_key}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('status') == 'success':
                            quote_data = data.get('data', {})
                            
                            # Try to find the data
                            ltp = None
                            for key, value in quote_data.items():
                                if instrument_key in key or any(part in key for part in instrument_key.split('|')):
                                    ltp = value.get('last_price', 0)
                                    if ltp > 0:
                                        print(f"   ✅ LTP: Rs.{ltp:.2f}")
                                        break
                            
                            if not ltp:
                                print(f"   ❌ No LTP found in response")
                                print(f"   Available keys: {list(quote_data.keys())}")
                        else:
                            print(f"   ❌ API error: {data}")
                    else:
                        error_text = await response.text()
                        print(f"   ❌ HTTP {response.status}: {error_text[:100]}")
                        
        except Exception as e:
            print(f"   ❌ Error: {e}")

async def main():
    """Main diagnostic function"""
    print("🔍 Upstox API Diagnostic Tool")
    print("=" * 50)
    
    token = get_token()
    if not token:
        print("❌ No token found!")
        return
    
    print(f"✅ Token found: {token[:10]}...{token[-10:]}")
    
    # Test basic APIs first
    sample_options = await test_basic_apis(token)
    
    # If we got sample options, test LTP fetching
    await test_option_ltp(token, sample_options)
    
    print("\n" + "=" * 50)
    print("🏁 Diagnostic Complete!")
    print("Use the results above to understand what works")

if __name__ == "__main__":
    asyncio.run(main())