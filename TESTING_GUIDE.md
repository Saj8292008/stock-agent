# Testing Guide for Stock-Agent Trading System

This guide walks you through testing your TradingView-connected trading system safely before deploying with real money.

## Testing Phases Overview

1. **Phase 1: Local Paper Trading** (30 minutes) - Test core functionality without broker
2. **Phase 2: Alpaca Paper Trading** (1-2 hours) - Test broker integration with fake money
3. **Phase 3: TradingView Integration** (1 hour) - Test webhook signals
4. **Phase 4: Live Monitoring** (1-2 weeks) - Run paper trading continuously
5. **Phase 5: Small Live Testing** (optional) - Start with minimal real capital

---

## Prerequisites

- Python 3.8+ installed
- Node.js 16+ installed (for frontend)
- Git repository cloned
- Internet connection

---

## Phase 1: Local Paper Trading (No Broker Required)

**Goal:** Verify the system works without any external APIs.

### Step 1.1: Set Up Environment

```bash
# Navigate to project directory
cd /workspace/claude-workspace/msgftdstkv_privaterelay.appleid.com/Saj8292008/stock-agent

# Create .env file (pure paper trading)
cat > .env << 'EOF'
# Paper Trading Mode (No Broker)
BROKER_ENABLED=false
TRADINGVIEW_ENABLED=false
ENABLE_RISK_MANAGER=true
EMERGENCY_STOP=false

# Not needed for paper trading but set to avoid warnings
ALPACA_API_KEY=paper_key_placeholder
ALPACA_API_SECRET=paper_secret_placeholder
ALPACA_PAPER_MODE=true
TRADINGVIEW_PASSPHRASE=test-passphrase-123
EOF

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
npm install --prefix frontend
```

### Step 1.2: Initialize Database

```bash
# Initialize the database with migrations
python -c "from backend.portfolio import init_db; init_db()"

# Verify database was created
ls -lh portfolio.db

# Should see: portfolio.db (~100KB file)
```

### Step 1.3: Start Backend Server

```bash
# Start the FastAPI backend
python serve.py

# Expected output:
# INFO:     Started server process [XXXX]
# INFO:     Waiting for application startup.
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Test Backend:** Open http://localhost:8000 in browser - should see welcome message.

### Step 1.4: Start Frontend Dashboard

**In a new terminal:**

```bash
cd /workspace/claude-workspace/msgftdstkv_privaterelay.appleid.com/Saj8292008/stock-agent

# Start React development server
npm run dev --prefix frontend

# Expected output:
# VITE ready in XXX ms
# Local: http://localhost:5173/
```

**Test Dashboard:** Open http://localhost:5173 - should see trading dashboard.

### Step 1.5: Verify Paper Trading

**Test Checklist:**

1. **Check Portfolio Display**
   - Should show $100,000 cash
   - No open positions initially
   - No trade history

2. **Test Manual Cycle**
   - Click "Run Trade Cycle" button
   - Watch for actions (should see price checks)
   - Check trades table for any buys (if prices meet buy-dip threshold)

3. **Test API Endpoints**
   ```bash
   # Test portfolio endpoint
   curl http://localhost:8000/api/portfolio

   # Test risk limits
   curl http://localhost:8000/api/risk-limits

   # Test config status
   curl http://localhost:8000/api/config-status
   ```

4. **Test Position Accumulation Fix**
   ```bash
   # Manually buy same stock twice to verify accumulation works
   # This tests the critical fix from commit d780722

   # You can do this by triggering cycles that buy the same stock
   curl -X POST http://localhost:8000/api/run-cycle
   # Wait a bit, then run again
   curl -X POST http://localhost:8000/api/run-cycle

   # Check positions - shares should accumulate, not overwrite
   curl http://localhost:8000/api/portfolio | jq .positions
   ```

5. **Test Emergency Stop**
   ```bash
   # Activate emergency stop
   curl -X POST http://localhost:8000/api/emergency-stop

   # Try to run cycle - should be blocked
   curl -X POST http://localhost:8000/api/run-cycle

   # Restart server and verify emergency stop persists
   # Stop server (Ctrl+C)
   python serve.py
   # Check config - should show emergency_stop: true
   curl http://localhost:8000/api/config-status

   # Disable emergency stop by editing database
   sqlite3 portfolio.db "UPDATE portfolio SET emergency_stop = 0 WHERE id = 1"
   # Restart server again
   ```

**Expected Results:**
- ✅ Dashboard loads without errors
- ✅ Portfolio shows correct cash balance
- ✅ Manual cycles execute (may or may not trade depending on prices)
- ✅ Positions accumulate correctly when buying same stock
- ✅ Emergency stop persists across restarts
- ✅ API endpoints return valid JSON

**Duration:** 30 minutes

---

## Phase 2: Alpaca Paper Trading (Broker Integration)

**Goal:** Test real broker integration with simulated money.

### Step 2.1: Create Alpaca Paper Trading Account

1. **Sign up at Alpaca:** https://alpaca.markets
2. **Go to Paper Trading:** Click "Go to Paper Trading" in dashboard
3. **Get API Keys:**
   - Navigate to "Your API Keys" in left sidebar
   - Click "Generate New Keys"
   - Save both API Key and Secret Key (you won't see secret again!)

### Step 2.2: Update Environment Configuration

```bash
# Edit .env file
cat > .env << 'EOF'
# Alpaca Paper Trading Configuration
ALPACA_API_KEY=PK...your_paper_key_here
ALPACA_API_SECRET=...your_paper_secret_here
ALPACA_PAPER_MODE=true

