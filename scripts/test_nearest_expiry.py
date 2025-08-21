# ==================== test_nearest_expiry.py ====================
"""
Quick test to verify nearest expiry selection logic
Run this to see which expiry will be selected for your trading
"""

import asyncio
import aiohttp
import json
from pathlib import Path
from datetime import datetime

def get_token():
    try:
        token_file = Path("data") / "access_token.json"
        with open(token_file, 'r') as f:
            return json.load(f).get('access_token')
    except:
        return None

async def test_expiry_selection():
    """Test which expiry will be selected for trading"""
    
    token = get_token()
    if not token:
        print("❌ No token found!")
        return
    
    print("🗓️ Testing Expiry Selection for Intraday Trading")
    print("=" * 60)
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json'
    }
    
    # Get all available expiries
    print("📋 Fetching all available NIFTY option expiries...")
    
    try:
        url = "https://api.upstox.com/v2/option/contract"
        params = {'instrument_key': 'NSE_INDEX|Nifty 50'}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('status') == 'success':
                        # Extract unique expiries
                        expiries = set()
                        for contract in data.get('data', []):
                            expiry = contract.get('expiry')
                            if expiry:
                                expiries.add(expiry)
                        
                        sorted_expiries = sorted(list(expiries))
                        
                        print(f"✅ Found {len(sorted_expiries)} available expiry dates:")
                        for i, expiry in enumerate(sorted_expiries, 1):
                            expiry_date = datetime.strptime(expiry, '%Y-%m-%d').date()
                            current_date = datetime.now().date()
                            days_diff = (expiry_date - current_date).days
                            
                            if days_diff == 0:
                                status = "🚨 TODAY (Expiry day!)"
                            elif days_diff < 0:
                                status = f"❌ EXPIRED ({abs(days_diff)} days ago)"
                            elif days_diff <= 7:
                                status = f"⭐ WEEKLY ({days_diff} days) - IDEAL for intraday"
                            else:
                                status = f"📅 FUTURE ({days_diff} days)"
                            
                            print(f"   {i}. {expiry} - {status}")
                        
                        # Determine which one would be selected
                        print(f"\n🎯 EXPIRY SELECTION LOGIC:")
                        current_time = datetime.now()
                        current_hour = current_time.hour
                        
                        # Check if today is expiry
                        today_expiry = None
                        for expiry in sorted_expiries:
                            expiry_date = datetime.strptime(expiry, '%Y-%m-%d').date()
                            if expiry_date == current_time.date():
                                today_expiry = expiry
                                break
                        
                        if today_expiry and current_hour < 15:
                            selected_expiry = today_expiry
                            reason = f"Today is expiry day and market is open (current: {current_hour}:xx)"
                            print(f"✅ SELECTED: {selected_expiry}")
                            print(f"📝 REASON: {reason}")
                        else:
                            # Find nearest future expiry
                            future_expiries = []
                            for expiry in sorted_expiries:
                                expiry_date = datetime.strptime(expiry, '%Y-%m-%d').date()
                                if expiry_date > current_time.date():
                                    future_expiries.append(expiry)
                            
                            if future_expiries:
                                selected_expiry = future_expiries[0]
                                expiry_date = datetime.strptime(selected_expiry, '%Y-%m-%d').date()
                                days_to_expiry = (expiry_date - current_time.date()).days
                                
                                print(f"✅ SELECTED: {selected_expiry}")
                                print(f"📝 REASON: Nearest future expiry ({days_to_expiry} days away)")
                                
                                if days_to_expiry <= 7:
                                    print(f"⭐ EXCELLENT: Weekly expiry - perfect for intraday trading!")
                                else:
                                    print(f"⚠️ WARNING: Monthly expiry - higher premiums, lower liquidity")
                            else:
                                print(f"❌ ERROR: No future expiries available!")
                                return
                        
                        # Test contract count for selected expiry
                        print(f"\n📊 Testing contract availability for {selected_expiry}...")
                        
                        params_specific = {
                            'instrument_key': 'NSE_INDEX|Nifty 50',
                            'expiry': selected_expiry
                        }
                        
                        async with session.get(url, headers=headers, params=params_specific) as response2:
                            if response2.status == 200:
                                data2 = await response2.json()
                                
                                if data2.get('status') == 'success':
                                    contracts = data2.get('data', [])
                                    ce_count = len([c for c in contracts if c.get('instrument_type') == 'CE'])
                                    pe_count = len([c for c in contracts if c.get('instrument_type') == 'PE'])
                                    
                                    strikes = set()
                                    for contract in contracts:
                                        strike = contract.get('strike_price')
                                        if strike:
                                            strikes.add(int(float(strike)))
                                    
                                    strike_list = sorted(list(strikes))
                                    
                                    print(f"✅ Found {len(contracts)} contracts for {selected_expiry}")
                                    print(f"   📈 {ce_count} CE options")
                                    print(f"   📉 {pe_count} PE options") 
                                    print(f"   🎯 Strike range: {min(strike_list)} - {max(strike_list)}")
                                    
                                    # Show strikes around current spot
                                    spot_price = 25009  # Approximate
                                    nearby_strikes = [s for s in strike_list if abs(s - spot_price) <= 200]
                                    print(f"   🎯 Nearby strikes: {nearby_strikes}")
                                    
                                    print(f"\n🎉 PERFECT! Ready for intraday option trading with {selected_expiry}")
                                    
                                else:
                                    print(f"❌ Error getting contracts: {data2}")
                            else:
                                print(f"❌ HTTP error: {response2.status}")
                
                else:
                    print(f"❌ API Error: {response.status}")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print(f"\n💡 RECOMMENDATION:")
    print(f"   For intraday trading, always use the nearest weekly expiry")
    print(f"   This gives you:")
    print(f"   ✅ Lower option premiums (less time value)")
    print(f"   ✅ Higher liquidity (more traders)")
    print(f"   ✅ Faster price movements")
    print(f"   ✅ Lower capital requirement")

if __name__ == "__main__":
    asyncio.run(test_expiry_selection())