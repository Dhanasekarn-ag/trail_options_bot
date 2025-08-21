# ==================== test_telegram.py ====================
import os
import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv()

async def test_telegram():
    """Test Telegram bot integration"""
    
    bot_token = "7325110708:AAHG74VGw_0ZXX9OTxGb4WioegHgzYsA6nE"
    chat_id = "5636009404"
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    test_message = """🤖 *AstraRise Trading Bot Test*

✅ Telegram integration successful!
📊 Bot is ready for live notifications
🚀 Ready for market session tomorrow!

*Trading Settings:*
- Paper Trading: ON
- Strategy: Pine Script v2  
- Market: NIFTY Options
- Timeframe: 3 minutes

*Tomorrow's Schedule:*
- 9:00 AM - Bot startup
- 9:15 AM - Market open
- Live notifications throughout trading hours

Hello Dhana! Your bot is ready! 🎯"""
    
    payload = {
        'chat_id': chat_id,
        'text': test_message,
        'parse_mode': 'Markdown'
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    print("✅ Telegram test message sent successfully!")
                    print(f"📱 Check your Telegram (@Dhana_agds) for the test message")
                    result = await response.json()
                    print(f"📋 Message ID: {result.get('result', {}).get('message_id')}")
                else:
                    print(f"❌ Failed to send message: {response.status}")
                    text = await response.text()
                    print(f"Response: {text}")
                    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_telegram())