# Enable broker but keep TradingView disabled for now
BROKER_ENABLED=true
TRADINGVIEW_ENABLED=false
ENABLE_RISK_MANAGER=true
EMERGENCY_STOP=false

TRADINGVIEW_PASSPHRASE=test-passphrase-123
EOF

# Restart backend server
# (Stop with Ctrl+C and start again)
python serve.py
```

### Step 2.3: Verify Broker Connection

```bash
# Test broker account endpoint
curl http://localhost:8000/api/account

# Expected response:
# {
#   "cash": 100000.0,
#   "buying_power": 100000.0,
#   "portfolio_value": 100000.0,
#   ...
# }

# Test configuration
curl http://localhost:8000/api/config-status

# Should show:
# "broker_mode": "PAPER"
```

### Step 2.4: Test Broker Order Execution

**Test 1: Manual Buy Order**

```bash
# Run a manual cycle with broker enabled
curl -X POST http://localhost:8000/api/run-cycle

# Check orders table
curl http://localhost:8000/api/orders

# Should see broker_order_id, status, filled_qty
```

**Test 2: Position Synchronization**

```bash
# Sync positions from broker
curl -X POST http://localhost:8000/api/sync-positions

# Check portfolio
curl http://localhost:8000/api/portfolio

# Compare with Alpaca dashboard: https://app.alpaca.markets/paper/dashboard/overview
```

**Test 3: Risk Manager Validation**

```bash
# Check risk status
curl http://localhost:8000/api/risk-status

# Try to violate position size limit
# (This would require modifying limits or forcing a large order)
curl -X PUT http://localhost:8000/api/risk-limits \
  -H "Content-Type: application/json" \
  -d '{"max_position_size": 0.05}'

# Run cycle - should respect new 5% limit
curl -X POST http://localhost:8000/api/run-cycle
```

**Test 4: Order Lifecycle**

Monitor an order from submission to fill:

```bash
# Submit order
curl -X POST http://localhost:8000/api/run-cycle

# Immediately check orders
curl http://localhost:8000/api/orders | jq '.[0]'

# Should see:
# - status: "submitted" or "filled"
# - broker_order_id: (Alpaca order ID)
# - filled_qty: (shares filled)
```

### Step 2.5: Verify in Alpaca Dashboard

1. **Login to Alpaca Paper Trading:** https://app.alpaca.markets/paper/dashboard/overview
2. **Check Positions:** Should match your local database
3. **Check Orders:** Should see orders submitted by your system
4. **Check Activity:** View order history

**Expected Results:**
- ✅ Broker connection successful
- ✅ Orders submitted to Alpaca
- ✅ Positions synchronized correctly
- ✅ Risk manager validates orders
- ✅ Order status tracked (submitted → filled)
- ✅ Alpaca dashboard matches local data

**Duration:** 1-2 hours

---

## Phase 3: TradingView Webhook Integration

**Goal:** Test TradingView alert signals trigger trades.

### Step 3.1: Enable TradingView

```bash
# Update .env
cat > .env << 'EOF'
# Full Integration Mode
ALPACA_API_KEY=PK...your_paper_key_here
ALPACA_API_SECRET=...your_paper_secret_here
ALPACA_PAPER_MODE=true
BROKER_ENABLED=true
TRADINGVIEW_ENABLED=true
ENABLE_RISK_MANAGER=true
EMERGENCY_STOP=false
TRADINGVIEW_PASSPHRASE=my-secure-passphrase-123
EOF

