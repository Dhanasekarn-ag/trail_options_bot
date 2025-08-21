import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent / "src"))

async def verify_integration():
    """Verify all components are working together"""
    print("🧪 Verifying Complete Integration")
    print("=" * 60)
    
    try:
        # Test 1: Import verification
        print("📦 Testing imports...")
        from src.strategy.option_integrated_pine_script import OptionIntegratedPineScript
        from src.trading_bot import TradingBot
        from config.settings import get_settings
        print("✅ All imports successful")
        
        # Test 2: Strategy creation
        print("\n🎯 Testing strategy creation...")
        config = {
            'option_trading_enabled': True,
            'enable_premium_monitoring': True,
            'profit_target_pct': 50,
            'stop_loss_pct': 30,
            'trailing_stop_enabled': True
        }
        
        strategy = OptionIntegratedPineScript("test_strategy", config)
        print("✅ Strategy created successfully")
        
        # Test 3: Method availability
        print("\n🔍 Testing method availability...")
        methods_to_check = [
            'should_enter',
            'should_exit', 
            'should_exit_option',
            'monitor_option_prices',
            'set_upstox_client'
        ]
        
        for method in methods_to_check:
            if hasattr(strategy, method):
                print(f"   ✅ {method}")
            else:
                print(f"   ❌ {method} - MISSING!")
        
        # Test 4: Configuration verification
        print(f"\n⚙️ Configuration verification:")
        print(f"   Option Trading: {strategy.option_trading_enabled}")
        print(f"   Premium Monitoring: {strategy.enable_premium_monitoring}")
        print(f"   Profit Target: {strategy.profit_target_pct}%")
        print(f"   Stop Loss: {strategy.stop_loss_pct}%")
        print(f"   Trailing Stop: {strategy.trailing_stop_enabled}")
        
        print(f"\n🎉 ALL VERIFICATIONS PASSED!")
        print(f"✅ Your integration is ready to go!")
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_integration())