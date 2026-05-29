# 📈 My First TradingView Alert Strategy

**Beginner-friendly trading strategies for your stock-agent system.**

---

## 🎯 Strategy 1: Simple Price Breakout (Recommended First Strategy)

**Perfect for:** Testing your system, learning how alerts work

### **Concept**
Buy when a stock breaks above a key price level (resistance).

### **Example: AAPL Breakout at $175**

**When to use:**
- AAPL is currently trading around $170-174
- You believe it will break through $175
- Want to catch momentum when it breaks out

---

### **📱 How to Set Up in TradingView Mobile**

#### **Step 1: Open TradingView App**
- Search for **AAPL**
- Switch to your preferred timeframe (15min, 1hour, or Daily)

#### **Step 2: Create Alert**
1. Tap the **Alert icon (🔔)** in top right
2. Tap **"+"** to create new alert

#### **Step 3: Configure Condition**
- **Field 1:** Select "AAPL" (should be pre-selected)
- **Condition:** Select "Crossing"
- **Value:** Enter `175` (or your breakout level)
- **Crossing direction:** "Crossing Up"

This triggers when AAPL crosses above $175.

#### **Step 4: Set Alert Options**
- **Alert name:** "AAPL Breakout $175 - BUY"
- **Expiration:** "Only once" (or set date if you prefer)
- **Once per bar close:** ✅ Check this (prevents false signals)

#### **Step 5: Configure Webhook**

**Webhook URL:**
```
https://your-railway-url.up.railway.app/api/webhook/tradingview
```

**Message:**
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

#### **Step 6: Create Alert**
Tap **"Create"** at the bottom.

---

### **What Happens When Alert Triggers:**

1. ✅ AAPL crosses above $175
2. ✅ TradingView sends webhook to your server
3. ✅ Server receives signal and processes it
4. ✅ Stock-agent buys 10 shares of AAPL at current price
5. ✅ Trade logged to database
6. ✅ You can see it in portfolio: `https://your-url/api/portfolio`

---

## 🎯 Strategy 2: RSI Oversold Buy Signal

**Perfect for:** Buying stocks when they're oversold (potential bounce)

### **Concept**
RSI (Relative Strength Index) below 30 = oversold = potential buying opportunity.

### **Example: TSLA RSI Oversold**

---

### **📱 How to Set Up**

#### **Step 1: Add RSI Indicator**
1. Open TSLA chart
2. Tap **"Indicators"** button
3. Search for **"RSI"** (Relative Strength Index)
4. Add "Relative Strength Index" (default settings: 14 period)

#### **Step 2: Create Alert**
1. Tap **Alert icon (🔔)**
2. Tap **"+"**

#### **Step 3: Configure Condition**
- **Field 1:** Select "RSI"
- **Condition:** Select "Crossing"
- **Value:** Enter `30`
- **Crossing direction:** "Crossing Down"

This triggers when RSI drops below 30 (oversold).

#### **Step 4: Webhook Configuration**

**Webhook URL:**
```
https://your-url/api/webhook/tradingview
```

**Message:**
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

**Name:** "TSLA RSI Oversold - BUY"

---

## 🎯 Strategy 3: Moving Average Crossover

**Perfect for:** Catching trend changes

### **Concept**
When fast MA (50) crosses above slow MA (200) = bullish signal (Golden Cross).

### **Example: GOOGL Golden Cross**

---

### **📱 How to Set Up**

#### **Step 1: Add Moving Averages**
1. Open GOOGL chart
2. Add indicator: **"SMA" (Simple Moving Average)**
3. Set length to **50** (fast MA)
4. Add another SMA indicator
5. Set length to **200** (slow MA)

#### **Step 2: Create Alert**
1. Tap **Alert icon**
2. Tap **"+"**

#### **Step 3: Configure Condition**
- **Field 1:** Select "SMA(50)"
- **Condition:** "Crossing"
- **Field 2:** Select "SMA(200)"
- **Crossing direction:** "Crossing Up"

#### **Step 4: Webhook Configuration**

**Message:**
```json
{
  "passphrase": "Eo8rD83SnDlzGadIBbILUpBetX0vx4LnwgEzvT_PQYg",
  "ticker": "GOOGL",
  "action": "buy",
  "price": {{close}},
  "quantity": 8,
  "strategy": "Golden Cross"
}
```

**Name:** "GOOGL Golden Cross - BUY"

---