# Restart server
python serve.py
```

### Step 3.2: Test Webhook Locally

**Test with curl (simulating TradingView):**

```bash
# Test valid webhook
curl -X POST http://localhost:8000/api/webhook/tradingview \
  -H "Content-Type: application/json" \
  -d '{
    "passphrase": "my-secure-passphrase-123",
    "ticker": "NASDAQ:GOOGL",
    "action": "buy",
    "strategy": "test_strategy",
    "price": 150.0,
    "contracts": 10
  }'

# Expected response:
# {"status": "signal_received", "signal_id": 1}

# Check signals table
curl http://localhost:8000/api/signals

# Check if order was created
curl http://localhost:8000/api/orders
```

**Test invalid passphrase (should fail):**

```bash
curl -X POST http://localhost:8000/api/webhook/tradingview \
  -H "Content-Type: application/json" \
  -d '{
    "passphrase": "wrong-password",
    "ticker": "NASDAQ:GOOGL",
    "action": "buy"
  }'

# Expected response:
# {"detail": "Invalid passphrase"}
```

### Step 3.3: Expose Webhook to Internet

**Option A: Using ngrok (recommended for testing)**

```bash
# Install ngrok: https://ngrok.com/download
# Or: brew install ngrok (macOS)

# Start ngrok tunnel
ngrok http 8000

# You'll see output like:
# Forwarding: https://abc123.ngrok.io -> http://localhost:8000

# Your webhook URL is:
# https://abc123.ngrok.io/api/webhook/tradingview
```

**Option B: Using the built-in tunnel (if available)**

```bash
# Check if tunnel is available
curl http://localhost:8000/api/config-status | jq .tunnel_url
```

### Step 3.4: Configure TradingView Alert

1. **Login to TradingView:** https://www.tradingview.com
2. **Open a chart** for a stock (e.g., GOOGL)
3. **Create Alert:**
   - Click Alert button (clock icon) at top
   - Set condition (e.g., "Crossing" a moving average)
   - Set "Alert actions" → check "Webhook URL"
   - Enter your webhook URL: `https://abc123.ngrok.io/api/webhook/tradingview`
   - Set "Message" to:

   ```json
   {
     "passphrase": "my-secure-passphrase-123",
     "ticker": "{{ticker}}",
     "action": "buy",
     "strategy": "ma_crossover",
     "price": {{close}},
     "contracts": 10,
     "time": "{{time}}"
   }
   ```

4. **Test Alert:** Click "Test" to send test webhook
5. **Create Alert:** Click "Create"

### Step 3.5: Monitor Webhook Signals

```bash
# Watch logs for incoming webhooks
tail -f serve.py.log

# Check signals received
curl http://localhost:8000/api/signals | jq

# Check orders created from signals
curl http://localhost:8000/api/orders | jq 'map(select(.source == "tradingview"))'
```

**Expected Results:**
- ✅ Local webhook test succeeds
- ✅ Invalid passphrase rejected
- ✅ ngrok tunnel exposes webhook
- ✅ TradingView test alert received
- ✅ Signal logged to database
- ✅ Order created and submitted to Alpaca

**Duration:** 1 hour

---

## Phase 4: Live Monitoring (Continuous Paper Trading)

**Goal:** Run the system continuously for 1-2 weeks to validate stability.

### Step 4.1: Start Continuous Trading

**Option A: Market Hours Mode (recommended)**

```bash
# Runs only during market hours (9:30 AM - 4:00 PM ET, Mon-Fri)
python autorun.py

# This will:
# - Check if market is open
# - Run cycles every 5 minutes during market hours
# - Sleep until next market open when closed
```

**Option B: Continuous Mode (24/7)**

```bash
# Runs cycles every 5 minutes, always
python main.py

# Note: This will try to trade even when market is closed
# Use market hours mode for realistic testing
```

### Step 4.2: Monitor System Health

**Daily Checks:**

```bash
# Check portfolio performance
curl http://localhost:8000/api/portfolio | jq '{cash, positions, total_value}'

# Check daily metrics
curl http://localhost:8000/api/daily-metrics | jq '.[-7:]'  # Last 7 days

# Check risk status
curl http://localhost:8000/api/risk-status

# Check for errors in logs
tail -100 serve.py.log | grep -i error
```

