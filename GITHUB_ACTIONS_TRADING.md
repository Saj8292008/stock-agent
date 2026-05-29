# 🤖 GitHub Actions Automated Trading

**Run your stock-agent trading bot in the cloud for FREE using GitHub Actions!**

---

## 🎯 Overview

**What is this?**
Your stock-agent can run automatically every 5 minutes during market hours using GitHub Actions - completely free!

**How it works:**
1. ✅ GitHub Actions runs on schedule (every 5 min during market hours)
2. ✅ Fetches current stock prices
3. ✅ Executes trading logic (buy-the-dip, take-profit, stop-loss)
4. ✅ Saves database between runs (portfolio persists!)
5. ✅ Creates trading summaries you can view

**Cost:** FREE (GitHub provides 2,000 minutes/month free for public repos, unlimited for public repos)

---

## ⚡ Quick Setup (5 Minutes)

### **Step 1: Enable GitHub Actions**

GitHub Actions is already enabled for your repo! The workflow is ready to go.

### **Step 2: Add Secrets (Optional)**

If you want to enable Alpaca broker integration:

1. Go to your GitHub repo: `https://github.com/Saj8292008/stock-agent`
2. Click **"Settings"** tab
3. Click **"Secrets and variables"** → **"Actions"**
4. Click **"New repository secret"**
5. Add these secrets:

```
BROKER_ENABLED = false  (or true for Alpaca)
TRADINGVIEW_ENABLED = true
ENABLE_RISK_MANAGER = true
EMERGENCY_STOP = false
ALPACA_API_KEY = your_alpaca_key (if BROKER_ENABLED=true)
ALPACA_API_SECRET = your_alpaca_secret (if BROKER_ENABLED=true)
ALPACA_PAPER_MODE = true
```

**For paper trading only:** You don't need to add any secrets! It works with defaults.

### **Step 3: Enable Workflow**

The workflow file is already created in `.github/workflows/trading-cycle.yml`

It will automatically:
- ✅ Run every 5 minutes during market hours (9:30 AM - 4:00 PM ET, Mon-Fri)
- ✅ Skip when market is closed
- ✅ Save your database between runs
- ✅ Create trading summaries

### **Step 4: Manual Trigger (Test Now)**

1. Go to **"Actions"** tab in GitHub
2. Click **"Automated Trading Cycle"** workflow (left sidebar)
3. Click **"Run workflow"** → **"Run workflow"** button
4. Wait 1-2 minutes for completion
5. Click on the run to see results

✅ **Done! Your bot is running!**

---

## 📊 How It Works

### **Schedule**

The bot runs automatically:
- **Market hours:** 9:30 AM - 4:00 PM ET (Monday - Friday)
- **Frequency:** Every 5 minutes
- **Automatic:** No action needed from you

**Cron schedule breakdown:**
```yaml
# 9:30-9:59 AM ET (every 5 minutes)
- cron: '30-59/5 14 * * 1-5'

# 10:00 AM - 4:00 PM ET (every 5 minutes)
- cron: '*/5 15-20 * * 1-5'

# 4:00 PM ET (final cycle)
- cron: '0 21 * * 1-5'
```

**Times are in UTC:**
- NYSE opens 9:30 AM ET = 14:30 UTC
- NYSE closes 4:00 PM ET = 21:00 UTC

### **What Happens Each Cycle**

1. **Checkout code** - Gets latest version from GitHub
2. **Setup Python** - Installs Python 3.11
3. **Install dependencies** - Installs required packages
4. **Restore database** - Loads your portfolio from previous run
5. **Run trading cycle:**
   - Fetch current prices (yfinance)
   - Check for buy signals (stock down 5%+)
   - Check for sell signals (take profit +10%, stop loss -7%)
   - Execute trades if signals present
6. **Show results** - Prints trades and portfolio status
7. **Save database** - Stores updated portfolio for next run
8. **Create summary** - Generates trading report

---

## 📈 Monitoring Your Bot

### **View Workflow Runs**

1. Go to **"Actions"** tab
2. See all trading cycles
3. Click any run to see details

**Each run shows:**
- ✅ Trades executed
- ✅ Portfolio status
- ✅ Recent trade history
- ✅ Summary report

### **Download Trading Data**

1. Go to workflow run
2. Scroll to **"Artifacts"** section
3. Download:
   - `portfolio-database` - Your SQLite database
   - `trading-summary` - Trading report

### **View Trading Summary**

Each run creates a summary in the workflow:
1. Click on a workflow run
2. Scroll to **"Summary"** section
3. See:
   - Portfolio value
   - Cash balance
   - Open positions
   - Recent trades

