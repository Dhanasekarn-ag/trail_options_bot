# ==================== test_option_premium.py (STANDALONE TEST) ====================
"""
Standalone script to test Upstox option premium fetching
Run this to validate the fix before implementing in your main bot

Usage:
1. Save this as test_option_premium.py  
2. Update ACCESS_TOKEN with your current token
3. Run: python test_option_premium.py
4. Check if it fetches real option premiums successfully
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, List

# ==================== CONFIGURATION ====================
# UPDATE THIS with your current Upstox access token
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiIyR0NFQ0MiLCJqdGkiOiI2OGE1NDY5MjkzOWUzZTEzNTVjMDA0OGEiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaWF0IjoxNzU1NjYxOTcwLCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3NTU3MjcyMDB9.TNm3J0CZ_6AgUe0ZbeVTlI4d-aLBfC2nEyWjs66fqHA"  # ⚠️ REPLACE WITH REAL TOKEN

# Test parameters
TEST_SYMBOL = "NIFTY"
TEST_STRIKES = [24900, 24950, 25000, 25050, 25100]  # Different strikes to test
TEST_OPTION_TYPES = ["CE", "PE"]

class OptionPremiumTester:
    """Standalone tester for Upstox option premium fetching"""
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://api.upstox.com/v2"
        
    def get_headers(self):
        """Get API headers"""
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json'
        }
    
    def get_nearest_expiry(self) -> str:
        """Get nearest Thursday expiry"""
        today = datetime.now()
        days_until_thursday = (3 - today.weekday()) % 7
        
        if days_until_thursday == 0:
            if today.hour < 15:  # Before 3 PM
                next_thursday = today
            else:
                next_thursday = today + timedelta(days=7)
        else:
            next_thursday = today + timedelta(days=days_until_thursday)
        
        return next_thursday.strftime('%Y-%m-%d')
    
    async def test_token_validity(self) -> bool:
        """Test if access token is valid"""
        print("🔐 Testing access token validity...")
        
        try:
            url = f"{self.base_url}/user/profile"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.get_headers()) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('status') == 'success':
                            user_name = data.get('data', {}).get('user_name', 'Unknown')
                            print(f"✅ Token valid! User: {user_name}")
                            return True
                    elif response.status == 401:
                        print("❌ Token expired or invalid!")
                        return False
                    else:
                        print(f"❌ API error: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ Error testing token: {e}")
            return False
    
    async def fetch_option_contracts(self, symbol: str = "NIFTY") -> Dict:
        """Fetch available option contracts"""
        print(f"📋 Fetching {symbol} option contracts...")
        
        try:
            url = f"{self.base_url}/option/contract"
            expiry = self.get_nearest_expiry()
            params = {'symbol': symbol, 'expiry': expiry}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.get_headers(), params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('status') == 'success':
                            contracts = {}
                            for contract in data.get('data', []):
                                strike = contract.get('strike_price')
                                option_type = contract.get('instrument_type')
                                instrument_key = contract.get('instrument_key')
                                
                                if strike and option_type and instrument_key:
                                    key = f"{strike}{option_type}"
                                    contracts[key] = {
                                        'instrument_key': instrument_key,
                                        'strike_price': strike,
                                        'option_type': option_type,
                                        'trading_symbol': contract.get('trading_symbol'),
                                        'expiry': contract.get('expiry')
                                    }
                            
                            print(f"✅ Found {len(contracts)} option contracts for expiry {expiry}")
                            return contracts
                        else:
                            print(f"❌ API returned error: {data}")
                    else:
                        error_text = await response.text()
                        print(f"❌ HTTP {response.status}: {error_text}")
                        
        except Exception as e:
            print(f"❌ Error fetching contracts: {e}")
        
        return {}
    
    async def test_ltp_fetch(self, instrument_key: str, option_name: str) -> Optional[float]:
        """Test LTP fetching for a specific instrument"""
        try:
            url = f"{self.base_url}/market-quote/ltp"
            params = {'instrument_key': instrument_key}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.get_headers(), params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('status') == 'success' and 'data' in data:
                            quote_data = data['data']
                            
                            if instrument_key in quote_data:
                                ltp = quote_data[instrument_key].get('last_price', 0)
                                if ltp > 0:
                                    print(f"✅ {option_name}: Rs.{ltp:.2f}")
                                    return float(ltp)
                                else:
                                    print(f"⚠️ {option_name}: Invalid LTP ({ltp})")
                            else:
                                print(f"❌ {option_name}: Key not in response")
                    else:
                        print(f"❌ {option_name}: HTTP {response.status}")
                        
        except Exception as e:
            print(f"❌ {option_name}: Error - {e}")
        
        return None
    
    async def run_comprehensive_test(self):
        """Run comprehensive test of option premium fetching"""
        print("🚀 Starting Comprehensive Option Premium Test")
        print("=" * 60)
        
        # Step 1: Test token
        if not await self.test_token_validity():
            print("\n❌ Cannot proceed - invalid access token!")
            print("Please update ACCESS_TOKEN in the script with your current token")
            return False
        
        # Step 2: Fetch option contracts
        contracts = await self.fetch_option_contracts(TEST_SYMBOL)
        
        if not contracts:
            print("\n❌ No option contracts found!")
            return False
        
        # Step 3: Show available strikes
        ce_strikes = sorted([int(k[:-2]) for k in contracts.keys() if k.endswith('CE')])
        pe_strikes = sorted([int(k[:-2]) for k in contracts.keys() if k.endswith('PE')])
        
        print(f"\n📊 Available strikes:")
        print(f"   CE options: {len(ce_strikes)} strikes ({min(ce_strikes)}-{max(ce_strikes)})")
        print(f"   PE options: {len(pe_strikes)} strikes ({min(pe_strikes)}-{max(pe_strikes)})")
        
        # Step 4: Test LTP fetching for specific strikes
        print(f"\n💰 Testing LTP fetch for sample options:")
        
        success_count = 0
        total_tests = 0
        
        for strike in TEST_STRIKES:
            for option_type in TEST_OPTION_TYPES:
                option_key = f"{strike}{option_type}"
                
                if option_key in contracts:
                    contract = contracts[option_key]
                    instrument_key = contract['instrument_key']
                    trading_symbol = contract['trading_symbol']
                    
                    print(f"\nTesting {option_key} ({trading_symbol}):")
                    print(f"   Instrument Key: {instrument_key}")
                    
                    ltp = await self.test_ltp_fetch(instrument_key, option_key)
                    total_tests += 1
                    
                    if ltp is not None:
                        success_count += 1
                        
                        # Additional validation
                        if 5 <= ltp <= 1000:  # Reasonable premium range
                            print(f"   ✅ Valid premium range")
                        else:
                            print(f"   ⚠️ Premium seems unusual: Rs.{ltp:.2f}")
                else:
                    print(f"❌ {option_key}: Not available in current expiry")
        
        # Step 5: Results summary
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        success_rate = (success_count / total_tests * 100) if total_tests > 0 else 0
        
        print(f"✅ Successful LTP fetches: {success_count}/{total_tests} ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            print("🎉 EXCELLENT! Option premium fetching is working well")
            print("👍 Ready to implement in your main bot")
            return True
        elif success_rate >= 50:
            print("⚠️ PARTIAL SUCCESS - Some options working")
            print("🔧 May need fine-tuning for production use")
            return True
        else:
            print("❌ POOR RESULTS - Significant issues remain")
            print("🛠️ Needs debugging before main implementation")
            return False
    
    async def quick_test(self):
        """Quick test - just check if basic functionality works"""
        print("⚡ Quick Option Premium Test")
        print("=" * 40)
        
        if not await self.test_token_validity():
            return False
        
        contracts = await self.fetch_option_contracts()
        
        if contracts:
            # Test first available CE option
            ce_options = [k for k in contracts.keys() if k.endswith('CE')]
            if ce_options:
                first_ce = ce_options[0]
                contract = contracts[first_ce]
                
                print(f"\n💡 Testing first available option: {first_ce}")
                ltp = await self.test_ltp_fetch(contract['instrument_key'], first_ce)
                
                if ltp:
                    print(f"🎉 SUCCESS! Basic option fetching works")
                    print(f"📈 {first_ce} = Rs.{ltp:.2f}")
                    return True
        
        print("❌ Quick test failed")
        return False


# ==================== MAIN EXECUTION ====================

async def main():
    """Main test function"""
    
    # Check if token is configured
    if ACCESS_TOKEN == "YOUR_ACCESS_TOKEN_HERE":
        print("❌ ERROR: Please update ACCESS_TOKEN in the script!")
        print("💡 Get your token from your existing bot authentication")
        return
    
    # Create tester
    tester = OptionPremiumTester(ACCESS_TOKEN)
    
    print("Choose test type:")
    print("1. Quick Test (30 seconds)")
    print("2. Comprehensive Test (2-3 minutes)")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        await tester.quick_test()
    else:
        await tester.run_comprehensive_test()


# ==================== HELPER: GET TOKEN FROM BOT ====================

def extract_token_from_bot():
    """
    Helper function to extract token from your existing bot
    Run this if you don't have the token handy
    """
    try:
        from pathlib import Path
        import json
        
        token_file = Path("data") / "access_token.json"
        
        if token_file.exists():
            with open(token_file, 'r') as f:
                token_data = json.load(f)
                token = token_data.get('access_token')
                
                if token:
                    print(f"Found token: {token[:10]}...{token[-10:]}")
                    return token
        
        print("❌ Token file not found")
        print("💡 Run your main bot once to generate the token")
        
    except Exception as e:
        print(f"Error extracting token: {e}")
    
    return None


# ==================== USAGE INSTRUCTIONS ====================

if __name__ == "__main__":
    print("🧪 Upstox Option Premium Fetching Test")
    print("=" * 50)
    
    # Check if user wants to extract token automatically
    if ACCESS_TOKEN == "YOUR_ACCESS_TOKEN_HERE":
        print("No token configured. Trying to extract from bot...")
        auto_token = extract_token_from_bot()
        
        if auto_token:
            ACCESS_TOKEN = auto_token
            print("✅ Token extracted successfully!")
        else:
            print("\n📝 MANUAL SETUP REQUIRED:")
            print("1. Run your main bot once to authenticate")
            print("2. Copy the access token from logs or data/access_token.json")
            print("3. Update ACCESS_TOKEN variable in this script")
            print("4. Run this test again")
            exit(1)
    
    # Run the test
    asyncio.run(main())


# ==================== EXPECTED OUTPUT ====================
"""
Expected output when working correctly:

🧪 Upstox Option Premium Fetching Test
==================================================
⚡ Quick Option Premium Test
========================================
🔐 Testing access token validity...
✅ Token valid! User: YOUR_USERNAME
📋 Fetching NIFTY option contracts...
✅ Found 234 option contracts for expiry 2025-08-21

💡 Testing first available option: 24900CE
Testing 24900CE:
   Instrument Key: NSE_FO|37590
✅ 24900CE: Rs.125.30
🎉 SUCCESS! Basic option fetching works
📈 24900CE = Rs.125.30

This means your option premium fetching will work in the main bot!
"""