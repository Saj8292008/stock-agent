# 📱 Quick Start: TradingView Mobile Testing

**Fast track guide to get your stock-agent working with TradingView mobile in under 15 minutes.**

---

## ⚡ 3-Step Quick Start

### **Step 1: Deploy Server (10 minutes)**

**Railway.app (Recommended):**

1. Go to: https://railway.app
2. Sign in with GitHub
3. "New Project" → "Deploy from GitHub repo"
4. Select: `Saj8292008/stock-agent`
5. Add Variables:
   ```
   TRADINGVIEW_ENABLED=true
   TRADINGVIEW_PASSPHRASE=Eo8rD83SnDlzGadIBbILUpBetX0vx4LnwgEzvT_PQYg
   BROKER_ENABLED=false
   ENABLE_RISK_MANAGER=true
   ```
6. Settings → "Generate Domain"
7. Copy your URL: `https://stock-agent-xxx.up.railway.app`

✅ **Done!** Your server is live.

---

### **Step 2: Create Alert in TradingView Mobile (3 minutes)**

1. Open TradingView mobile app
2. Search for stock (AAPL, TSLA, etc.)
3. Tap Alert icon (🔔)
4. Tap "+" to create alert
5. Set condition (e.g., AAPL > $150)
6. **Webhook URL:**
   ```
   https://your-railway-url.up.railway.app/api/webhook/tradingview
   ```
7. **Message:**
   ```json
   {
     "passphrase": "Eo8rD83SnDlzGadIBbILUpBetX0vx4LnwgEzvT_PQYg",
     "ticker": "{{ticker}}",
     "action": "buy",
     "price": {{close}},
     "quantity": 10
   }
   ```
8. Tap "Create"

✅ **Done!** Alert is active.

---

### **Step 3: Test & Monitor (2 minutes)**

**Test from phone browser:**
```
https://your-railway-url.up.railway.app/api/portfolio
```

**Trigger alert:**
- Set easy condition (e.g., AAPL > $1)
- Wait for notification
- Check signals: `https://your-url/api/signals`

✅ **Done!** System is working.

---

## 📱 Phone Bookmarks

Save these URLs in your mobile browser:

**Portfolio:**
```
https://your-url/api/portfolio
```

**Recent Signals:**
```
https://your-url/api/signals
```

**Trades:**
```
https://your-url/api/trades
```

**Emergency Stop:**
```
https://your-url/api/emergency-stop
```

---

## ⚠️ Important Notes

1. **TradingView requires paid plan** (Premium/Pro) for webhooks
2. **Your passphrase:** `Eo8rD83SnDlzGadIBbILUpBetX0vx4LnwgEzvT_PQYg`
3. **Currently paper trading** (no real money)
4. **Monitor daily** for first week

---

## 🆘 Troubleshooting

**Alert not triggering?**
- Check condition is met (look at current price)
- Verify TradingView Premium subscription

**401/403 error?**
- Check passphrase matches exactly
- No extra spaces in JSON

**Signal not executing?**
- Check risk limits: `https://your-url/api/risk-status`

---

## 📚 Full Guides

- **Complete mobile guide:** `MOBILE_TRADINGVIEW_SETUP.md`
- **TradingView setup:** `TRADINGVIEW_SETUP.md`
- **Testing guide:** `README_TESTING.md`

---

**You're ready to test mobile trading!** 📱🚀
