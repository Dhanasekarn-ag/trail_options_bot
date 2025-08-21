# ==================== test_pine_script.py ====================
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.strategy.complete_pine_script_strategy import CompletePineScriptStrategy

async def test_pine_script_strategy():
    """Test Pine Script strategy with sample data"""
    print("🧪 Testing Pine Script Strategy Implementation")
    print("=" * 50)
    
    # Create strategy instance
    config = {
        'adx_length': 14,
        'adx_threshold': 20,
        'strong_candle_threshold': 0.6,
        'total_capital': 50000,
        'risk_per_trade': 15000
    }
    
    strategy = CompletePineScriptStrategy("test_strategy", config)
    
    # Test with sample Heikin Ashi candle data
    sample_candles = [
        {'ha_open': 24600, 'ha_high': 24650, 'ha_low': 24580, 'ha_close': 24640, 'timestamp': datetime.now()},
        {'ha_open': 24640, 'ha_high': 24680, 'ha_low': 24620, 'ha_close': 24670, 'timestamp': datetime.now()},
        {'ha_open': 24670, 'ha_high': 24720, 'ha_low': 24650, 'ha_close': 24710, 'timestamp': datetime.now()},
        # Add more sample candles...
    ]
    
    # Test candle analysis
    for i, candle in enumerate(sample_candles):
        market_data = {
            'symbol': 'NIFTY',
            'ha_candle': candle,
            'timestamp': datetime.now(),
            'price': candle['ha_close']
        }
        
        # Test strategy logic
        entry_order = await strategy.should_enter(market_data)
        
        if entry_order:
            print(f"✅ Entry signal detected on candle {i+1}")
            print(f"   Price: Rs.{entry_order.price:.2f}")
            print(f"   Quantity: {entry_order.quantity} lots")
        else:
            print(f"⏳ No entry signal on candle {i+1}")
    
    # Test strategy status
    status = strategy.get_strategy_status()
    print(f"\n📊 Strategy Status:")
    for key, value in status.items():
        print(f"   {key}: {value}")

if __name__ == "__main__":
    asyncio.run(test_pine_script_strategy())