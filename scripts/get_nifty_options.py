#!/usr/bin/env python3
"""Get NIFTY option instrument keys from Upstox"""
import asyncio
import aiohttp
import json
import csv
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

async def download_instruments():
    """Download and parse instruments file from Upstox"""
    
    print("📥 Downloading Upstox Instruments File...")
    print("=" * 50)
    
    # Upstox provides daily instrument file
    # Format: https://assets.upstox.com/market-quote/instruments/exchange/NSE_FO.csv
    
    async with aiohttp.ClientSession() as session:
        # Download NSE F&O instruments
        url = "https://assets.upstox.com/market-quote/instruments/exchange/NSE_FO.csv"
        
        print(f"Downloading from: {url}")
        
        async with session.get(url) as response:
            if response.status == 200:
                content = await response.text()
                
                # Save to file
                instruments_file = Path("data/nse_fo_instruments.csv")
                instruments_file.parent.mkdir(exist_ok=True)
                
                with open(instruments_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"✅ Saved to: {instruments_file}")
                
                # Parse and find NIFTY options
                return parse_nifty_options(instruments_file)
            else:
                print(f"❌ Failed to download: {response.status}")
                return None

def parse_nifty_options(file_path):
    """Parse the instruments file and find NIFTY options"""
    
    print("\n🔍 Searching for NIFTY Options...")
    print("=" * 50)
    
    try:
        # Read CSV file
        df = pd.read_csv(file_path)
        
        # Print column names to understand structure
        print(f"Columns found: {df.columns.tolist()}")
        
        # Filter for NIFTY options
        # Look for NIFTY in name/symbol columns
        nifty_options = df[
            df.apply(lambda row: 'NIFTY' in str(row.values), axis=1)
        ]
        
        # Get current/next Thursday for weekly expiry
        today = datetime.now()
        days_until_thursday = (3 - today.weekday()) % 7
        if days_until_thursday == 0 and today.hour >= 15:
            days_until_thursday = 7
        next_thursday = today + timedelta(days=days_until_thursday)
        expiry_date = next_thursday.strftime('%Y-%m-%d')
        
        print(f"\n📅 Looking for expiry around: {expiry_date}")
        
        # Find options with strikes around current price (24600)
        strikes_to_find = [24500, 24550, 24600, 24650, 24700]
        
        found_options = []
        
        print("\n📊 NIFTY Options Found:")
        print("-" * 80)
        
        for idx, row in nifty_options.head(100).iterrows():
            row_str = str(row.values)
            
            # Check if this is an option (has CE or PE)
            if 'CE' in row_str or 'PE' in row_str:
                # Try to find instrument key column
                for col in ['instrument_key', 'instrumentKey', 'trading_symbol', 'tradingsymbol', 'symbol']:
                    if col in df.columns:
                        instrument_key = row[col]
                        
                        # Check if it matches our strikes
                        for strike in strikes_to_find:
                            if str(strike) in str(instrument_key):
                                found_options.append({
                                    'instrument_key': instrument_key,
                                    'name': row.get('name', ''),
                                    'lot_size': row.get('lot_size', ''),
                                    'strike': strike
                                })
                                
                                if len(found_options) <= 10:  # Show first 10
                                    print(f"Strike {strike}: {instrument_key}")
                                break
                        break
        
        # Save found options
        if found_options:
            output_file = Path("data/nifty_options_keys.json")
            with open(output_file, 'w') as f:
                json.dump(found_options, f, indent=2)
            
            print(f"\n✅ Found {len(found_options)} options")
            print(f"📁 Saved to: {output_file}")
            
            return found_options
        else:
            print("\n❌ No NIFTY options found in expected format")
            
            # Show sample rows for debugging
            print("\n📋 Sample rows from file:")
            for idx, row in nifty_options.head(5).iterrows():
                print(f"  {row.to_dict()}")
            
    except Exception as e:
        print(f"❌ Error parsing file: {e}")
        return None

async def test_found_options():
    """Test the found option keys"""
    
    options_file = Path("data/nifty_options_keys.json")
    if not options_file.exists():
        print("❌ No options file found. Run download first.")
        return
    
    with open(options_file) as f:
        options = json.load(f)
    
    if not options:
        return
    
    # Load access token
    token_file = Path("data/access_token.json")
    with open(token_file) as f:
        token_data = json.load(f)
        access_token = token_data.get('access_token')
    
    print("\n🧪 Testing Found Option Keys...")
    print("=" * 50)
    
    base_url = "https://api.upstox.com/v2"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }
    
    async with aiohttp.ClientSession() as session:
        # Test first 3 options
        for option in options[:3]:
            instrument_key = option['instrument_key']
            print(f"\nTesting: {instrument_key}")
            
            url = f"{base_url}/market-quote/ltp?symbol={instrument_key}"
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Success: {data}")
                else:
                    print(f"❌ Failed: {response.status}")

async def main():
    """Main function"""
    
    print("🚀 NIFTY OPTIONS INSTRUMENT KEY FINDER")
    print("=" * 50)
    
    # Step 1: Download instruments
    options = await download_instruments()
    
    if options:
        # Step 2: Test the found options
        await test_found_options()
    
    print("\n✅ Complete!")
    
    # Show how to use in strategy
    print("\n📝 To use in your strategy:")
    print("1. Check data/nifty_options_keys.json for instrument keys")
    print("2. Update your strategy to use these exact keys")
    print("3. Example: NSE_FO|<actual_key_from_file>")

if __name__ == "__main__":
    asyncio.run(main())