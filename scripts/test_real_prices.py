async def test_real_prices():
    """Test if we're getting real option prices"""
    
    settings = get_settings()
    client = UpstoxClient(
        settings.upstox_api_key,
        settings.upstox_api_secret,
        settings.upstox_redirect_uri
    )
    
    print("=" * 50)
    print("🔍 TESTING REAL OPTION PRICES")
    print("=" * 50)
    
    # ✅ CORRECT INSTRUMENT KEYS FOR AUGUST 14, 2025
    # Format: NSE_FO|NIFTY[YY][W/M][DD]-[STRIKE][CE/PE]
    
    test_cases = [
        ("NSE_FO|NIFTY25814-24600CE", "24600CE"),  # Weekly expiry format
        ("NSE_FO|NIFTY25814-24600PE", "24600PE"),
        ("NSE_FO|NIFTY25814-24500CE", "24500CE"),
        ("NSE_FO|NIFTY25814-24700PE", "24700PE"),
    ]
    
    print(f"📅 Testing NIFTY Options for Aug 14, 2025")
    print(f"📊 Current Date: {datetime.now().strftime('%Y-%m-%d')}")
    print()
    
    for instrument_key, label in test_cases:
        print(f"Testing {label}:")
        print(f"  Instrument: {instrument_key}")
        
        try:
            # Method 1: Try LTP endpoint
            real_price = await client.get_option_ltp(instrument_key)
            
            if real_price and real_price > 0:
                print(f"  ✅ Real Price: Rs.{real_price:.2f}")
            else:
                # Method 2: Try market quote endpoint
                market_data = await client.get_market_data(instrument_key)
                if market_data:
                    print(f"  📊 Market Data: {market_data}")
                else:
                    print(f"  ❌ Failed to get price")
                    
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        print()