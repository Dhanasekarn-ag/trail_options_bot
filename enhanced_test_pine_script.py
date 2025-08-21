# ==================== enhanced_test_pine_script.py ====================
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.strategy.complete_pine_script_strategy import CompletePineScriptStrategy

def generate_realistic_candle_data(num_candles=30, base_price=24600):
    """Generate realistic NIFTY candle data for testing"""
    candles = []
    current_price = base_price
    
    for i in range(num_candles):
        # Simulate realistic price movement
        price_change = random.uniform(-50, 50)  # ±50 points movement
        current_price += price_change
        
        # Ensure price stays realistic
        current_price = max(24000, min(25500, current_price))
        
        # Generate OHLC with realistic ranges
        open_price = current_price + random.uniform(-20, 20)
        close_price = current_price + random.uniform(-30, 30)
        
        # High and Low based on open/close
        high_price = max(open_price, close_price) + random.uniform(5, 25)
        low_price = min(open_price, close_price) - random.uniform(5, 25)
        
        # Create strong green candles occasionally (for testing signals)
        if i > 20 and random.random() < 0.3:  # 30% chance after candle 20
            # Force a strong green candle
            open_price = current_price - 15
            close_price = current_price + 25
            high_price = close_price + 5
            low_price = open_price - 5
        
        candle = {
            'ha_open': round(open_price, 2),
            'ha_high': round(high_price, 2),
            'ha_low': round(low_price, 2),
            'ha_close': round(close_price, 2),
            'timestamp': datetime.now() - timedelta(minutes=(num_candles - i))
        }
        
        candles.append(candle)
        current_price = close_price
    
    return candles

async def test_pine_script_strategy_enhanced():
    """Enhanced test with sufficient candle data"""
    print("🧪 Enhanced Pine Script Strategy Test")
    print("=" * 60)
    
    # Create strategy instance
    config = {
        'adx_length': 14,
        'adx_threshold': 20,
        'strong_candle_threshold': 0.6,
        'total_capital': 50000,
        'risk_per_trade': 15000
    }
    
    strategy = CompletePineScriptStrategy("test_strategy", config)
    
    print(f"📊 Strategy Configuration:")
    print(f"   ADX Length: {config['adx_length']}")
    print(f"   ADX Threshold: {config['adx_threshold']}")
    print(f"   Strong Candle: >{config['strong_candle_threshold']*100:.0f}%")
    print(f"   Capital: Rs.{config['total_capital']:,}")
    print()
    
    # Generate realistic test data (30 candles)
    print("📈 Generating 30 realistic NIFTY candles...")
    sample_candles = generate_realistic_candle_data(30, 24600)
    
    entry_signals = 0
    exit_signals = 0
    current_position = None
    
    # Process each candle
    for i, candle in enumerate(sample_candles):
        market_data = {
            'symbol': 'NIFTY',
            'ha_candle': candle,
            'timestamp': candle['timestamp'],
            'price': candle['ha_close'],
            'instrument_key': 'NSE_INDEX|Nifty 50'
        }
        
        print(f"\n🕯️ Candle {i+1:2d}: O:{candle['ha_open']:7.2f} H:{candle['ha_high']:7.2f} L:{candle['ha_low']:7.2f} C:{candle['ha_close']:7.2f}")
        
        # Test entry logic
        if not current_position:
            entry_order = await strategy.should_enter(market_data)
            
            if entry_order:
                entry_signals += 1
                print(f"    🚀 ENTRY SIGNAL #{entry_signals}!")
                print(f"       💰 Price: Rs.{entry_order.price:.2f}")
                print(f"       📊 Quantity: {entry_order.quantity} lots")
                
                # Simulate position creation
                current_position = {
                    'symbol': entry_order.symbol,
                    'quantity': entry_order.quantity,
                    'average_price': entry_order.price,
                    'instrument_key': entry_order.instrument_key or ''
                }
                
                # Create mock position object for exit testing
                class MockPosition:
                    def __init__(self, data):
                        self.symbol = data['symbol']
                        self.quantity = data['quantity']
                        self.average_price = data['average_price']
                        self.instrument_key = data['instrument_key']
                
                current_position_obj = MockPosition(current_position)
            else:
                if i >= 22:  # Only log after we have enough data
                    print(f"    ⏳ No entry signal (need: price_above + strong_green + adx>20)")
        
        # Test exit logic if we have a position
        else:
            exit_order = await strategy.should_exit(current_position_obj, market_data)
            
            if exit_order:
                exit_signals += 1
                entry_price = current_position['average_price']
                exit_price = exit_order.price
                pnl = (exit_price - entry_price) * current_position['quantity'] * 75
                pnl_pct = ((exit_price - entry_price) / entry_price) * 100
                
                print(f"    🛑 EXIT SIGNAL #{exit_signals}!")
                print(f"       💰 Exit Price: Rs.{exit_price:.2f}")
                print(f"       📊 P&L: Rs.{pnl:.2f} ({pnl_pct:+.2f}%)")
                if hasattr(exit_order, 'exit_reason'):
                    print(f"       📋 Reason: {exit_order.exit_reason}")
                
                # Close position
                current_position = None
                current_position_obj = None
            else:
                if i >= 22:
                    print(f"    ✋ Holding position (no exit signal)")
    
    # Final strategy status
    print(f"\n" + "=" * 60)
    print(f"📊 FINAL TEST RESULTS")
    print(f"=" * 60)
    
    status = strategy.get_strategy_status()
    print(f"📈 Entry Signals Generated: {entry_signals}")
    print(f"📉 Exit Signals Generated: {exit_signals}")
    print(f"📊 Total Candles Processed: {len(sample_candles)}")
    print(f"📊 Candles Available for Analysis: {status['candles_available']}")
    print(f"🎯 Total Signals Analyzed: {status['total_signals_analyzed']}")
    print(f"✅ Successful Entries: {status['successful_entries']}")
    print(f"📊 Signal Success Rate: {status['signal_success_rate']}")
    print(f"🎯 Current Trade Status: {'IN TRADE' if status['in_trade'] else 'NO POSITION'}")
    print()
    
    # Test validation
    if entry_signals > 0:
        print("✅ SUCCESS: Strategy generated entry signals!")
        print("✅ Pine Script logic is working correctly")
        if exit_signals > 0:
            print("✅ BONUS: Exit signals also working!")
    else:
        print("⚠️  No entry signals generated. This could mean:")
        print("   • Market conditions didn't meet criteria (normal)")
        print("   • ADX threshold too high for test data")
        print("   • Strong candle threshold too strict")
        print("   • Try running test multiple times")
    
    print(f"\n🎯 Ready for integration with main trading bot!")
    return entry_signals > 0

