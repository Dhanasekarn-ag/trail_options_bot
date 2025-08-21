# ==================== test_group_telegram.py ====================
import os
import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv()

async def test_group_messaging():
    """Test sending to both personal and group"""
    
    bot_token = "7325110708:AAHG74VGw_0ZXX9OTxGb4WioegHgzYsA6nE"
    
    # Both destinations
    destinations = [
        {
            "chat_id": "5636009404",
            "name": "Personal Chat (Dhana)"
        },
        {
            "chat_id": "-1002867661585", 
            "name": "TradingBot updates Group"
        }
    ]
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    test_message = """🤖 *AstraRise Trading Bot - Multi-Chat Test*

✅ Successfully connected to TradingBot updates group!
👥 Group notifications are now active
📊 All trading signals will be shared here

*Group Setup Complete:*
- Bot added as Administrator ✅
- Full permissions granted ✅
- Ready for live trading notifications ✅

*Tomorrow's Features:*
🚀 Real-time BUY signals
🛑 Instant EXIT alerts  
📊 Live performance tracking
📈 Daily trading summaries

*Group ID:* `-1002867661585`
*Personal ID:* `5636009404`

Ready for market session tomorrow! 🎯"""
    
    for dest in destinations:
        payload = {
            'chat_id': dest["chat_id"],
            'text': test_message,
            'parse_mode': 'Markdown'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ Message sent to {dest['name']}")
                        print(f"   📋 Message ID: {result.get('result', {}).get('message_id')}")
                    else:
                        print(f"❌ Failed to send to {dest['name']}: {response.status}")
                        text = await response.text()
                        print(f"   Error: {text}")
                        
        except Exception as e:
            print(f"❌ Error sending to {dest['name']}: {e}")
        
        # Small delay between messages
        await asyncio.sleep(0.5)

if __name__ == "__main__":
    asyncio.run(test_group_messaging())