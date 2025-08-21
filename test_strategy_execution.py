# Create: test_strategy_execution.py

import asyncio
import logging
from src.trading_bot import TradingBot
from config.settings import get_settings
from src.strategy.pine_script_strategy import PineScriptStrategy

async def test_strategy_execution():
    """Test if strategy execution works after 15 candles"""
    
    # Setup logging to see detailed output
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("🧪 Testing Strategy Execution Fix...")
    
    try:
        # Load settings
        settings = get_settings()
        
        # Create bot
        bot = TradingBot(settings)
        
        # Add a test strategy
        strategy = PineScriptStrategy("test_strategy", {
            'adx_length': 14,
            'adx_threshold': 20,
            'strong_candle_threshold': 0.6,
            'total_capital': 20000,
            'max_risk_pct': 0.75,
            'risk_per_trade': 5000
        })
        bot.add_strategy(strategy)
        
        logger.info(f"✅ Strategy added: {strategy.name}")
        logger.info(f"✅ Strategy is active: {strategy.is_active}")
        
        # Test the HA candle processing method directly
        logger.info("🧪 Testing HA candle processing...")
        
        # Create a mock HA candle with 15 candles history
        mock_ha_candles = []
        for i in range(15):
            mock_ha_candles.append({
                'ha_open': 25000 + i,
                'ha_high': 25020 + i,
                'ha_low': 24990 + i,
                'ha_close': 25010 + i,
                'volume': 1000,
                'timestamp': f"candle_{i}"
            })
        
        mock_ha_candle = {
            'symbol': 'NIFTY',
            'ha_open': 25015.0,
            'ha_high': 25025.0,
            'ha_low': 25005.0,
            'ha_close': 25020.0,
            'volume': 1000,
            'candle_history': mock_ha_candles
        }
        
        logger.info("🚀 Simulating HA candle received with 15 candles...")
        
        # Test the callback method directly
        await bot.on_ha_candle_received(mock_ha_candle)
        
        logger.info("✅ Strategy execution test completed!")
        logger.info("📊 Check the logs above for:")
        logger.info("   - 'STRATEGY READY - NIFTY has 15 candles'")
        logger.info("   - 'EXECUTING STRATEGIES for NIFTY'")
        logger.info("   - 'Checking strategy 1/1: test_strategy'")
        logger.info("   - Strategy analysis results")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_strategy_execution())