import asyncio
import aiohttp

async def test_telegram():
    bot_token = "7325110708:AAHG74VGw_0ZXX9OTxGb4WioegHgzYsA6nE"
    
    # Test both chat IDs individually
    chat_ids = ["5636009404", "-1002867661585"]
    
    for chat_id in chat_ids:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': "🤖 Bot Connection Test - Working perfectly!"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    print(f"✅ Success: {chat_id}")
                else:
                    print(f"❌ Failed: {chat_id} - {response.status}")

asyncio.run(test_telegram())