# Create this file: test_market_hours.py
# Save it in your main directory (same level as main.py)

from src.websocket.websocket_manager import MarketHoursChecker
import logging

logging.basicConfig(level=logging.INFO)

print("🧪 Testing Market Hours Checker...")

try:
    checker = MarketHoursChecker()
    status = checker.get_market_status()
    
    print(f"📊 Current Status: {status['status']}")
    print(f"💬 Message: {status['message']}")
    print(f"⏰ Current Time: {status['current_time']}")
    
    if status['status'] == 'CLOSED':
        print("✅ GOOD: Market is closed, candle formation will be stopped")
        print(f"📅 Next Open: {status.get('next_open', 'Check tomorrow')}")
    else:
        print("✅ GOOD: Market is open, candle formation will continue")
        
    # Also test the basic is_market_open method
    is_open = checker.is_market_open()
    print(f"🔍 is_market_open(): {is_open}")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    print("Make sure you've updated websocket_manager.py with the MarketHoursChecker class")