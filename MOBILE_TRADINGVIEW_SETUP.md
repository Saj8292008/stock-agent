# TradingView Mobile Testing Guide

Complete guide to test your stock-agent with TradingView mobile app.

---

## 🎯 Overview

Your stock-agent needs:
1. **Server running** with public HTTPS URL
2. **TradingView mobile app** with alert configured
3. **Secure passphrase** configured (✅ Already set!)

Your passphrase: `Eo8rD83SnDlzGadIBbILUpBetX0vx4LnwgEzvT_PQYg`

---

## 📋 Prerequisites

- ✅ Stock-agent code ready (done)
- ✅ Secure passphrase configured (done)
- ✅ TradingView account
- ✅ TradingView mobile app installed (iOS or Android)
- ⏳ Server deployed to cloud (next step)

---

## Option 1: Quick Test with Railway.app (Recommended)

### **Why Railway?**
- ✅ Free tier (500 hours/month)
- ✅ Automatic HTTPS URL
- ✅ Deploy in 10 minutes
- ✅ Works perfectly with TradingView mobile

### **Step-by-Step Deployment:**

#### 1. Push Code to GitHub (Already Done ✅)

Your repo: https://github.com/Saj8292008/stock-agent

#### 2. Sign Up for Railway

- Go to: https://railway.app
- Click "Login" → Sign in with GitHub
- Authorize Railway to access your repos

#### 3. Create New Project

- Click "New Project"
- Select "Deploy from GitHub repo"
- Choose: `Saj8292008/stock-agent`
- Click "Deploy Now"

#### 4. Add Environment Variables

In Railway dashboard:
- Click on your service
- Go to "Variables" tab
- Add these variables:

```
TRADINGVIEW_ENABLED=true
TRADINGVIEW_PASSPHRASE=Eo8rD83SnDlzGadIBbILUpBetX0vx4LnwgEzvT_PQYg
BROKER_ENABLED=false
ENABLE_RISK_MANAGER=true
EMERGENCY_STOP=false
ALPACA_PAPER_MODE=true
```

#### 5. Configure Start Command

Railway should auto-detect Python. If needed:
- Go to "Settings" tab
- Set start command: `python serve.py`

#### 6. Get Your Public URL

- Go to "Settings" tab
- Click "Generate Domain"
- Copy the URL (e.g., `https://stock-agent-production.up.railway.app`)

**Your webhook URL will be:**
```
https://your-railway-url.railway.app/api/webhook/tradingview
```

#### 7. Test the Deployment

From your phone browser or computer:
```
https://your-railway-url.railway.app/api/portfolio
```

Should return JSON with portfolio data.

---

## Option 2: Quick Test with ngrok (Temporary)

### **Why ngrok?**
- ✅ Fastest way to test (2 minutes)
- ✅ Free tier available
- ⚠️ Temporary URL (changes when restarted)
- ⚠️ Requires your computer running

### **Step-by-Step:**

#### 1. Install ngrok

**macOS:**
```bash
brew install ngrok
```

**Windows/Linux:**
Download from: https://ngrok.com/download

#### 2. Start Your Server

```bash
cd /path/to/stock-agent
python serve.py
```

Should show:
```
INFO: Uvicorn running on http://0.0.0.0:8000
```

#### 3. Start ngrok Tunnel

In a new terminal:
```bash
ngrok http 8000
```

You'll see output like:
```
Forwarding  https://abc123.ngrok.io -> http://localhost:8000
```

#### 4. Copy the HTTPS URL

**Your webhook URL will be:**
```
https://abc123.ngrok.io/api/webhook/tradingview
```

⚠️ **Note**: This URL changes every time you restart ngrok (unless you have paid account).

---

## 📱 Configure TradingView Mobile Alert

### **Step 1: Open TradingView Mobile App**

- Launch TradingView app (iOS or Android)
- Search for a stock (e.g., AAPL, TSLA, GOOGL)
- Open the chart

### **Step 2: Create Alert**

1. **Tap the Alert icon** (bell icon, top right)
2. **Tap "+"** to create new alert
3. **Configure condition:**
   - **Condition**: Choose your trigger (e.g., "Crossing", "Greater than", "Less than")
   - **Value**: Set your price/indicator threshold
   - **Example**: AAPL crossing above $150

### **Step 3: Configure Webhook**

