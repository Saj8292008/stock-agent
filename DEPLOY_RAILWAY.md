# 🚂 Deploy to Railway.app

**Deploy your stock-agent to Railway in 10 minutes - zero code changes needed!**

---

## ✅ Why Railway?

- ✅ **Persistent SQLite** - Your database doesn't get wiped
- ✅ **Always-on server** - No cold starts
- ✅ **Free tier** - 500 hours/month ($5 credit)
- ✅ **Automatic HTTPS** - TradingView webhooks work
- ✅ **Zero config** - Detects Python automatically
- ✅ **One-click deploy** - From GitHub

---

## 🚀 Step-by-Step Deployment

### **Step 1: Sign Up for Railway (2 min)**

1. Go to: **https://railway.app**
2. Click **"Login"**
3. Choose **"Sign in with GitHub"**
4. Authorize Railway to access your GitHub repos

✅ **Account created!**

---

### **Step 2: Create New Project (2 min)**

1. Click **"New Project"** (top right)
2. Select **"Deploy from GitHub repo"**
3. Choose: **Saj8292008/stock-agent**
4. Click **"Deploy Now"**

Railway will:
- ✅ Clone your repo
- ✅ Detect Python
- ✅ Install dependencies
- ✅ Start your server

**Wait 2-3 minutes for initial deployment...**

---

### **Step 3: Add Environment Variables (3 min)**

1. Click on your service (in the project dashboard)
2. Click **"Variables"** tab
3. Click **"+ New Variable"**
4. Add these one by one:

```bash
TRADINGVIEW_ENABLED=true
TRADINGVIEW_PASSPHRASE=Eo8rD83SnDlzGadIBbILUpBetX0vx4LnwgEzvT_PQYg
BROKER_ENABLED=false
ENABLE_RISK_MANAGER=true
EMERGENCY_STOP=false
ALPACA_PAPER_MODE=true
ALPACA_API_KEY=test_key
ALPACA_API_SECRET=test_secret
```

5. Railway will **automatically redeploy** with new variables

---

### **Step 4: Generate Public Domain (2 min)**

1. Go to **"Settings"** tab
2. Scroll to **"Networking"** section
3. Click **"Generate Domain"**
4. Railway creates URL like: `stock-agent-production.up.railway.app`

**Copy this URL!** This is your webhook URL.

✅ **Your server is live with HTTPS!**

---

### **Step 5: Test Your Deployment (1 min)**

**Test from browser or phone:**

```
https://your-app-name.up.railway.app/api/portfolio
```

**Expected response:**
```json
{
  "cash": 100000.0,
  "positions": [],
  "total_value": 100000.0
}
```

✅ **Server is working!**

---

## 📱 **Your TradingView Webhook URL**

**Use this in all TradingView alerts:**

```
https://your-app-name.up.railway.app/api/webhook/tradingview
```

Replace `your-app-name` with your actual Railway domain.

---

## 🔍 **Monitoring Your Deployment**

### **View Logs**

1. Click on your service
2. Go to **"Deployments"** tab
3. Click latest deployment
4. Click **"View Logs"**

**Useful for:**
- Checking if server started
- Debugging webhook issues
- Seeing TradingView signals received

### **Check Metrics**

1. Go to **"Metrics"** tab
2. See:
   - CPU usage
   - Memory usage
   - Network traffic
   - Request count

---

## 💰 **Pricing & Usage**

### **Free Tier (Trial)**

- **$5 in credits** (one time)
- **500 hours/month** of usage
- **Perfect for testing** - lasts ~20 days of 24/7 usage

### **After Trial**

- **$5/month** for basic usage
- Pay as you grow
- No hidden fees

### **Usage Monitoring**

Check usage in Railway dashboard:
1. Click **"Usage"** (left sidebar)
2. See current credit balance
3. View detailed breakdown

---

## 🔧 **Advanced Configuration**

### **Persistent Volume (Optional)**

If you want guaranteed database persistence:

1. Go to **"Settings"** tab
2. Scroll to **"Volumes"**
3. Click **"+ Add Volume"**
4. **Mount path:** `/app/data`
5. **Size:** 1GB (free)

Then update database path in code to use `/app/data/stock_agent.db`.

**Note:** Not required for basic usage - Railway already persists files.

### **Custom Start Command**

If Railway doesn't auto-detect correctly:

1. Go to **"Settings"** tab
2. **Start Command:** `python serve.py`
3. **Build Command:** `pip install -r requirements.txt`

Usually not needed - Railway auto-detects!

---

## 🆘 **Troubleshooting**

### **Deployment Failed**

**Check:**
1. Go to **"Deployments"** → Click failed deployment
2. View **"Build Logs"**
3. Look for error messages

**Common issues:**
- Missing `requirements.txt` (❌ your repo has it ✅)
- Python version mismatch (Railway uses 3.11 by default)
- Missing dependencies

**Solution:** Check logs, fix issue, push to GitHub (auto-redeploys)

### **Server Not Responding**

