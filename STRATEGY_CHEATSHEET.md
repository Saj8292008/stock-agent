# 📱 TradingView Strategy Cheatsheet

**Quick reference for creating alerts on your phone.**

---

## 🔑 Your Credentials

**Passphrase:**
```
Eo8rD83SnDlzGadIBbILUpBetX0vx4LnwgEzvT_PQYg
```

**Webhook URL:**
```
https://your-railway-url.up.railway.app/api/webhook/tradingview
```

---

## 📋 5 Quick Strategies

### 1️⃣ **Test Strategy (Try This First!)**

**Condition:** AAPL > 1
**Triggers:** Immediately (for testing)

**Webhook Message:**
```json
{
  "passphrase": "Eo8rD83SnDlzGadIBbILUpBetX0vx4LnwgEzvT_PQYg",
  "ticker": "AAPL",
  "action": "buy",
  "price": {{close}},
  "quantity": 1,
  "strategy": "System Test"
}
```

---

### 2️⃣ **Price Breakout**

**Condition:** AAPL Crossing Up 175
**Triggers:** When AAPL breaks above $175

**Webhook Message:**
```json
{
  "passphrase": "Eo8rD83SnDlzGadIBbILUpBetX0vx4LnwgEzvT_PQYg",
  "ticker": "AAPL",
  "action": "buy",
  "price": {{close}},
  "quantity": 10,
  "strategy": "Breakout $175"
}
```

---

### 3️⃣ **RSI Oversold**

**Condition:** RSI(14) Crossing Down 30
**Triggers:** When RSI drops below 30

**Webhook Message:**
```json
{
  "passphrase": "Eo8rD83SnDlzGadIBbILUpBetX0vx4LnwgEzvT_PQYg",
  "ticker": "TSLA",
  "action": "buy",
  "price": {{close}},
  "quantity": 5,
  "strategy": "RSI Oversold"
}
```

---

### 4️⃣ **Take Profit (5%)**

**Condition:** NVDA > 126 (if bought at $120)
**Triggers:** When price hits profit target

**Webhook Message:**
```json
{
  "passphrase": "Eo8rD83SnDlzGadIBbILUpBetX0vx4LnwgEzvT_PQYg",
  "ticker": "NVDA",
  "action": "sell",
  "price": {{close}},
  "strategy": "Take Profit 5%"
}
```

---

### 5️⃣ **Stop Loss (3%)**

**Condition:** META < 485 (if bought at $500)
**Triggers:** When price drops 3%

**Webhook Message:**
```json
{
  "passphrase": "Eo8rD83SnDlzGadIBbILUpBetX0vx4LnwgEzvT_PQYg",
  "ticker": "META",
  "action": "sell",
  "price": {{close}},
  "strategy": "Stop Loss 3%"
}
```

---

## 📱 Quick Monitoring Links

**Portfolio:**
```
https://your-url/api/portfolio
```

**Recent Signals:**
```
https://your-url/api/signals
```

**Recent Trades:**
```
https://your-url/api/trades
```

**Risk Status:**
```
https://your-url/api/risk-status
```

---

## 🎯 Alert Creation Checklist

- [ ] Webhook URL set
- [ ] Passphrase correct (copy-paste!)
- [ ] Ticker symbol correct
- [ ] Action: "buy" or "sell"
- [ ] Quantity set
- [ ] Strategy name clear
- [ ] "Once per bar close" ✅

---

## 🔢 Quick Calculations

**Take Profit:**
- Entry × 1.05 = 5% profit
- Entry × 1.10 = 10% profit
- Entry × 1.15 = 15% profit

**Stop Loss:**
- Entry × 0.97 = 3% loss
- Entry × 0.95 = 5% loss
- Entry × 0.90 = 10% loss

**Example:**
Bought at $100
- 5% profit target: $105
- 3% stop loss: $97

---

## ⚡ Emergency Stop

**Browser URL:**
```
https://your-url/api/emergency-stop
```

(POST request to activate)

---

## 💡 Pro Tips

✅ Start with 1 share for testing
✅ Use "Once per bar close"
✅ Test during market hours
✅ Clear alert names
✅ Monitor daily first week

---

**Bookmark this page on your phone!** 📱