## 🎯 Strategy 4: Take Profit Exit

**Perfect for:** Locking in profits automatically

### **Concept**
Sell when stock reaches your profit target (e.g., +5%, +10%).

### **Example: Take 5% Profit on NVDA**

**Scenario:** You bought NVDA at $120, want to sell at $126 (5% gain).

---

### **📱 How to Set Up**

#### **Step 1: Calculate Target Price**
- **Entry price:** $120
- **Profit target:** 5%
- **Exit price:** $120 × 1.05 = $126

#### **Step 2: Create Alert**
- **Condition:** NVDA > 126
- **Direction:** "Crossing Up"

#### **Step 3: Webhook Configuration**

**Message:**
```json
{
  "passphrase": "Eo8rD83SnDlzGadIBbILUpBetX0vx4LnwgEzvT_PQYg",
  "ticker": "NVDA",
  "action": "sell",
  "price": {{close}},
  "strategy": "Take Profit 5%"
}
```

**Name:** "NVDA Take Profit 5% - SELL"

**⚠️ Important:** This sells ALL shares of NVDA. Adjust if you want partial exits.

---

## 🎯 Strategy 5: Stop Loss Protection

**Perfect for:** Limiting losses automatically

### **Concept**
Sell when stock drops below a certain level to prevent bigger losses.

### **Example: 3% Stop Loss on META**

**Scenario:** You bought META at $500, want to limit loss to 3%.

---

### **📱 How to Set Up**

#### **Step 1: Calculate Stop Price**
- **Entry price:** $500
- **Stop loss:** 3%
- **Stop price:** $500 × 0.97 = $485

#### **Step 2: Create Alert**
- **Condition:** META < 485
- **Direction:** "Crossing Down"

#### **Step 3: Webhook Configuration**

**Message:**
```json
{
  "passphrase": "Eo8rD83SnDlzGadIBbILUpBetX0vx4LnwgEzvT_PQYg",
  "ticker": "META",
  "action": "sell",
  "price": {{close}},
  "strategy": "Stop Loss 3%"
}
```

**Name:** "META Stop Loss 3% - SELL"

---

## 🧪 Test Strategy (Recommended First!)

**Use this to verify your system is working before using real strategies.**

### **Instant Trigger Test**

**Purpose:** Alert triggers immediately so you can test the full workflow.

---

### **📱 How to Set Up**

#### **Step 1: Create Alert**
- **Stock:** AAPL (or any actively trading stock)
- **Condition:** AAPL > 1
- **Direction:** "Crossing Up"

This triggers immediately since AAPL is always > $1!

#### **Step 2: Webhook Configuration**

**Message:**
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

**Name:** "SYSTEM TEST - Instant Trigger"

**What to expect:**
1. Alert triggers within seconds
2. You get TradingView notification
3. Check signals: `https://your-url/api/signals`
4. Should see new signal immediately
5. Check portfolio: `https://your-url/api/portfolio`
6. Should show AAPL purchase

**Delete this alert after successful test!**

---

## 📊 Strategy Comparison Table

| Strategy | Difficulty | Frequency | Risk Level | Best For |
|----------|-----------|-----------|----------|----------|
| **Price Breakout** | ⭐ Easy | Medium | Medium | Beginners, momentum |
| **RSI Oversold** | ⭐⭐ Medium | High | Medium | Mean reversion |
| **MA Crossover** | ⭐⭐ Medium | Low | Low | Trend following |
| **Take Profit** | ⭐ Easy | Medium | Low | Profit taking |
| **Stop Loss** | ⭐ Easy | Low | Low | Risk management |
| **Test Strategy** | ⭐ Easy | Once | None | Testing system |

---

## 🎯 Recommended First Week Strategy Mix

### **Day 1-2: Testing**
1. ✅ Set up **Test Strategy** (instant trigger)
2. ✅ Verify signals received
3. ✅ Check portfolio updates
4. ✅ Delete test alert

### **Day 3-4: Simple Strategy**
1. ✅ Set up **Price Breakout** for AAPL
2. ✅ Monitor for 2 days
3. ✅ Verify execution when triggered

### **Day 5-7: Multiple Strategies**
1. ✅ Add **RSI Oversold** for TSLA
2. ✅ Add **Take Profit** for any positions
3. ✅ Add **Stop Loss** for risk management

---

## 💡 Pro Tips for Your First Strategies

