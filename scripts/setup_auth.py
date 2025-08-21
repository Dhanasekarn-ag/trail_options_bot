# ==================== scripts/setup_auth.py ====================
#!/usr/bin/env python3
"""
One-time authentication setup script
"""
import sys
import asyncio
from pathlib import Path

# Add project root to path (not just src)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from config.settings import get_settings
from src.upstox_client import UpstoxClient

async def main():
    """Setup authentication"""
    try:
        settings = get_settings()
        
        print("=== Upstox Trading Bot Authentication Setup ===")
        print()
        
        # Verify credentials are loaded
        if not settings.upstox_api_key or settings.upstox_api_key == "your_actual_api_key_here":
            print("❌ Please update your .env file with actual Upstox credentials!")
            print("   Edit .env and replace placeholder values with real credentials")
            return
        
        client = UpstoxClient(
            settings.upstox_api_key,
            settings.upstox_api_secret,
            settings.upstox_redirect_uri
        )
        
        print("✅ Credentials loaded successfully!")
        print()
        print("📋 Step 1: Visit this URL to authorize the application:")
        print(f"🔗 {client.get_login_url()}")
        print()
        print("📋 Step 2: After authorization, copy the 'code' parameter from the callback URL")
        print("   Example: http://localhost:8080/callback?code=XXXXXXX")
        print("   Copy only the XXXXXXX part")
        print()
        
        auth_code = input("Enter the authorization code: ").strip()
        
        if not auth_code:
            print("❌ No authorization code provided!")
            return
        
        print("\n🔄 Getting access token...")
        
        if await client.get_access_token(auth_code):
            print("✅ Authentication successful!")
            print()
            
            # Test the connection
            print("🔄 Testing API connection...")
            
            profile = await client.get_profile()
            if profile and profile.get('status') == 'success':
                user_data = profile.get('data', {})
                print(f"✅ Profile: {user_data.get('user_name', 'Unknown')} ({user_data.get('email', 'No email')})")
            else:
                print("⚠️  Profile fetch failed, but authentication succeeded")
            
            funds = await client.get_funds()
            if funds and funds.get('status') == 'success':
                print("✅ Funds data accessible")
            else:
                print("⚠️  Funds fetch failed, but authentication succeeded")
                
            print()
            print("🎉 Setup complete! Your trading bot is ready to use.")
            print()
            print("📋 Next steps:")
            print("   1. Run: python main.py (to start the bot)")
            print("   2. The bot will start in PAPER TRADING mode by default")
            print("   3. Check logs in data/logs/ directory")
            
        else:
            print("❌ Authentication failed!")
            print("   Please check your credentials and try again")
            
    except Exception as e:
        print(f"❌ Error during setup: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())