1. **Scroll down to "Webhook URL"**
2. **Enter your webhook URL:**
   ```
   https://your-railway-url.railway.app/api/webhook/tradingview
   ```
   or
   ```
   https://your-ngrok-url.ngrok.io/api/webhook/tradingview
   ```

3. **Tap "Message"** (webhook body)

4. **Enter this JSON** (copy exactly):

```json
{
  "passphrase": "Eo8rD83SnDlzGadIBbILUpBetX0vx4LnwgEzvT_PQYg",
  "ticker": "{{ticker}}",
  "action": "buy",
  "price": {{close}},
  "quantity": 10,
  "strategy": "Mobile Test"
}
```

**Important TradingView Variables:**
- `{{ticker}}` - Stock symbol (e.g., AAPL)
- `{{close}}` - Current close price
- `{{open}}`, `{{high}}`, `{{low}}` - OHLC prices
- `{{volume}}` - Trading volume

### **Step 4: Save Alert**

1. **Name your alert** (e.g., "AAPL Buy Test")
2. **Set expiration** (or leave "Never")
3. **Tap "Create"**

---

## 🧪 Testing Your Setup

### **Test 1: Manual Webhook Test**

Before triggering real alert, test manually from phone browser:

**Option A: Use API Testing App**

iOS: Download "HTTP Request" or "API Tester"
Android: Download "HTTP Request Maker" or "REST API Client"

**Request:**
- **Method**: POST
- **URL**: `https://your-url/api/webhook/tradingview`
- **Headers**: `Content-Type: application/json`
- **Body**:
```json
{
  "passphrase": "Eo8rD83SnDlzGadIBbILUpBetX0vx4LnwgEzvT_PQYg",
  "ticker": "AAPL",
  "action": "buy",
  "price": 150.0,
  "quantity": 5
}
```

**Expected Response:**
```json
{
  "status": "success",
  "message": "Signal processed successfully",
  "signal_id": 1
}
```

### **Test 2: Trigger TradingView Alert**

**Force alert to trigger:**

1. **Set alert with easy condition**
   - Example: AAPL > $1 (will trigger immediately if stock is trading)
2. **Wait for alert notification** on phone
3. **Check if webhook was sent** (should happen automatically)

### **Test 3: Verify Signal Received**

**Check from phone browser:**

```
https://your-url/api/signals
```

Should show your signal in JSON:
```json
[
  {
    "id": 1,
    "symbol": "AAPL",
    "action": "buy",
    "price": 150.0,
    "quantity": 10,
    "status": "processed",
    "received_at": "2024-05-28T23:30:00"
  }
]
```

**Check portfolio:**
```
https://your-url/api/portfolio
```

Should show updated cash and positions.

---

## 📊 Monitoring from Phone

### **Useful Endpoints to Bookmark**

Save these in your phone browser:

**1. Portfolio Status:**
```
https://your-url/api/portfolio
```

**2. Recent Trades:**
```
https://your-url/api/trades
```

**3. TradingView Signals:**
```
https://your-url/api/signals
```

**4. Orders:**
```
https://your-url/api/orders
```

**5. Risk Status:**
```
https://your-url/api/risk-status
```

**6. Emergency Stop:**
```
https://your-url/api/emergency-stop
```
(POST request to trigger)

### **Recommended: Create Phone Bookmarks**

iOS Safari:
1. Visit URL
2. Tap Share icon
3. "Add to Home Screen"

Android Chrome:
1. Visit URL
2. Tap menu (⋮)
3. "Add to Home screen"

---

## 🎯 Example Alert Strategies for Mobile

### **Strategy 1: RSI Oversold Buy**

**Alert Condition:**
- Indicator: RSI(14)
- Condition: Crossing
- Value: 30 (crossing below)

**Webhook Message:**
```json
{
  "passphrase": "Eo8rD83SnDlzGadIBbILUpBetX0vx4LnwgEzvT_PQYg",
  "ticker": "{{ticker}}",
  "action": "buy",
  "price": {{close}},
  "quantity": 10,
  "strategy": "RSI Oversold",
  "take_profit": {{close}} * 1.05
}
```

### **Strategy 2: Price Breakout**

**Alert Condition:**
- Condition: {{ticker}} > $150.00
- Once per bar