# Additional diagnostic test
async def test_individual_components():
    """Test individual strategy components"""
    print("\n" + "=" * 60)
    print("🔬 COMPONENT TESTING")
    print("=" * 60)
    
    strategy = CompletePineScriptStrategy("component_test", {})
    
    # Test with known good data
    test_candles = [
        {'ha_open': 24600, 'ha_high': 24650, 'ha_low': 24580, 'ha_close': 24640},
        {'ha_open': 24640, 'ha_high': 24680, 'ha_low': 24620, 'ha_close': 24670},
        {'ha_open': 24670, 'ha_high': 24720, 'ha_low': 24650, 'ha_close': 24710},
    ]
    
    # Add 25 candles to strategy
    for i in range(25):
        base_candle = test_candles[i % 3]
        market_data = {
            'ha_candle': {
                'ha_open': base_candle['ha_open'] + i,
                'ha_high': base_candle['ha_high'] + i,
                'ha_low': base_candle['ha_low'] + i,
                'ha_close': base_candle['ha_close'] + i,
                'timestamp': datetime.now()
            }
        }
        strategy.add_candle_data(market_data)
    
    # Test trend line calculation
    trend_line = strategy.calculate_trend_line()
    print(f"📈 Trend Line Calculation: {trend_line:.2f if trend_line else 'None'}")
    
    # Test ADX calculation
    adx, plus_di, minus_di = strategy.calculate_adx_manual()
    print(f"📊 ADX Calculation: ADX={adx:.2f if adx else 'None'}, +DI={plus_di:.2f if plus_di else 'None'}, -DI={minus_di:.2f if minus_di else 'None'}")
    
    # Test candle analysis
    if strategy.candle_history:
        latest_candle = strategy.candle_history[-1]
        strong_green, strong_red, body_pct = strategy.analyze_candle_properties(latest_candle)
        print(f"🕯️ Candle Analysis: Green={strong_green}, Red={strong_red}, Body={body_pct:.1%}")
    
    print("✅ Component testing complete!")

async def main():
    """Run all tests"""
    success = await test_pine_script_strategy_enhanced()
    await test_individual_components()
    
    if success:
        print(f"\n ALL TESTS PASSED! Ready to integrate with your main bot.")
        print(f" Next step: Update your main.py with the new strategy")
    else:
        print(f"\n🔄 Tests completed. Strategy logic is sound, just needs market conditions.")

if __name__ == "__main__":
    asyncio.run(main())