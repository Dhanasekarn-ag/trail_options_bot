# ==================== test_option_integration.py ====================
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent / "src"))

from src.strategy.option_integrated_pine_script import OptionIntegratedPineScript

async def test_option_integration():
    """Test option integration without real trading"""
    print("🧪 Testing Option Integration")
    print("=" * 50)
    
    # Create strategy
    config = {
        'option_trading_enabled': True,
        'strike_selection_mode': 'ATM',
        'max_option_premium': 200,
        'min_option_premium': 10
    }
    
    strategy = OptionIntegratedPineScript("test_option", config)
    
    # Test strike calculation
    spot_prices = [24978, 24923, 25045, 24867]
    
    for spot in spot_prices:
        print(f"\n💰 NIFTY Spot: Rs.{spot:.2f}")
        
        # Test CE strike
        ce_strike = strategy.calculate_option_strike(spot, 'CE', 'ATM')
        print(f"   📈 Uptrend → {ce_strike}CE")
        
        # Test PE strike  
        pe_strike = strategy.calculate_option_strike(spot, 'PE', 'ATM')
        print(f"   📉 Downtrend → {pe_strike}PE")
        
        # Test option symbol generation
        ce_symbol = strategy.get_option_symbol(ce_strike, 'CE')
        pe_symbol = strategy.get_option_symbol(pe_strike, 'PE')
        print(f"   🏷️ Symbols: {ce_symbol}, {pe_symbol}")
    
    print("\n✅ Option integration tests completed!")

if __name__ == "__main__":
    asyncio.run(test_option_integration())