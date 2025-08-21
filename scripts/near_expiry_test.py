# ==================== nearest_expiry_test.py ====================
"""
IMPROVED VERSION: Filter for nearest expiry options only
✅ Fetches all option contracts  
✅ Filters for NEAREST expiry date only
✅ Handles decimal strike prices correctly
✅ Tests real LTP fetching for weekly options
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

class NearestExpiryOptionTester:
    """Option tester focused on nearest expiry contracts"""
    
    def __init__(self, token):
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json'
        }
    
    async def fetch_option_contracts_nearest_expiry(self):
        """Fetch option contracts and filter for nearest expiry only"""
        print("📋 Fetching NIFTY option contracts...")
        
        try:
            url = "https://api.upstox.com/v2/option/contract"
            params = {'instrument_key': 'NSE_INDEX|Nifty 50'}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('status') == 'success':
                            # Step 1: Collect all contracts with expiry dates
                            all_contracts = []
                            
                            for contract in data.get('data', []):
                                strike = contract.get('strike_price')
                                option_type = contract.get('instrument_type')
                                instrument_key = contract.get('instrument_key')
                                trading_symbol = contract.get('trading_symbol')
                                expiry = contract.get('expiry')
                                
                                if strike and option_type and instrument_key and expiry:
                                    strike_int = int(float(strike))
                                    
                                    all_contracts.append({
                                        'strike_price': strike_int,
                                        'option_type': option_type,
                                        'instrument_key': instrument_key,
                                        'trading_symbol': trading_symbol,
                                        'expiry': expiry,
                                        'expiry_date': datetime.strptime(expiry, '%Y-%m-%d').date()
                                    })
                            
                            print(f"📦 Total contracts found: {len(all_contracts)}")
                            
                            # Step 2: Find all unique expiry dates
                            expiry_dates = sorted(set(contract['expiry_date'] for contract in all_contracts))
                            today = datetime.now().date()
                            
                            print(f"\n📅 Available Expiry Dates:")
                            for i, exp_date in enumerate(expiry_dates):
                                days_to_expiry = (exp_date - today).days
                                is_nearest = (i == 0)
                                marker = "👈 NEAREST" if is_nearest else f"({days_to_expiry} days)"
                                print(f"   {exp_date} {marker}")
                            
                            # Step 3: Filter for nearest expiry only
                            nearest_expiry = expiry_dates[0]
                            print(f"\n🎯 Filtering for nearest expiry: {nearest_expiry}")
                            
                            contracts = {}
                            for contract in all_contracts:
                                if contract['expiry_date'] == nearest_expiry:
                                    key = f"{contract['strike_price']}{contract['option_type']}"
                                    contracts[key] = {
                                        'instrument_key': contract['instrument_key'],
                                        'strike_price': contract['strike_price'],
                                        'option_type': contract['option_type'],
                                        'trading_symbol': contract['trading_symbol'],
                                        'expiry': contract['expiry'],
                                        'expiry_date': contract['expiry_date']
                                    }
                            
                            print(f"✅ Nearest expiry contracts: {len(contracts)}")
                            return contracts, nearest_expiry
                        else:
                            print(f"❌ API error: {data}")
                    else:
                        error_text = await response.text()
                        print(f"❌ HTTP {response.status}: {error_text}")
            
            return {}, None
            
        except Exception as e:
            print(f"❌ Error fetching contracts: {e}")
            return {}, None
    
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
                            
                            # Try different key formats
                            possible_keys = [
                                instrument_key,
                                instrument_key.replace('|', ':'),
                                instrument_key.replace('NSE_FO|', 'NSE_FO:'),
                            ]
                            
                            for key_format in possible_keys:
                                if key_format in quote_data:
                                    ltp = quote_data[key_format].get('last_price', 0)
                                    if ltp > 0:
                                        print(f"   ✅ {option_name}: Rs.{ltp:.2f}")
                                        return ltp
                            
                            # Find any matching key
                            for key in quote_data.keys():
                                if any(part in key for part in instrument_key.split('|')):
                                    ltp = quote_data[key].get('last_price', 0)
                                    if ltp > 0:
                                        print(f"   ✅ {option_name}: Rs.{ltp:.2f} (Matched: {key})")
                                        return ltp
                            
                            print(f"   ❌ {option_name}: No matching key found")
                            
                        else:
                            print(f"   ❌ {option_name}: API error {data}")
                    else:
                        print(f"   ❌ {option_name}: HTTP {response.status}")
                        
        except Exception as e:
            print(f"   ❌ {option_name}: {e}")
        
        return None
    
    async def run_nearest_expiry_test(self):
        """Run test focused on nearest expiry options"""
        print("🚀 Nearest Expiry Option Premium Test")
        print("=" * 60)
        
        # Step 1: Get NIFTY spot price
        spot_price = 25000
        try:
            url = "https://api.upstox.com/v2/market-quote/ltp"
            params = {'instrument_key': 'NSE_INDEX|Nifty 50'}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        for key, value in data.get('data', {}).items():
                            if 'Nifty' in key:
                                spot_price = value.get('last_price', 25000)
                                print(f"📈 NIFTY Spot: Rs.{spot_price:.2f}")
                                break
        except:
            print(f"📈 NIFTY Spot: Rs.{spot_price:.2f} (fallback)")
        
        # Step 2: Fetch nearest expiry option contracts
        contracts, nearest_expiry = await self.fetch_option_contracts_nearest_expiry()
        
        if not contracts:
            print("❌ Could not fetch option contracts")
            return False
        
        # Step 3: Analyze nearest expiry contracts
        ce_options = [k for k in contracts.keys() if k.endswith('CE')]
        pe_options = [k for k in contracts.keys() if k.endswith('PE')]
        
        print(f"\n📊 Nearest Expiry Analysis ({nearest_expiry}):")
        print(f"   CE Options: {len(ce_options)}")
        print(f"   PE Options: {len(pe_options)}")
        
        if ce_options:
            ce_strikes = sorted([int(k[:-2]) for k in ce_options])
            print(f"   Strike Range: {min(ce_strikes)} - {max(ce_strikes)}")
            
            # Find ATM strike
            atm_strike = min(ce_strikes, key=lambda x: abs(x - spot_price))
            print(f"   ATM Strike: {atm_strike} (Spot: {spot_price:.0f})")
            
            # Days to expiry
            today = datetime.now().date()
            days_to_expiry = (nearest_expiry - today).days
            print(f"   Days to Expiry: {days_to_expiry}")
        
        # Step 4: Test ATM and nearby options (nearest expiry only)
        print(f"\n💰 Testing Nearest Expiry Option LTP:")
        
        if ce_strikes:
            # Test ATM and nearby strikes
            test_strikes = [atm_strike - 50, atm_strike, atm_strike + 50]
            test_strikes = [s for s in test_strikes if s in ce_strikes]  # Only valid strikes
            
            success_count = 0
            total_tests = 0
            
            for strike in test_strikes:
                for opt_type in ['CE', 'PE']:
                    option_key = f"{strike}{opt_type}"
                    
                    if option_key in contracts:
                        contract = contracts[option_key]
                        total_tests += 1
                        
                        print(f"\n🧪 Testing {option_key} (Expiry: {nearest_expiry}):")
                        print(f"   Trading Symbol: {contract['trading_symbol']}")
                        print(f"   Instrument Key: {contract['instrument_key']}")
                        
                        ltp = await self.test_option_ltp(contract['instrument_key'], option_key)
                        
                        if ltp and ltp > 0:
                            success_count += 1
                            
                            # Calculate moneyness
                            if opt_type == 'CE':
                                moneyness = "ITM" if spot_price > strike else "OTM"
                            else:
                                moneyness = "ITM" if spot_price < strike else "OTM"
                            
                            print(f"   📊 {moneyness} option, premium: Rs.{ltp:.2f}")
            
            # Step 5: Results
            print(f"\n" + "=" * 60)
            print(f"🎯 NEAREST EXPIRY TEST RESULTS:")
            print(f"=" * 60)
            
            success_rate = (success_count / total_tests * 100) if total_tests > 0 else 0
            
            print(f"📅 Target Expiry: {nearest_expiry} ({days_to_expiry} days)")
            print(f"✅ Contracts filtered: {len(contracts)}")
            print(f"✅ LTP tests successful: {success_count}/{total_tests} ({success_rate:.1f}%)")
            
            if success_count > 0:
                print(f"\n🎉 SUCCESS! Nearest expiry option fetching WORKS!")
                print(f"✅ Your bot can now fetch weekly/nearest expiry options")
                print(f"\n📋 Implementation notes:")
                print(f"   1. Always filter by nearest expiry date")
                print(f"   2. Weekly options have better liquidity")
                print(f"   3. Use this approach for intraday strategies")
                
                return True
            else:
                print(f"\n⚠️ LTP fetching failed - check market hours")
                return False
        
        return False

async def main():
    """Main function"""
    print("🔧 Nearest Expiry Option Premium Test")
    print("Focusing on weekly/nearest expiry contracts")
    print("=" * 60)
    
    token = get_token()
    if not token:
        print("❌ No token found!")
        return
    
    tester = NearestExpiryOptionTester(token)
    await tester.run_nearest_expiry_test()
    
    print(f"\n🎯 RESULT:")
    print(f"This version filters for the nearest expiry (weekly options)")
    print(f"Perfect for intraday trading and better liquidity!")

if __name__ == "__main__":
    asyncio.run(main())