# ==================== scripts/install_websocket_deps.py ====================
#!/usr/bin/env python3
"""
Install WebSocket dependencies for real-time trading
"""
import subprocess
import sys
import os
from pathlib import Path

def install_package(package):
    """Install a package using pip"""
    try:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package}: {e}")
        return False

def main():
    """Install WebSocket dependencies"""
    print("🚀 Installing WebSocket dependencies for real-time trading...")
    print()
    
    # Required packages for websocket functionality
    websocket_packages = [
        "upstox-python-sdk>=1.9.0",
        "protobuf>=4.21.0", 
        "websocket-client>=1.6.0"
    ]
    
    success_count = 0
    total_packages = len(websocket_packages)
    
    for package in websocket_packages:
        if install_package(package):
            success_count += 1
        print()
    
    print("="*50)
    print(f"Installation Summary: {success_count}/{total_packages} packages installed")
    
    if success_count == total_packages:
        print("🎉 All WebSocket dependencies installed successfully!")
        print()
        print("✅ Your trading bot now supports:")
        print("   • Real-time market data streaming")
        print("   • 3-minute candle aggregation")
        print("   • Heikin Ashi conversion")
        print("   • Instant order updates")
        print("   • Real-time strategy execution")
        print()
        print("🚀 You can now run: python main.py")
        
        # Test imports
        print("\n🔍 Testing WebSocket functionality...")
        try:
            import upstox_client
            print("✅ upstox-python-sdk imported successfully")
            
            import websocket
            print("✅ websocket-client imported successfully")
            
            import google.protobuf
            print("✅ protobuf imported successfully")
            
            print("\n🎊 WebSocket setup complete! Your bot is ready for real-time trading.")
            
        except ImportError as e:
            print(f"⚠️  Import test failed: {e}")
            print("You may need to restart your terminal/IDE")
    else:
        print("❌ Some packages failed to install")
        print("Please check the error messages above and try again")
        print()
        print("You can also try installing manually:")
        for package in websocket_packages:
            print(f"   pip install {package}")

if __name__ == "__main__":
    main()