**Webhook Message:**
```json
{
  "passphrase": "Eo8rD83SnDlzGadIBbILUpBetX0vx4LnwgEzvT_PQYg",
  "ticker": "{{ticker}}",
  "action": "buy",
  "price": {{close}},
  "quantity": 5,
  "strategy": "Breakout $150"
}
```

### **Strategy 3: Take Profit**

**Alert Condition:**
- Condition: AAPL > $160 (5% profit target)

**Webhook Message:**
```json
{
  "passphrase": "Eo8rD83SnDlzGadIBbILUpBetX0vx4LnwgEzvT_PQYg",
  "ticker": "AAPL",
  "action": "sell",
  "price": {{close}},
  "strategy": "Take Profit 5%"
}
```

---

## 🔍 Troubleshooting

### **Problem: Alert Created but Webhook Not Sent**

**Possible Causes:**
1. ❌ Webhook URL incorrect
2. ❌ Alert condition not met yet
3. ❌ TradingView webhook feature requires paid plan

**Solution:**
- Verify URL in alert settings
- Check if condition triggered (look at chart)
- Ensure you have TradingView Premium/Pro (webhooks require paid plan)

⚠️ **Important**: TradingView webhooks require **Premium, Pro, or Pro+** subscription!

### **Problem: Webhook Returns 401/403**

**Cause:** Passphrase mismatch

**Solution:**
- Double-check passphrase in webhook message
- Ensure no extra spaces or quotes
- Passphrase is case-sensitive

### **Problem: Signal Received but Not Processed**

**Cause:** Risk manager rejected trade

**Solution:**
Check risk status:
```
https://your-url/api/risk-status
```

Review rejected signals:
```
https://your-url/api/signals?status=rejected
```

### **Problem: ngrok URL Stops Working**

**Cause:** ngrok tunnel restarted (free tier changes URL)

**Solution:**
- Get new ngrok URL
- Update TradingView alert webhook URL
- Or use Railway for permanent URL

---

## 📱 Best Practices for Mobile Testing

### **1. Start Simple**

First alert:
- Use basic price condition
- Small quantity (1-5 shares)
- Test with one stock only

### **2. Verify Each Step**

- ✅ Server running and accessible
- ✅ Manual webhook test successful
- ✅ Alert created in TradingView
- ✅ Alert triggered and notification received
- ✅ Signal appears in `/api/signals`
- ✅ Trade executed in portfolio

### **3. Monitor Closely**

First few days:
- Check portfolio multiple times daily
- Review all signals and trades
- Watch for errors in risk validation
- Verify positions match expectations

### **4. Use Paper Trading First**

```bash
BROKER_ENABLED=false  # Pure simulation
```

Test for 1-2 weeks before enabling Alpaca.

---

## 🚀 Quick Start Checklist

- [ ] Server deployed to Railway or ngrok running
- [ ] Public HTTPS URL obtained
- [ ] URL tested from phone browser
- [ ] TradingView mobile app installed
- [ ] TradingView Premium/Pro subscription active (required for webhooks)
- [ ] Alert created with webhook URL
- [ ] Webhook message JSON configured with correct passphrase
- [ ] Test alert triggered successfully
- [ ] Signal received and processed
- [ ] Portfolio updated correctly
- [ ] Bookmarks created for monitoring URLs

---

## 🎓 Next Steps After Testing

Once mobile testing works:

1. ✅ **Test multiple stocks** (AAPL, TSLA, GOOGL, etc.)
2. ✅ **Test different strategies** (RSI, MA, breakouts)
3. ✅ **Test sell signals** (not just buys)
4. ✅ **Enable Alpaca paper trading** (if ready)
5. ✅ **Set appropriate risk limits**
6. ✅ **Monitor for 2+ weeks** before live trading

---

## 📞 Support

- **Documentation**: `TRADINGVIEW_SETUP.md`
- **API Docs**: Visit `https://your-url/docs`
- **Issue Tracker**: GitHub Issues

---

## ⚠️ Important Reminders

1. 🔒 **Keep passphrase secret** - Don't share publicly
2. 💰 **Start with paper trading** - Test before real money
3. 📊 **TradingView requires paid plan** - Webhooks not in free tier
4. 🚨 **Monitor actively** - Especially first few days
5. ⚡ **Have emergency stop ready** - Can trigger from phone

---

**Happy Mobile Trading!** 📱📈🚀
