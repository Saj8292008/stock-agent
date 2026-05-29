# ⚡ Quick Start: GitHub Actions Trading

**Get your bot running in the cloud in 5 minutes - FREE!**

---

## 🚀 3-Step Setup

### **Step 1: The Workflow is Already Created!**

✅ File: `.github/workflows/trading-cycle.yml`
✅ Committed to your repo
✅ Ready to run!

### **Step 2: Test It Now**

1. Go to: `https://github.com/Saj8292008/stock-agent/actions`
2. Click **"Automated Trading Cycle"** (left sidebar)
3. Click **"Run workflow"** button (right side)
4. Click green **"Run workflow"** button
5. Wait 1-2 minutes
6. Click on the run to see results!

### **Step 3: It Runs Automatically**

✅ Every 5 minutes during market hours
✅ Monday - Friday
✅ 9:30 AM - 4:00 PM ET
✅ No action needed from you!

**Done!** 🎉

---

## 📊 What It Does

- ✅ Fetches stock prices every 5 minutes
- ✅ Checks for buy signals (stock down 5%+)
- ✅ Checks for sell signals (take-profit, stop-loss)
- ✅ Executes trades automatically
- ✅ Saves portfolio between runs
- ✅ Creates trading summaries

**All in the cloud, for FREE!**

---

## 👀 Monitor Your Bot

### **View Workflow Runs**
```
https://github.com/Saj8292008/stock-agent/actions
```

**See:**
- All trading cycles
- Trades executed
- Portfolio status
- Recent trades

### **Download Your Data**

Each run saves:
- `portfolio-database` - Your SQLite database (90 days)
- `trading-summary` - Trading report (30 days)

Click workflow → Artifacts → Download

---

## 🎮 Manual Controls

### **Run Now (Don't Wait for Schedule)**
1. Actions tab → "Automated Trading Cycle"
2. "Run workflow" → "Run workflow"

### **Stop Trading**
1. Go to: Settings → Secrets → Actions
2. Add: `EMERGENCY_STOP = true`

### **Resume Trading**
1. Update: `EMERGENCY_STOP = false`

---

## 📅 Schedule

**Automatic runs:**
- Every 5 minutes
- Market hours: 9:30 AM - 4:00 PM ET
- Days: Monday - Friday
- Skips weekends and after-hours

**Next run:** Check Actions tab for schedule

---

## 💰 Cost

**FREE!**
- Public repos: Unlimited GitHub Actions
- Private repos: 2,000 minutes/month free
- Each cycle: ~1-2 minutes
- **300-600+ cycles/month** on free tier

---

## 🔧 Configuration (Optional)

### **Enable Alpaca Broker**
1. Settings → Secrets → Actions → New secret
2. Add:
   ```
   BROKER_ENABLED = true
   ALPACA_API_KEY = your_paper_key
   ALPACA_API_SECRET = your_paper_secret
   ALPACA_PAPER_MODE = true
   ```

**For paper trading:** No secrets needed!

---

## 📈 Example Workflow Output

```
=== Trading Cycle Complete ===
2 trade(s) executed:
  BUY AAPL - 10.0000 shares @ $175.50
  SELL TSLA - 5.0000 shares @ $260.00

=== Portfolio Status ===
Cash: $97,530.00
Total Value: $99,780.00
Positions: 2

=== Recent Trades ===
2024-05-28 14:30:00 | BUY  | AAPL  |  10.0000 @ $175.50 | Dip below -5%
2024-05-28 14:35:00 | SELL | TSLA  |   5.0000 @ $260.00 | Take profit +10%
```

---

## ⚠️ Important Notes

### **What It CAN Do:**
✅ Scheduled trading (every 5 min)
✅ Buy-the-dip strategy
✅ Take-profit / stop-loss
✅ Paper trading
✅ Alpaca broker integration
✅ Complete automation

### **What It CAN'T Do:**
❌ TradingView webhooks (use Railway for that)
❌ Real-time responses (5 min delay)
❌ Run during closed market hours

---

## 🎯 Best Use Cases

### **Perfect For:**
- ✅ Automated paper trading
- ✅ Testing strategies
- ✅ Scheduled position management
- ✅ Free cloud hosting
- ✅ Learning automated trading

### **Also Use Railway/Render For:**
- TradingView webhooks (real-time alerts)
- API monitoring endpoint
- Mobile access

**You can use BOTH together!**

---

## 🆘 Quick Troubleshooting

**Bot not running?**
- Check: Actions tab → Enable workflow
- Check: Is it market hours?
- Try: Manual trigger

**No trades?**
- Normal! No signals present
- Bot monitors continuously
- Trades only when conditions met

**Database not persisting?**
- First run creates new database
- Subsequent runs load previous state
- Download artifact to verify

---

## 📚 Full Documentation

See: `GITHUB_ACTIONS_TRADING.md`

---

## 🎉 You're All Set!

Your trading bot is now running in GitHub Actions!

**What happens next:**
1. ✅ Bot runs every 5 min during market hours
2. ✅ Executes trades when signals present
3. ✅ Saves portfolio automatically
4. ✅ Creates summaries you can view

**Check Actions tab to see it in action!** 🚀📈

---

**Next:**
- Monitor: `github.com/Saj8292008/stock-agent/actions`
- Download data: Check Artifacts
- Full guide: `GITHUB_ACTIONS_TRADING.md`
