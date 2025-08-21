#!/usr/bin/env python3
"""
Verify all imports work correctly
"""

def test_basic_imports():
    """Test basic Python imports"""
    try:
        import sys
        import asyncio
        import logging
        import pandas as pd
        import numpy as np
        print("✅ Basic imports: OK")
        return True
    except ImportError as e:
        print(f"❌ Basic imports failed: {e}")
        return False

def test_upstox_imports():
    """Test Upstox SDK imports"""
    try:
        import upstox_client
        print("✅ upstox_client: OK")
        
        # Test specific classes
        from upstox_client.rest import ApiException
        print("✅ upstox_client.rest: OK")
        
        # Test configuration
        config = upstox_client.Configuration()
        print("✅ upstox_client.Configuration: OK")
        
        return True
    except ImportError as e:
        print(f"❌ Upstox imports failed: {e}")
        return False

def test_websocket_imports():
    """Test WebSocket related imports"""
    try:
        import websocket
        print("✅ websocket: OK")
        
        import google.protobuf
        print("✅ protobuf: OK")
        
        return True
    except ImportError as e:
        print(f"❌ WebSocket imports failed: {e}")
        return False

def test_project_imports():
    """Test our project imports"""
    try:
        from config.settings import get_settings
        print("✅ config.settings: OK")
        
        from src.upstox_client import UpstoxClient
        print("✅ src.upstox_client: OK")
        
        from src.websocket.websocket_manager import WebSocketManager
        print("✅ src.websocket.websocket_manager: OK")
        
        return True
    except ImportError as e:
        print(f"❌ Project imports failed: {e}")
        return False

def main():
    """Run all import tests"""
    print("🔍 Import Verification Test")
    print("=" * 40)
    
    tests = [
        ("Basic Imports", test_basic_imports),
        ("Upstox SDK", test_upstox_imports),
        ("WebSocket", test_websocket_imports),
        ("Project Modules", test_project_imports)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Testing {test_name}...")
        if test_func():
            passed += 1
    
    print("\n" + "=" * 40)
    print(f"🎯 Results: {passed}/{total} import groups passed")
    
    if passed == total:
        print("🎉 All imports working! Ready to run trading bot.")
    else:
        print("❌ Some imports failed. Check the errors above.")
        
        if passed < total:
            print("\n🔧 Possible fixes:")
            print("1. Reinstall upstox SDK: pip install --upgrade upstox-python-sdk")
            print("2. Check virtual environment is activated")
            print("3. Restart VS Code/IDE after installation")

if __name__ == "__main__":
    main()