**What to Monitor:**

1. **Portfolio Value Trend**
   - Is it growing, stable, or declining?
   - Compare to buy-and-hold strategy

2. **Trade Frequency**
   - How many trades per day?
   - Are you over-trading or under-trading?

3. **Win Rate**
   ```bash
   # Calculate win rate from trades
   curl http://localhost:8000/api/trades?limit=100 | jq '
     group_by(.action) |
     map({action: .[0].action, count: length})'
   ```

4. **Risk Limit Violations**
   - Check audit log for rejected orders
   ```bash
   sqlite3 portfolio.db "SELECT * FROM audit_log WHERE result = 'FAILURE' ORDER BY timestamp DESC LIMIT 10"
   ```

5. **System Uptime**
   - Is the system staying online?
   - Any crashes or restarts?

### Step 4.3: Dashboard Monitoring

Keep the dashboard open: http://localhost:5173

**Monitor:**
- Portfolio value chart (should update every 60 seconds)
- Trade history (verify trades make sense)
- Position P&L (are positions profitable?)
- Signal status (if using TradingView)

### Step 4.4: Weekly Review

**Every Friday (or weekly):**

```bash
# Export weekly report
curl http://localhost:8000/api/daily-metrics | jq '.[-7:]' > weekly_report_$(date +%Y%m%d).json

# Calculate key metrics:
# - Total return %
# - Number of trades
# - Win rate
# - Max drawdown
# - Sharpe ratio (if implemented)

# Review trades
curl http://localhost:8000/api/trades?limit=100 > trades_$(date +%Y%m%d).json
```

**Questions to Answer:**

1. Is the strategy profitable in paper trading?
2. Are risk limits being respected?
3. Is position sizing appropriate?
4. Are there any unexpected behaviors?
5. How does it compare to simply holding the stocks?

**Expected Results After 1-2 Weeks:**
- ✅ System runs continuously without crashes
- ✅ Trades execute as expected
- ✅ Risk limits are respected
- ✅ No data integrity issues
- ✅ Performance is acceptable (positive or learning from losses)

**Duration:** 1-2 weeks continuous running

---

## Phase 5: Small Live Testing (Optional - Real Money)

**⚠️ WARNING: This phase uses real money. Only proceed if:**
- Phase 1-4 completed successfully
- You're comfortable with the strategy
- You understand the risks
- You've reviewed all code and security measures

### Step 5.1: Prepare for Live Trading

**Checklist before going live:**

- [ ] Paper trading ran successfully for 1-2 weeks
- [ ] No critical bugs or issues found
- [ ] Strategy shows promise (positive or acceptable returns)
- [ ] Risk limits are properly configured
- [ ] Emergency stop works correctly
- [ ] You've read and understand CLAUDE.md
- [ ] You have backup plan if things go wrong
- [ ] You're using money you can afford to lose

### Step 5.2: Enable Live Trading

```bash
# Update .env to live mode
cat > .env << 'EOF'
# ⚠️ LIVE TRADING MODE - REAL MONEY AT RISK ⚠️
ALPACA_API_KEY=PK...your_LIVE_key_here
ALPACA_API_SECRET=...your_LIVE_secret_here
ALPACA_PAPER_MODE=false  # ⚠️ LIVE TRADING

BROKER_ENABLED=true
TRADINGVIEW_ENABLED=true
ENABLE_RISK_MANAGER=true
EMERGENCY_STOP=false

TRADINGVIEW_PASSPHRASE=your-secure-production-passphrase
EOF

# Restart server
python serve.py
```

### Step 5.3: Start Small

**Recommended approach:**

1. **Reduce Position Sizes**
   ```bash
   # Lower max position size to 5% instead of 10%
   curl -X PUT http://localhost:8000/api/risk-limits \
     -H "Content-Type: application/json" \
     -d '{"max_position_size": 0.05, "max_daily_loss": -0.01}'
   ```

2. **Reduce Capital**
   - Start with $1,000-5,000 instead of $100,000
   - Only trade 1-2 stocks initially
   - Increase gradually as confidence builds

3. **Manual Approval (optional)**
   - Disable automated trading
   - Review signals manually
   - Execute trades manually through dashboard

### Step 5.4: Monitor Closely

**For the first week of live trading:**

- Check dashboard every 1-2 hours during market hours
- Review every trade immediately after execution
- Watch for unexpected behavior
- Be ready to hit emergency stop if needed

