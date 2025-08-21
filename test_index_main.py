# Create: test_index_main.py

#!/usr/bin/env python3
"""
Index Market Testing - Alternative if commodity instruments not available
"""
import os
import sys
import asyncio
from pathlib import Path
import logging

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.trading_bot import TradingBot
from config.settings import get_settings
from config.logging_config import setup_logging

async def index_test_main():
    """Test bot using index data (available even after market hours for validation)"""
    try:
        # Setup logging
        setup_logging()
        logger = logging.getLogger(__name__)
        
        # Load configuration
        settings = get_settings()
        
        logger.info("🧪 INDEX MARKET TESTING - Extended Hours Validation")
        
        # Initialize trading bot
        bot = TradingBot(settings)
        
        # Strategy for testing
        from src.strategy.enhanced_pine_script_strategy import EnhancedPineScriptStrategy
        
        test_strategy = EnhancedPineScriptStrategy("index_test_strategy", {
            'strategy_id': 'Index_Test_Strategy',
            'trading_mode': 'BIDIRECTIONAL',
            'adx_length': 14,
            'adx_threshold': 20,
            'strong_candle_threshold': 0.6,
            'max_positions': 2,
            'total_capital': 20000,
            'max_risk_pct': 0.75,
            'risk_per_trade': 10000
        })
        
        bot.add_strategy(test_strategy)
        
        # Test with multiple indices
        bot.default_instruments = [
            'NSE_INDEX|Nifty 50',      # NIFTY
            'NSE_INDEX|Nifty Bank',    # BANKNIFTY
            'BSE_INDEX|SENSEX',        # SENSEX
            'NSE_INDEX|Nifty Fin Service', # FINNIFTY
        ]
        
        logger.info("🎯 COMPREHENSIVE SYSTEM TEST:")
        logger.info("   📊 Multiple instrument data streams")
        logger.info("   🕯️ Candle formation validation")
        logger.info("   🎯 Strategy logic verification")
        logger.info("   📱 Notification system test")
        logger.info("   ⏰ Market hours control test")
        
        # Run comprehensive test
        await bot.run()
        
    except KeyboardInterrupt:
        print("\n🛑 Index testing stopped by user")
    except Exception as e:
        print(f"❌ Index test error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(index_test_main())