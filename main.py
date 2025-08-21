import asyncio
import logging
from pathlib import Path
import sys
from datetime import datetime
import os
os.environ['PYTHONIOENCODING'] = 'utf-8:replace'

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.trading_bot import TradingBot
from config.settings import get_settings
from config.logging_config import setup_logging

async def main():
    """Enhanced main function with Option-Integrated Pine Script Strategy"""
    try:
        # Setup logging
        setup_logging()
        logger = logging.getLogger(__name__)
        
        # Load configuration
        settings = get_settings()
        
        logger.info("🚀 Starting AstraRise Trading Bot - Option-Integrated Pine Script V5")
        logger.info(f"💰 Capital: Rs.50,000 | Max per trade: Rs.15,000")
        
        # Initialize enhanced trading bot
        bot = TradingBot(settings)
        
        # ✅ Import the option-integrated strategy
        from src.strategy.option_integrated_pine_script import OptionIntegratedPineScript
        from src.options.option_chain_manager import OptionChainManager
        bot.option_chain_manager = OptionChainManager(bot.upstox_client)
        
        
        # ✅ SINGLE COMPREHENSIVE CONFIG (combine both configs)
        option_pine_config = {
            'strategy_id': 'OptionIntegratedPineScript_V5_Live',
            'trading_mode': 'OPTION_TRADING',
            
            # ✅ Pine Script Parameters
            'adx_length': 14,
            'adx_threshold': 20,
            'strong_candle_threshold': 0.6,
            
            # ✅ Capital Management
            'total_capital': 50000,
            'risk_per_trade': 15000,
            'max_positions': 1,  # One trade at a time like Pine Script
            
            # ✅ Option Trading Configuration
            'option_trading_enabled': True,
            'strike_selection_mode': 'ATM',  # ATM, OTM, ITM
            'max_option_premium': 200,       # Max Rs.200 per share
            'min_option_premium': 10,        # Min Rs.10 per share
            
            # ✅ Advanced Features Configuration
            'enable_premium_monitoring': True,
            'monitoring_interval': 30,        # Monitor every 30 seconds
            'profit_target_pct': 50,         # 50% profit target
            'stop_loss_pct': 30,             # 30% stop loss
            'trailing_stop_enabled': True,
            'trail_activation_pct': 25,      # Start trailing at 25% profit
            'trail_step_pct': 10,            # Trail by 10%
            
            # ✅ Symbol Configuration
            'allowed_symbols': ['NIFTY'],
            'lot_sizes': {'NIFTY': 75},
            
            # ✅ Time Management
            'trading_start_time': '09:30',
            'no_entry_after': '15:10',
            'auto_square_off_time': '15:20',
        }
        
        # ✅ Create and add the option-integrated strategy
        option_strategy = OptionIntegratedPineScript("option_pine_v5", option_pine_config)
        
        # ✅ CRITICAL: Set Upstox client for real option pricing
        option_strategy.set_upstox_client(bot.upstox_client)
        
        # 🚨 ADD THIS LINE - This is what's missing:
        option_strategy.option_chain_manager = bot.option_chain_manager
        
        # ✅ Add strategy to bot
        bot.add_strategy(option_strategy)
        
        # ✅ Log successful configuration
        logger.info("🎯 Option-Integrated Pine Script V5 Strategy Loaded!")
        logger.info("📊 Features: Pine Script + Real Option Trading + Advanced Monitoring")
        logger.info("🔄 Uptrend → CE options | Downtrend → PE options")
        logger.info("💰 Premium Range: Rs.10-200 per share")
        logger.info("🎯 Profit Target: 50% | Stop Loss: 30% | Trailing Stop: Active")
        logger.info("🔍 Real-time Monitoring: Every 30 seconds")
        
        # Run the enhanced bot
        await bot.run()
        
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        # Print detailed error for debugging
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    asyncio.run(main())