**Emergency Stop Procedure:**

```bash
# If anything goes wrong:
curl -X POST http://localhost:8000/api/emergency-stop

# This will:
# 1. Close all open positions
# 2. Block new orders
# 3. Set persistent flag in database
```

### Step 5.5: Scale Gradually

If successful after 1 week:
- Increase position sizes gradually
- Add more stocks to trading universe
- Increase capital allocated
- Enable more advanced strategies

**Expected Results:**
- ✅ Live trades execute correctly
- ✅ Risk limits protect capital
- ✅ No unexpected losses
- ✅ Strategy performs similar to paper trading
- ✅ Emergency stop ready if needed

**Duration:** Ongoing

---

## Testing Checklist Summary

### Before Starting
- [ ] Python 3.8+ installed
- [ ] Node.js 16+ installed
- [ ] Repository cloned
- [ ] Dependencies installed

### Phase 1: Paper Trading
- [ ] Database initialized
- [ ] Backend server starts
- [ ] Frontend dashboard loads
- [ ] Manual cycle executes
- [ ] Position accumulation works
- [ ] Emergency stop persists

### Phase 2: Broker Integration
- [ ] Alpaca paper account created
- [ ] API keys configured
- [ ] Broker connection successful
- [ ] Orders submitted to Alpaca
- [ ] Positions synchronized
- [ ] Risk manager validates orders

### Phase 3: TradingView
- [ ] Webhook endpoint works locally
- [ ] Invalid passphrase rejected
- [ ] Tunnel exposes webhook
- [ ] TradingView alert configured
- [ ] Signals received and processed
- [ ] Orders created from signals

### Phase 4: Monitoring
- [ ] System runs continuously 1-2 weeks
- [ ] No crashes or data corruption
- [ ] Performance is acceptable
- [ ] Risk limits respected
- [ ] Ready for live trading decision

### Phase 5: Live Trading (Optional)
- [ ] All checklist items completed
- [ ] Risks understood and accepted
- [ ] Starting with small capital
- [ ] Emergency stop ready
- [ ] Monitoring closely

---

## Troubleshooting

### Server Won't Start

```bash
# Check if port 8000 is in use
lsof -ti :8000 | xargs kill -9

# Check for Python errors
python serve.py
```

### Database Errors

```bash
# Reinitialize database (⚠️ deletes all data)
rm portfolio.db
python -c "from backend.portfolio import init_db; init_db()"
```

### Broker Connection Issues

```bash
# Verify credentials
curl http://localhost:8000/api/config-status | jq .broker_mode

# Test Alpaca API directly
curl -H "APCA-API-KEY-ID: YOUR_KEY" \
     -H "APCA-API-SECRET-KEY: YOUR_SECRET" \
     https://paper-api.alpaca.markets/v2/account
```

### Frontend Won't Load

```bash
# Reinstall dependencies
rm -rf frontend/node_modules
npm install --prefix frontend

# Check backend is running
curl http://localhost:8000/api/portfolio
```

### TradingView Webhook Not Receiving

```bash
# Verify ngrok is running
curl https://YOUR_TUNNEL.ngrok.io/api/config-status

# Check webhook logs
tail -f serve.py.log | grep webhook

# Test webhook manually
curl -X POST https://YOUR_TUNNEL.ngrok.io/api/webhook/tradingview \
  -H "Content-Type: application/json" \
  -d '{"passphrase": "your-passphrase", "ticker": "NASDAQ:GOOGL", "action": "buy"}'
```

---

## Next Steps

After completing testing:

1. **Review Results** - Analyze performance data
2. **Adjust Strategy** - Tune parameters based on results
3. **Improve Risk Management** - Refine position sizing and limits
4. **Add Features** - Implement additional strategies or indicators
5. **Scale Up** - Increase capital gradually if successful

---

## Support

- **Documentation:** See CLAUDE.md for technical details
- **Code Review:** See code review comments in GitHub issue #1
- **Questions:** Create GitHub issues for specific problems

---

## Safety Reminders

- ✅ Always start with paper trading
- ✅ Test thoroughly before using real money
- ✅ Start small with live trading
- ✅ Use risk limits to protect capital
- ✅ Have emergency stop ready
- ✅ Monitor closely during live trading
- ⚠️ Never trade with money you can't afford to lose
- ⚠️ Past performance doesn't guarantee future results
