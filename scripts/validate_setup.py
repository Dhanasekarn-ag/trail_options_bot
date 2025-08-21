#!/usr/bin/env python3
"""Quick validation before running the bot"""
import sys
from pathlib import Path

def validate_setup():
    """Validate bot setup"""
    print("🔍 Validating AstraRise Bot Setup...")
    
    issues = []
    warnings = []
    
    # Check 1: .env file
    if not Path(".env").exists():
        issues.append("❌ .env file not found")
    else:
        print("✅ .env file found")
    
    # Check 2: Access token
    if not Path("data/access_token.json").exists():
        warnings.append("⚠️ No access token - will need to authenticate")
    else:
        print("✅ Access token exists")
    
    # Check 3: Required directories
    for dir_name in ["data", "data/logs", "data/cache"]:
        if not Path(dir_name).exists():
            Path(dir_name).mkdir(parents=True, exist_ok=True)
            print(f"📁 Created directory: {dir_name}")
    
    # Check 4: Critical imports
    try:
        import upstox_client
        print("✅ Upstox SDK installed")
    except ImportError:
        issues.append("❌ upstox-python-sdk not installed")
    
    try:
        import websocket
        print("✅ WebSocket client installed")
    except ImportError:
        warnings.append("⚠️ websocket-client not installed - real-time data won't work")
    
    # Report
    print("\n" + "=" * 50)
    if issues:
        print("🛑 CRITICAL ISSUES FOUND:")
        for issue in issues:
            print(f"  {issue}")
        print("\nFix these before running the bot!")
        return False
    elif warnings:
        print("⚠️ WARNINGS:")
        for warning in warnings:
            print(f"  {warning}")
        print("\n✅ Bot can run with limitations")
        return True
    else:
        print("✅ ALL CHECKS PASSED - Bot ready to run!")
        return True

if __name__ == "__main__":
    if validate_setup():
        print("\n🚀 You can now run: python main.py")
    else:
        print("\n❌ Please fix issues first")