---

## 🎮 Manual Controls

### **Run Cycle Manually**

1. Go to **"Actions"** tab
2. Click **"Automated Trading Cycle"**
3. Click **"Run workflow"** → **"Run workflow"**
4. Wait for completion

**Use when:**
- Testing the bot
- Want immediate trade execution
- Market just opened/closed

### **Stop Trading**

**Option 1: Disable workflow**
1. Open `.github/workflows/trading-cycle.yml`
2. Add `# ` before each `cron:` line (comments them out)
3. Commit and push

**Option 2: Emergency stop**
1. Go to **"Settings"** → **"Secrets and variables"** → **"Actions"**
2. Set `EMERGENCY_STOP = true`
3. All trading stops immediately

**Option 3: Delete workflow file**
1. Delete `.github/workflows/trading-cycle.yml`
2. Commit and push

### **Resume Trading**

1. Re-enable workflow (undo above steps)
2. Or set `EMERGENCY_STOP = false`

---

## 💾 Database Persistence

### **How Database is Saved**

Your portfolio database (`stock_agent.db`) is saved as a GitHub Actions artifact:
- ✅ Uploaded after each run
- ✅ Downloaded before next run
- ✅ Retained for 90 days
- ✅ Portfolio survives between runs

**This means:**
- Your trades persist
- Cash balance persists
- Positions persist
- Everything continues from last run

### **Download Your Database**

1. Go to any workflow run
2. Scroll to **"Artifacts"**
3. Download `portfolio-database`
4. Unzip to get `stock_agent.db`

**Use locally:**
```bash
# Replace local database with downloaded one
cp ~/Downloads/stock_agent.db .
python cli.py status
```

### **Upload Database to GitHub Actions**

If you've been trading locally and want to continue in GitHub Actions:

1. Commit your `stock_agent.db` to repo (one-time)
2. Push to GitHub
3. Workflow will use it automatically

**Or** manually upload as artifact (advanced).

---

## ⚠️ Important Limitations

### **GitHub Actions Constraints**

1. **No real-time webhooks**
   - ❌ Can't receive TradingView webhooks
   - ✅ Can run scheduled cycles every 5 min
   - ✅ Use Railway/Render for webhooks

2. **Workflow concurrency**
   - Only 1 run at a time
   - If cycle takes > 5 min, next one waits

3. **Network access**
   - ✅ Can fetch stock prices (yfinance)
   - ✅ Can call Alpaca API (if configured)

4. **Free tier limits**
   - 2,000 minutes/month for private repos
   - Unlimited for public repos
   - Each cycle takes ~1-2 minutes
   - ~300-600 cycles/month on free tier (plenty!)

### **What GitHub Actions is Good For**

✅ **Perfect for:**
- Scheduled trading (every 5 min)
- Buy-the-dip strategy
- Automated position management
- Paper trading
- Alpaca broker integration
- Cost-free automation

❌ **Not ideal for:**
- TradingView webhooks (use Railway/Render)
- Real-time responses (5 min delay)
- High-frequency trading (seconds/minutes)

---

## 🔧 Customization

### **Change Schedule**

Edit `.github/workflows/trading-cycle.yml`:

**Every 10 minutes:**
```yaml
schedule:
  - cron: '30-59/10 14 * * 1-5'
  - cron: '*/10 15-20 * * 1-5'
```

**Every 15 minutes:**
```yaml
schedule:
  - cron: '30,45 14 * * 1-5'
  - cron: '*/15 15-20 * * 1-5'
```

**Only at market open/close:**
```yaml
schedule:
  - cron: '30 14 * * 1-5'  # 9:30 AM ET
  - cron: '0 21 * * 1-5'   # 4:00 PM ET
```

### **Add Email Notifications**

Add this step to workflow:
```yaml
- name: Send email notification
  if: always()
  uses: dawidd6/action-send-mail@v3
  with:
    server_address: smtp.gmail.com
    server_port: 465
    username: ${{secrets.EMAIL_USERNAME}}
    password: ${{secrets.EMAIL_PASSWORD}}
    subject: Trading Cycle Complete
    body: Check GitHub Actions for details
    to: your-email@example.com
```

(Requires email secrets configured)

### **Run on Specific Days**

**Only Mondays and Fridays:**
```yaml
schedule:
  - cron: '*/5 14-21 * * 1'  # Monday
  - cron: '*/5 14-21 * * 5'  # Friday
```

---

## 📊 Monitoring Dashboard

### **View in GitHub**

1. **Actions tab** - See all runs
2. **Insights** → **Actions** - Usage statistics
3. **Each run** - Detailed logs

