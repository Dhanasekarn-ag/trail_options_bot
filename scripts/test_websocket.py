#!/usr/bin/env python3
"""
Test WebSocket functionality
"""
import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

async def test_websocket_import():
    """Test if websocket components can be imported"""
    print("🔍 Testing WebSocket imports...")
    
    try:
        # Test Upstox SDK
        import upstox_client
        print("✅ upstox-python-sdk: OK")
        
        # Test protobuf
        import google.protobuf
        print("✅ protobuf: OK")
        
        # Test websocket client
        import websocket
        print("✅ websocket-client: OK")
        
        # Test our websocket manager
        from src.websocket.websocket_manager import WebSocketManager, CandleAggregator, HeikinAshiConverter
        print("✅ WebSocket Manager: OK")
        print("✅ Candle Aggregator: OK") 
        print("✅ Heikin Ashi Converter: OK")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

async def test_candle_aggregator():
    """Test candle aggregation functionality"""
    print("\n🔍 Testing Candle Aggregator...")
    
    try:
        from src.websocket.websocket_manager import CandleAggregator
        
        aggregator = CandleAggregator(timeframe_minutes=3)
        
        # Simulate some ticks
        tick_data = {
            'ltp': 100.50,
            'volume': 1000
        }
        
        result = aggregator.process_tick("TEST", tick_data)
        print("✅ Candle Aggregator: Processing ticks OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Candle Aggregator test failed: {e}")
        return False

async def test_heikin_ashi():
    """Test Heikin Ashi conversion"""
    print("\n🔍 Testing Heikin Ashi Converter...")
    
    try:
        from src.websocket.websocket_manager import HeikinAshiConverter
        
        converter = HeikinAshiConverter()
        
        # Test candle
        candle = {
            'open': 100,
            'high': 105,
            'low': 98,
            'close': 102,
            'volume': 1000
        }
        
        ha_candle = converter.convert_candle("TEST", candle)
        
        if 'ha_open' in ha_candle and 'ha_close' in ha_candle:
            print("✅ Heikin Ashi Converter: Conversion OK")
            return True
        else:
            print("❌ Heikin Ashi Converter: Missing HA values")
            return False
            
    except Exception as e:
        print(f"❌ Heikin Ashi test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🧪 WebSocket Functionality Test Suite")
    print("="*40)
    
    tests = [
        ("Import Test", test_websocket_import),
        ("Candle Aggregator Test", test_candle_aggregator), 
        ("Heikin Ashi Test", test_heikin_ashi)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        try:
            if await test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
    
    print("\n" + "="*40)
    print(f"🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! WebSocket functionality is ready.")
        print("\n🚀 Next steps:")
        print("   1. Run: python main.py")
        print("   2. Your bot will use real-time data streams")
        print("   3. 3-minute Heikin Ashi candles will trigger your strategy")
    else:
        print("❌ Some tests failed. Please check the installation.")
        print("   Try running: python scripts/install_websocket_deps.py")

if __name__ == "__main__":
    asyncio.run(main())