**Check:**
1. View **"Logs"** to see if server started
2. Look for: `Uvicorn running on http://0.0.0.0:8000`
3. Check **"Metrics"** for crashes

**Common causes:**
- Port binding issue (Railway uses `PORT` env var)
- Crash on startup
- Missing environment variables

**Solution:** Check your `serve.py` uses correct port binding

### **Database Not Persisting**

**Check:**
1. SQLite file location (`stock_agent.db`)
2. Should be in `/app` directory (Railway default)

**Solution:** Add persistent volume (see Advanced Configuration)

### **TradingView Webhook Fails**

**Check:**
1. Webhook URL correct? (`https://your-app.up.railway.app/api/webhook/tradingview`)
2. Passphrase matches?
3. Server logs show request received?

**Test manually:**
```bash
curl -X POST https://your-app.up.railway.app/api/webhook/tradingview \
  -H "Content-Type: application/json" \
  -d '{
    "passphrase": "Eo8rD83SnDlzGadIBbILUpBetX0vx4LnwgEzvT_PQYg",
    "ticker": "AAPL",
    "action": "buy",
    "price": 150.0
  }'
```

---

## 🔄 **Updates & Redeployment**

### **Automatic Deployment**

Railway watches your GitHub repo:
- ✅ Push to main → Auto deploys
- ✅ Zero downtime
- ✅ Rollback available

**To update:**
```bash
git add .
git commit -m "Update feature"
git push origin main
```

Railway redeploys automatically in 2-3 minutes!

### **Manual Redeploy**

1. Go to **"Deployments"** tab
2. Click **"⋮"** on any deployment
3. Click **"Redeploy"**

### **Rollback**

If new deployment breaks:
1. Go to **"Deployments"**
2. Find working deployment
3. Click **"⋮"** → **"Redeploy"**

---

## 📊 **Production Checklist**

Before going live with real trading:

- [ ] Server deployed and running
- [ ] Database persisting correctly
- [ ] Environment variables set
- [ ] HTTPS domain generated
- [ ] TradingView webhooks tested
- [ ] Monitoring logs regularly
- [ ] Credits/billing configured
- [ ] Backup strategy planned
- [ ] Emergency stop tested
- [ ] Risk limits configured

---

## 🔐 **Security Best Practices**

### **Environment Variables**

✅ **DO:**
- Store all secrets in Railway Variables
- Use strong passphrase
- Rotate credentials periodically

❌ **DON'T:**
- Commit `.env` to git
- Share passphrase publicly
- Use default/test passphrases

### **Access Control**

- Only you have Railway dashboard access
- TradingView passphrase protects webhook
- Consider IP whitelisting (Railway Pro)

---

## 💡 **Pro Tips**

### **1. Use Railway CLI**

Install Railway CLI for advanced control:
```bash
npm install -g @railway/cli
railway login
railway link  # Link to your project
railway logs  # View logs from terminal
railway run python main.py  # Run commands remotely
```

### **2. Set Up Notifications**

Get notified of deployments:
1. Go to project settings
2. Enable **"Deployment Notifications"**
3. Connect Slack/Discord/Email

### **3. Monitor Database Size**

Railway free tier includes storage:
- Check database size regularly
- Archive old trades if needed
- Keep database under 1GB for free tier

### **4. Optimize for Performance**

- Use Railway's built-in caching
- Enable HTTP/2
- Consider Railway's proxy for better latency

---

## 🎯 **Quick Start Summary**

1. ✅ Sign up: https://railway.app
2. ✅ Deploy from GitHub: `Saj8292008/stock-agent`
3. ✅ Add environment variables
4. ✅ Generate domain
5. ✅ Test: `https://your-app.up.railway.app/api/portfolio`
6. ✅ Use in TradingView: `https://your-app.up.railway.app/api/webhook/tradingview`

**Total time: ~10 minutes**
**Cost: Free trial ($5 credit), then $5/month**

---

## 🆚 **Railway vs Vercel**

| Feature | Railway | Vercel |
|---------|---------|--------|
| **Persistent DB** | ✅ Yes | ❌ No (needs external DB) |
| **Always-on** | ✅ Yes | ❌ Serverless (cold starts) |
| **SQLite** | ✅ Works | ❌ Doesn't persist |
| **Setup time** | 10 min | 30+ min (DB setup) |
| **Code changes** | ✅ None | ❌ Major refactor |
| **Cost** | $5/mo | Free tier limited |
| **Best for** | ✅ Stock-agent | Static sites, APIs |

**Verdict: Railway is perfect for stock-agent!**

---

## 📚 **Additional Resources**

- **Railway Docs:** https://docs.railway.app
- **Railway Discord:** https://discord.gg/railway
- **Status Page:** https://status.railway.app

---

## 🎉 **You're Ready to Deploy!**

Railway is the easiest way to deploy your stock-agent with zero code changes. Your SQLite database persists, webhooks work perfectly, and you get automatic HTTPS.

**Next:** Follow the 5 steps above and you'll be live in 10 minutes! 🚀