### **Create Status Badge**

Add to your README.md:
```markdown
![Trading Status](https://github.com/Saj8292008/stock-agent/actions/workflows/trading-cycle.yml/badge.svg)
```

Shows: ✅ Passing or ❌ Failing

---

## 🆘 Troubleshooting

### **Workflow Not Running**

**Check:**
1. Is workflow enabled? (Actions tab → workflow → "Enable workflow")
2. Is schedule correct? (Check cron syntax)
3. Is repo public or have Actions minutes? (Settings → Billing)

**Fix:**
- Manually trigger: "Run workflow" button
- Check Actions tab for errors

### **Database Not Persisting**

**Check:**
1. Is artifact being uploaded? (Check "Artifacts" section)
2. Is artifact being downloaded? (Check "Restore database" step)

**Fix:**
- First run creates fresh database
- Subsequent runs load previous state
- Download artifact to verify data

### **Trades Not Executing**

**Check:**
1. Are signals present? (Check workflow logs)
2. Is emergency stop enabled? (Check secrets)
3. Is risk manager blocking? (Check logs for rejection)

**Fix:**
- Run manually to debug
- Check portfolio status in logs
- Verify prices are fetched

### **"No trades executed"**

**This is normal!** Means:
- No buy signals (stocks not down 5%+)
- No sell signals (no take-profit/stop-loss hit)
- Just monitoring, no action needed

**The bot is working correctly.**

---

## 💡 Pro Tips

### **1. Test First**

Before relying on automation:
```bash
# Test locally
python cli.py run-cycle

# Then test in GitHub Actions
# Actions → Run workflow → Manually trigger
```

### **2. Monitor Daily**

Check GitHub Actions tab daily:
- Review executed trades
- Verify portfolio status
- Check for errors

### **3. Download Database Weekly**

Backup your portfolio:
- Download `portfolio-database` artifact
- Keep local copy
- Can restore if needed

### **4. Use with CLI**

Download database, then use CLI locally:
```bash
python cli.py status
python cli.py trades
```

Best of both worlds!

### **5. Combine with TradingView**

Use both:
- **GitHub Actions**: Scheduled trading (every 5 min)
- **Railway/Render**: TradingView webhooks (real-time)
- Separate databases or sync between them

---

## 🎯 Example Workflow

### **Week 1: Testing**

**Day 1:**
- ✅ Push workflow to GitHub
- ✅ Manually trigger test run
- ✅ Verify trades execute

**Day 2-7:**
- ✅ Let run automatically
- ✅ Check Actions tab daily
- ✅ Review trades and portfolio

### **Week 2+: Production**

- ✅ Monitor weekly
- ✅ Download database backups
- ✅ Adjust strategy if needed
- ✅ Enable Alpaca if ready

---

## 🆚 GitHub Actions vs Other Options

| Feature | GitHub Actions | Railway | Render |
|---------|---------------|---------|--------|
| **Cost** | Free | $5/mo | $7/mo |
| **Setup** | 5 min | 10 min | 15 min |
| **TradingView Webhooks** | ❌ No | ✅ Yes | ✅ Yes |
| **Scheduled Trading** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Database Persistence** | ✅ Yes (artifacts) | ✅ Yes | ✅ Yes |
| **Best For** | Scheduled trading | Webhooks + Scheduled | Budget webhooks |

**Recommendation:**
- **Start with GitHub Actions** (free, easy)
- **Add Railway/Render later** (if you need TradingView webhooks)
- **Use both together** (Actions for scheduled, Railway for webhooks)

---

## 📋 Quick Start Checklist

- [x] Workflow file created (`.github/workflows/trading-cycle.yml`)
- [ ] Secrets added (optional, for Alpaca)
- [ ] Manually test workflow run
- [ ] Verify trades execute
- [ ] Check database persists
- [ ] Monitor daily for first week
- [ ] Download database backup

---

## 🎉 You're Ready!

Your stock-agent is now running in the cloud, completely free, with GitHub Actions!

**Next steps:**
1. ✅ Go to Actions tab
2. ✅ Manually trigger first run
3. ✅ Check results
4. ✅ Let it run automatically

**Your bot will trade every 5 minutes during market hours!** 🚀📈

---

## 📚 Related Documentation

- **CLI Usage:** `CLI_GUIDE.md`
- **TradingView Setup:** `TRADINGVIEW_SETUP.md`
- **Railway Deployment:** `DEPLOY_RAILWAY.md`
- **Strategy Guide:** `MY_FIRST_STRATEGY.md`

---

**Questions?** Check the workflow logs in the Actions tab for detailed execution information.
