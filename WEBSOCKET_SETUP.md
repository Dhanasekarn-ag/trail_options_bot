# ==================== WEBSOCKET_SETUP.md ====================
# WebSocket Setup Guide

## 🚀 Quick Setup

### 1. Install WebSocket Dependencies
```powershell
# Install required packages
python scripts\install_websocket_deps.py
```

### 2. Test WebSocket Functionality  
```powershell
# Run tests to verify installation
python scripts\test_websocket.py
```

### 3. Run Bot with Real-Time Data
```powershell
# Start trading bot (now with websockets!)
python main.py
```

## ✅ What WebSockets Add to Your Bot

### **Real-Time Features:**
- ✅ **3-minute candle aggregation** from live ticks
- ✅ **Heikin Ashi conversion** in real-time
- ✅ **Instant strategy triggers** on new candles
- ✅ **Real-time order updates** 
- ✅ **Live position tracking**
- ✅ **Fast exit conditions** (red candle detection)

### **Performance Improvements:**
- ⚡ **Instant data** vs 60-second REST API delays
- ⚡ **Real-time exits** vs delayed stop losses
- ⚡ **Live strategy execution** vs periodic checks
- ⚡ **Immediate order confirmations**

## 📊 Bot Behavior Changes

### **Before WebSockets (REST API Only):**
```
Check every 60 seconds → Get stale data → Make decisions → Place orders
```

### **After WebSockets (Real-Time):**
```
Live tick data → Build 3min candles → Convert to HA → Trigger strategy → Instant execution
```

## 🔧 Configuration

### **Instruments Subscribed by Default:**
- `NSE_INDEX|Nifty 50` - NIFTY Index
- `NSE_INDEX|Nifty Bank` - BANKNIFTY Index  
- `BSE_INDEX|SENSEX` - SENSEX Index

### **Customize Instruments:**
```python
# In trading_bot.py, modify default_instruments:
self.default_instruments = [
    'NSE_INDEX|Nifty 50',
    'NSE_FO|50201',  # NIFTY Futures
    # Add your options instrument keys here
]
```

## 📈 Strategy Integration

### **Your Strategy Will Receive:**
```python
market_data = {
    'symbol': 'NIFTY',
    'ha_candle': {
        'ha_open': 25000.50,
        'ha_high': 25050.25, 
        'ha_low': 24980.75,
        'ha_close': 25025.00
    },
    'historical_ha_candles': [...],  # Last 50 HA candles
    'current_tick': {...},           # Latest tick data
    'timestamp': datetime.now()
}
```

### **Strategy Trigger Points:**
- ✅ **New 3-min HA candle completed** → Strategy evaluation
- ✅ **Strong red candle formed** → Exit condition check
- ✅ **Price crosses trend line** → Entry/exit signals
- ✅ **ADX threshold breached** → Trend strength validation

## 🚨 Troubleshooting

### **If WebSocket Installation Fails:**
```powershell
# Manual installation
pip install upstox-python-sdk>=1.9.0
pip install protobuf>=4.21.0
pip install websocket-client>=1.6.0
```

### **If Bot Falls Back to REST API:**
- Check logs: `notepad data\logs\trading_bot.log`
- Look for: "WebSocket not available" warnings
- Verify: All dependencies installed correctly

### **If No Real-Time Data:**
- Check: Internet connection stable
- Verify: Access token is valid
- Confirm: Market hours (9:15 AM - 3:30 PM)

## 📋 Next Steps

1. ✅ **WebSockets working** → Implement your Pine Script strategy
2. ✅ **Strategy implemented** → Run backtests
3. ✅ **Backtests passed** → Test with paper trading  
4. ✅ **Paper trading successful** → Go live!

**Your bot is now ready for real-time options trading with 3-minute Heikin Ashi strategy execution! 🎊**