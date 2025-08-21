# ==================== src/utils/notification.py (FIXED) ====================
import asyncio
import logging
from typing import Optional, List
import aiohttp
from datetime import datetime

class TelegramNotifier:
    """Telegram notification service with support for multiple chats"""
    
    def __init__(self, bot_token: Optional[str], chat_id: Optional[str], enabled: bool = True):
        self.bot_token = bot_token
        
        # Handle multiple chat IDs separated by comma
        if chat_id:
            # Split by comma and clean up whitespace
            self.chat_ids = [id.strip() for id in str(chat_id).split(',') if id.strip()]
        else:
            self.chat_ids = []
        
        self.enabled = enabled and bot_token and self.chat_ids
        self.logger = logging.getLogger(__name__)
        
        if not self.enabled:
            self.logger.warning("Telegram notifications disabled - missing token or chat_id")
        else:
            self.logger.info(f"Telegram enabled for {len(self.chat_ids)} chats: {self.chat_ids}")
    
    async def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """Send message to all configured Telegram chats"""
        if not self.enabled:
            return False
        
        success_count = 0
        
        # Send to all chat IDs
        for chat_id in self.chat_ids:
            if await self._send_to_single_chat(chat_id, message, parse_mode):
                success_count += 1
        
        # Return True if at least one message was sent successfully
        return success_count > 0
    
    async def _send_to_single_chat(self, chat_id: str, message: str, parse_mode: str = "HTML") -> bool:
        """Send message to a single chat"""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': parse_mode
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        self.logger.debug(f"Telegram message sent successfully to {chat_id}")
                        return True
                    else:
                        self.logger.error(f"Failed to send Telegram message to {chat_id}: {response.status}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Error sending Telegram message to {chat_id}: {e}")
            return False
    
    async def send_trade_alert(self, action: str, symbol: str, quantity: int, price: float, order_type: str):
        """Send enhanced trade alert with better formatting"""
        
        # Determine emoji based on action
        action_emoji = "🚀" if "BUY" in action.upper() else "🛑"
        
        message = f"""
{action_emoji} <b>AstraRise Trading Bot</b>

📊 <b>Action:</b> {action}
📈 <b>Symbol:</b> {symbol}
🔢 <b>Quantity:</b> {quantity} lots
💰 <b>Price:</b> Rs.{price:.2f}
📋 <b>Order Type:</b> {order_type}

⏰ <b>Time:</b> {datetime.now().strftime('%I:%M:%S %p')}
🗓️ <b>Date:</b> {datetime.now().strftime('%B %d, %Y')}

Good luck! 🎯
        """
        await self.send_message(message)
    
    async def send_enhanced_trade_alert(self, action: str, symbol: str, quantity: int, 
                                      price: float, investment: float, capital_used: float, 
                                      remaining_capital: float):
        """Send enhanced trade alert with capital management details"""
        
        action_emoji = "🚀" if "BUY" in action.upper() else "🛑"
        lot_size = 75
        total_shares = quantity * lot_size
        
        message = f"""
{action_emoji} <b>{action} SIGNAL - AstraRise Bot</b>

📊 <b>NIFTY Analysis:</b> Pine Script Signal
🎯 <b>Strategy:</b> Trend + Strong Candle + ADX &gt; 20

💰 <b>PAPER TRADE EXECUTED:</b>
🔹 <b>Symbol:</b> {symbol}
🔹 <b>Action:</b> {action} {quantity} lots ({total_shares:,} shares)
🔹 <b>Price:</b> Rs.{price:.2f} per share
🔹 <b>Investment:</b> Rs.{investment:,.2f}

📈 <b>Capital Management:</b>
💵 Total Capital: Rs.{50000 + capital_used:,.2f}
💸 Used: Rs.{investment:,.2f} ({(investment/(50000 + capital_used))*100:.1f}%)
💰 Remaining: Rs.{remaining_capital:,.2f}

⏰ <b>Time:</b> {datetime.now().strftime('%I:%M:%S %p')}
🗓️ <b>Date:</b> {datetime.now().strftime('%B %d, %Y')}

Pine Script in action! 🎯
        """
        await self.send_message(message)
    
    async def send_pnl_alert(self, symbol: str, pnl: float, entry_price: float, 
                           exit_price: float, quantity: int, total_trades: int, 
                           winning_trades: int, total_pnl: float):
        """Send P&L alert with performance tracking"""
        
        lot_size = 75
        total_shares = quantity * lot_size
        trade_value = entry_price * total_shares
        pnl_pct = (pnl / trade_value) * 100 if trade_value > 0 else 0
        
        status_emoji = "🟢" if pnl > 0 else "🔴"
        status_text = "PROFIT" if pnl > 0 else "LOSS"
        
        win_rate = (winning_trades / max(1, total_trades)) * 100
        
        message = f"""
📊 <b>TRADE COMPLETED - AstraRise Bot</b>

{status_emoji} <b>{status_text}:</b> Rs.{abs(pnl):,.2f} ({pnl_pct:+.2f}%)

📈 <b>Trade Details:</b>
🔹 <b>Symbol:</b> {symbol}
🔹 <b>Quantity:</b> {quantity} lots ({total_shares:,} shares)
🔹 <b>Entry Price:</b> Rs.{entry_price:.2f}
🔹 <b>Exit Price:</b> Rs.{exit_price:.2f}
🔹 <b>Price Change:</b> Rs.{exit_price - entry_price:+.2f}

📊 <b>Performance:</b>
🎯 <b>Total Trades:</b> {total_trades}
✅ <b>Winning Trades:</b> {winning_trades} ({win_rate:.1f}%)
💵 <b>Total P&amp;L:</b> Rs.{total_pnl:,.2f}
📈 <b>Pine Script Target:</b> 67% (Current: {win_rate:.1f}%)

⏰ <b>Time:</b> {datetime.now().strftime('%I:%M:%S %p')}

{"Excellent work! 🌟" if pnl > 0 else "Stay strong! 💪"}
        """
        await self.send_message(message)
    
    async def send_error_alert(self, error_message: str):
        """Send error alert"""
        message = f"""
❌ <b>AstraRise Bot Error</b>

🚨 <b>Error:</b> {error_message}
⏰ <b>Time:</b> {datetime.now().strftime('%I:%M:%S %p')}
🗓️ <b>Date:</b> {datetime.now().strftime('%B %d, %Y')}

Please check the logs for more details.
        """
        await self.send_message(message)
    
    async def send_status_update(self, status: str, details: str = ""):
        """Send status update"""
        
        status_emoji = {
            "Started": "🚀",
            "Stopped": "🛑", 
            "Error": "❌",
            "Connected": "✅",
            "Authenticated": "🔐"
        }.get(status, "📋")
        
        message = f"""
{status_emoji} <b>AstraRise Bot Status</b>

🔄 <b>Status:</b> {status}
📝 <b>Details:</b> {details}
⏰ <b>Time:</b> {datetime.now().strftime('%I:%M:%S %p')}
🗓️ <b>Date:</b> {datetime.now().strftime('%B %d, %Y')}

Bot is {"ready for action! 💪" if status == "Started" else "monitoring..."}
        """
        await self.send_message(message)
    
    async def send_daily_summary(self, total_trades: int, winning_trades: int, 
                               total_pnl: float, best_trade: float, worst_trade: float):
        """Send end-of-day summary"""
        
        win_rate = (winning_trades / max(1, total_trades)) * 100
        portfolio_return = (total_pnl / 20000) * 100
        
        performance = "🔥 EXCELLENT" if win_rate >= 70 and portfolio_return > 5 else \
                     "🎯 GOOD" if win_rate >= 60 and portfolio_return > 2 else \
                     "👍 AVERAGE" if win_rate >= 50 and portfolio_return > 0 else \
                     "📉 NEEDS IMPROVEMENT"
        
        message = f"""
📊 <b>DAILY TRADING SUMMARY</b>
🗓️ <b>Date:</b> {datetime.now().strftime('%B %d, %Y')}

{performance}

📈 <b>Today's Performance:</b>
🎯 <b>Total Trades:</b> {total_trades}
✅ <b>Winning Trades:</b> {winning_trades} ({win_rate:.1f}%)
❌ <b>Losing Trades:</b> {total_trades - winning_trades}
💵 <b>Total P&amp;L:</b> Rs.{total_pnl:,.2f}

🏆 <b>Trade Records:</b>
🥇 <b>Best Trade:</b> Rs.{best_trade:,.2f}
📉 <b>Worst Trade:</b> Rs.{worst_trade:,.2f}

💰 <b>Capital Analysis:</b>
🏦 <b>Starting Capital:</b> Rs.20,000
💵 <b>Current Capital:</b> Rs.{20000 + total_pnl:,.2f}
📈 <b>Portfolio Return:</b> {portfolio_return:+.2f}%

🎯 <b>Pine Script Analysis:</b>
📊 <b>Target Accuracy:</b> 67%
📈 <b>Actual Accuracy:</b> {win_rate:.1f}%
{"✅ ON TARGET!" if win_rate >= 67 else "⚠️ Below target - review strategy"}

Great work today! See you tomorrow! 🌟
        """
        await self.send_message(message)