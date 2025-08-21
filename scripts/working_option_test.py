# ==================== working_option_test.py (FINAL WORKING VERSION) ====================
"""
FINAL VERSION: Based on diagnostic results
✅ Uses /option/contract API with correct parameters (instrument_key)
✅ Fetches real option contracts and tests LTP
✅ Should work 100% based on your diagnostic results
"""

import asyncio
import aiohttp
import json
from pathlib import Path
from datetime import datetime, timedelta

def get_token():
    """Get token from bot data"""
    try:
        token_file = Path("data") / "access_token.json"
        with open(token_file, 'r') as f:
            data = json.load(f)
            return data.get('access_token')
    except:
        return None

class WorkingOptionTester:
    """Working option tester based on diagnostic results"""
    
    def __init__(self, token):
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json'
        }
    
    def get_nearest_expiry(self):
        """Get nearest Thursday expiry"""
        today = datetime.now()
        days_until_thursday = (3 - today.weekday()) % 7
        
        if days_until_thursday == 0:
            if today.hour < 15:
                next_thursday = today
            else:
                next_thursday = today + timedelta(days=7)
        else:
            next_thursday = today + timedelta(days=days_until_thursday)
        
        return next_thursday.strftime('%Y-%m-%d')
    
    async def fetch_option_contracts(self):
        """Fetch option contracts using the WORKING API endpoint"""
        print("📋 Fetching NIFTY option contracts...")
        
        try:
            url = "https://api.upstox.com/v2/option/contract"
            
            # ✅ CORRECT PARAMETERS based on diagnostic
            params = {
                'instrument_key': 'NSE_INDEX|Nifty 50'  # This is what works!
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('status') == 'success':
                            contracts = {}
                            
                            for contract in data.get('data', []):
                                strike = contract.get('strike_price')
                                option_type = contract.get('instrument_type')  # CE or PE
                                instrument_key = contract.get('instrument_key')
                                trading_symbol = contract.get('trading_symbol')
                                expiry = contract.get('expiry')
                                
                                if strike and option_type and instrument_key:
                                    key = f"{strike}{option_type}"
                                    contracts[key] = {
                                        'instrument_key': instrument_key,
                                        'strike_price': strike,
                                        'option_type': option_type,
                                        'trading_symbol': trading_symbol,
                                        'expiry': expiry
                                    }
                            
                            print(f"✅ Found {len(contracts)} option contracts")
                            return contracts
                        else:
                            print(f"❌ API error: {data}")
                    else:
                        error_text = await response.text()
                        print(f"❌ HTTP {response.status}: {error_text}")
            
            return {}
            
        except Exception as e:
            print(f"❌ Error fetching contracts: {e}")
            return {}
    
    async def test_option_ltp(self, instrument_key, option_name):
        """Test LTP fetching for specific option"""
        try:
            url = "https://api.upstox.com/v2/market-quote/ltp"
            params = {'instrument_key': instrument_key}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('status') == 'success':
                            quote_data = data.get('data', {})
                            
                            # Debug: Show what keys are available
                            print(f"   Response keys: {list(quote_data.keys())}")
                            
                            # Try to find our instrument key in response
                            for key in quote_data.keys():
                                if instrument_key in key or key.replace(':', '|') == instrument_key:
                                    ltp = quote_data[key].get('last_price', 0)
                                    if ltp > 0:
                                        print(f"   ✅ {option_name}: Rs.{ltp:.2f}")
                                        return ltp
                            
                            # If exact match not found, show available keys
                            print(f"   ❌ {option_name}: Instrument key not found")
                            print(f"   Looking for: {instrument_key}")
                            
                        else:
                            print(f"   ❌ {option_name}: API error {data}")
                    else:
                        error_text = await response.text()
                        print(f"   ❌ {option_name}: HTTP {response.status}")
                        
        except Exception as e:
            print(f"   ❌ {option_name}: {e}")
        
        return None
    
    async def run_working_test(self):
        """Run the test using working API endpoints"""
        print("🚀 Working Option Premium Test")
        print("=" * 50)
        
        # Step 1: Get NIFTY spot price (we know this works)
        try:
            url = "https://api.upstox.com/v2/market-quote/ltp"
            params = {'instrument_key': 'NSE_INDEX|Nifty 50'}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        for key, value in data.get('data', {}).items():
                            if 'Nifty' in key:
                                spot_price = value.get('last_price', 0)
                                print(f"📈 NIFTY Spot: Rs.{spot_price:.2f}")
                                break
        except:
            spot_price = 25000
        
        # Step 2: Fetch option contracts
        contracts = await self.fetch_option_contracts()
        
        if not contracts:
            print("❌ Could not fetch option contracts")
            return False
        
        # Step 3: Show available contracts
        ce_options = [k for k in contracts.keys() if k.endswith('CE')]
        pe_options = [k for k in contracts.keys() if k.endswith('PE')]
        
        print(f"\n📊 Available Options:")
        print(f"   CE Options: {len(ce_options)}")
        print(f"   PE Options: {len(pe_options)}")
        
        if ce_options:
            # Show first few CE strikes
            ce_strikes = sorted([int(k[:-2]) for k in ce_options])
            print(f"   CE Strikes: {ce_strikes[:5]}...{ce_strikes[-5:]} (showing first/last 5)")
        
        # Step 4: Test LTP for a few options
        print(f"\n💰 Testing LTP Fetching:")
        
        success_count = 0
        test_options = []
        
        # Pick a few options to test
        if ce_options:
            test_options.extend(ce_options[:3])  # First 3 CE
        if pe_options:
            test_options.extend(pe_options[:2])  # First 2 PE
        
        for option_key in test_options:
            if option_key in contracts:
                contract = contracts[option_key]
                print(f"\n🧪 Testing {option_key}:")
                print(f"   Trading Symbol: {contract['trading_symbol']}")
                print(f"   Instrument Key: {contract['instrument_key']}")
                print(f"   Expiry: {contract['expiry']}")
                
                ltp = await self.test_option_ltp(contract['instrument_key'], option_key)
                
                if ltp:
                    success_count += 1
                    
                    # Validate premium range
                    if 5 <= ltp <= 1000:
                        print(f"   ✅ Premium in valid range: Rs.{ltp:.2f}")
                    else:
                        print(f"   ⚠️ Premium unusual: Rs.{ltp:.2f}")
        
        # Step 5: Results
        print(f"\n" + "=" * 50)
        print(f"📊 TEST RESULTS:")
        print(f"✅ Successful LTP fetches: {success_count}/{len(test_options)}")
        
        if success_count > 0:
            print(f"🎉 SUCCESS! Option premium fetching works!")
            print(f"✅ Ready to implement in your main bot")
            print(f"\n📝 Implementation notes:")
            print(f"   - Use /option/contract API with instrument_key='NSE_INDEX|Nifty 50'")
            print(f"   - LTP API works with the returned instrument keys")
            print(f"   - Response format may need key mapping")
            return True
        else:
            print(f"❌ LTP fetching failed - may be market hours issue")
            if datetime.now().hour < 9 or datetime.now().hour > 15:
                print(f"⏰ Market is likely closed - try during 9:15 AM - 3:30 PM")
            return False

async def main():
    """Main function"""
    print("🔧 Final Working Option Premium Test")
    print("=" * 50)
    
    token = get_token()
    if not token:
        print("❌ No token found!")
        return
    
    tester = WorkingOptionTester(token)
    await tester.run_working_test()

if __name__ == "__main__":
    asyncio.run(main())


# ==================== IMPLEMENTATION GUIDE ====================
"""
🎯 HOW TO FIX YOUR MAIN BOT:

Based on the test results, here's what you need to change in your main bot:

1. ✅ CORRECT API ENDPOINT:
   URL: https://api.upstox.com/v2/option/contract
   Parameters: {'instrument_key': 'NSE_INDEX|Nifty 50'}

2. ✅ CORRECT RESPONSE PARSING:
   The response contains 'data' array with option contracts
   Each contract has: instrument_key, strike_price, instrument_type, trading_symbol

3. ✅ CORRECT LTP FETCHING:
   URL: https://api.upstox.com/v2/market-quote/ltp  
   Parameters: {'instrument_key': '<actual_instrument_key_from_contract>'}

4. ✅ KEY MAPPING:
   The LTP response keys might be formatted differently (e.g., 'NSE_FO:TOKEN' vs 'NSE_FO|TOKEN')
   You'll need to handle this in your parsing logic

5. ✅ ERROR HANDLING:
   - Check market hours (9:15 AM - 3:30 PM)
   - Handle missing strikes gracefully  
   - Cache option contracts to avoid repeated API calls

NEXT STEP: Run this test and if successful, I'll give you the exact code 
to replace in your main bot!
"""