### **1. Start with Small Quantities**
```json
"quantity": 1  // Start with 1 share to minimize risk
```

### **2. Use Common Stocks First**
- ✅ AAPL, TSLA, GOOGL, MSFT, NVDA
- ❌ Avoid penny stocks or illiquid stocks initially

### **3. Test During Market Hours**
- NYSE: 9:30 AM - 4:00 PM ET
- Set alerts that might trigger during these hours

### **4. Monitor Closely First Week**
Check these URLs daily:
- Signals: `https://your-url/api/signals`
- Portfolio: `https://your-url/api/portfolio`
- Trades: `https://your-url/api/trades`

### **5. Use Clear Alert Names**
Good: "AAPL Breakout $175 - BUY"
Bad: "Alert 1"

This helps you track what triggered.

---

## 🔍 Monitoring Your Strategies

### **Check Signal Processing**

After alert triggers:

**1. View recent signals:**
```
https://your-url/api/signals?limit=10
```

**2. Check if processed:**
Look for `"status": "processed"` in response

**3. Check for rejections:**
```
https://your-url/api/signals?status=rejected
```

If rejected, check `rejection_reason` field.

### **Common Rejection Reasons:**

1. **"Exceeds position size limit"**
   - Quantity too large for portfolio
   - Reduce quantity in alert

2. **"Daily loss limit reached"**
   - Lost too much today
   - Risk manager blocked trade
   - Wait until tomorrow

3. **"Exceeds concentration limit"**
   - Too much of one stock
   - Diversify or adjust limits

---

## 📱 Quick Reference: Alert Setup Checklist

When creating ANY alert:

- [ ] Stock symbol correct (e.g., AAPL not Apple)
- [ ] Condition makes sense (will it trigger?)
- [ ] Webhook URL is your server URL + `/api/webhook/tradingview`
- [ ] Passphrase matches exactly (copy-paste!)
- [ ] Action is "buy" or "sell"
- [ ] Quantity is reasonable (start with 1-10)
- [ ] Strategy name is descriptive
- [ ] Alert name is clear
- [ ] "Once per bar close" checked (prevents spam)

---

## 🆘 Troubleshooting Your First Strategy

### **Alert Created but Not Triggering**

**Check:**
1. Is condition already met? (e.g., AAPL > $150 when it's $175)
2. Is market open?
3. Is stock trading? (check chart has recent bars)

**Fix:** Adjust condition or wait for market hours.

### **Alert Triggered but No Signal**

**Check:**
1. Webhook URL correct?
2. TradingView Premium/Pro active?
3. Server running?

**Test:** Visit `https://your-url/api/portfolio` in phone browser.

### **Signal Received but Not Executed**

**Check:**
```
https://your-url/api/signals
```

Look for `"status": "rejected"` and `"rejection_reason"`.

**Common fixes:**
- Reduce quantity
- Check risk limits: `https://your-url/api/risk-status`
- Verify cash available

---

## 🎓 Next Steps After First Strategy

Once your first strategy works:

1. ✅ **Add more stocks** (diversify)
2. ✅ **Add exit strategies** (take profit, stop loss)
3. ✅ **Experiment with indicators** (MACD, Bollinger Bands)
4. ✅ **Adjust quantities** (as confidence grows)
5. ✅ **Enable Alpaca paper trading** (more realistic)

---

## 📚 Additional Resources

- **Full TradingView guide:** `TRADINGVIEW_SETUP.md`
- **Mobile setup:** `MOBILE_TRADINGVIEW_SETUP.md`
- **Quick start:** `QUICK_START_MOBILE.md`
- **Technical docs:** `CLAUDE.md`

---

## 🎯 Your Action Plan

**Right Now:**

1. ✅ Deploy server (Railway or ngrok)
2. ✅ Set up **Test Strategy** (instant trigger)
3. ✅ Verify it works
4. ✅ Set up **Price Breakout** strategy for AAPL
5. ✅ Monitor for 2-3 days

**This Week:**

1. ✅ Add 2-3 more stocks
2. ✅ Add take profit alerts
3. ✅ Add stop loss alerts
4. ✅ Review performance daily

**Next Week:**

1. ✅ Try RSI or MA strategies
2. ✅ Adjust quantities
3. ✅ Consider Alpaca paper trading

---

**You're ready to create your first strategy!** 🚀📈

Start with the **Test Strategy** to verify everything works, then move to **Price Breakout** for your first real strategy.
