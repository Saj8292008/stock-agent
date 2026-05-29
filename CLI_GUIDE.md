# 📟 Stock-Agent CLI Guide

**Command-line interface for managing your paper trading portfolio.**

---

## 🚀 Quick Start

### **Basic Usage**

```bash
# From your stock-agent directory
python cli.py [command]
```

---

## 📋 Available Commands

### **1. Portfolio Status** (Most Used)

```bash
python cli.py status
```

**Shows:**
- 💰 Total portfolio value
- 💵 Available cash
- 📊 Current positions with P&L
- 📈 Tracked stocks with signals
- 🎯 Buy/sell targets

**Example Output:**
```
╭─────────────────────────────────────╮
│     Portfolio Summary               │
├─────────────────────────────────────┤
│ Total Value    $102,450.00          │
│ Cash           $ 45,230.00          │
│ Invested       $ 57,220.00          │
│ Total P&L      $ +2,450.00          │
│ Starting capital $100,000.00        │
╰─────────────────────────────────────╯

Open Positions
┌────────┬───────┬────────┬──────────┬────────┬──────────┬─────────┬────────┐
│ Symbol │ Name  │ Shares │ Avg Cost │ Price  │ Value    │ P&L     │ P&L %  │
├────────┼───────┼────────┼──────────┼────────┼──────────┼─────────┼────────┤
│ AAPL   │ Apple │ 100.0  │ $175.50  │ $180.25│ $18,025  │ +$475   │ +2.71% │
│ TSLA   │ Tesla │ 50.0   │ $250.00  │ $245.00│ $12,250  │ -$250   │ -2.00% │
└────────┴───────┴────────┴──────────┴────────┴──────────┴─────────┴────────┘
```

---

### **2. View Trade History**

```bash
# Show last 20 trades (default)
python cli.py trades

# Show last 50 trades
python cli.py trades --limit 50
```

**Shows:**
- ⏰ Timestamp
- 🔄 Action (BUY/SELL)
- 📊 Symbol
- 💹 Shares, price, total
- 📝 Reason for trade

**Example Output:**
```
Trade History (last 20)
┌─────────────────────┬────────┬────────┬────────┬────────┬──────────┬─────────────────┐
│ Timestamp           │ Action │ Symbol │ Shares │ Price  │ Total    │ Reason          │
├─────────────────────┼────────┼────────┼────────┼────────┼──────────┼─────────────────┤
│ 2024-05-28 14:30:00 │ BUY    │ AAPL   │ 10.0   │ $175.50│ $1,755.00│ Dip below -5%   │
│ 2024-05-28 15:45:00 │ SELL   │ TSLA   │ 5.0    │ $260.00│ $1,300.00│ Take profit +10%│
└─────────────────────┴────────┴────────┴────────┴────────┴──────────┴─────────────────┘
```

---

### **3. Run Trading Cycle** (Manual)

```bash
python cli.py run-cycle
```

**What it does:**
1. ✅ Fetches current prices for all tracked stocks
2. ✅ Runs buy-the-dip strategy logic
3. ✅ Executes trades if signals present
4. ✅ Shows portfolio status after cycle

**Use when:**
- Testing strategy manually
- Want to trigger trades outside auto mode
- Debugging trading logic

**Example Output:**
```
Running trading cycle…
Cycle complete — 2 trade(s) executed:
  BUY AAPL  10.0000 shares @ $175.50
  SELL TSLA  5.0000 shares @ $260.00

[Portfolio Status shown here...]
```

---

### **4. Auto Trading Mode** (Market Hours)

```bash
python cli.py auto
```

**What it does:**
- ✅ Waits for NYSE market open (9:30 AM ET)
- ✅ Runs trading cycles automatically every 5 minutes
- ✅ Stops at market close (4:00 PM ET)
- ✅ Respects weekends and holidays
- ✅ Runs continuously until Ctrl+C

**Example Output:**
```
Market is currently closed.
Next open: Monday 2024-05-29 09:30 ET (15.5 h)
Press Ctrl+C to stop.

[Waiting for market open...]

Market is open — starting trading session now.
[09:30 ET] Running cycle...
[09:35 ET] Running cycle...
[09:40 ET] Running cycle...
...
```

**Stop with:** `Ctrl+C`

---

### **5. Reset Portfolio**

```bash
python cli.py reset
```

**What it does:**
- ⚠️ **DANGER:** Deletes entire database
- ✅ Resets cash to $100,000
- ✅ Clears all positions
- ✅ Clears all trades
- ✅ Requires confirmation

**Use when:**
- Starting fresh
- Testing new strategies
- Clearing bad test data

**Example:**
```
Reset portfolio to $100,000 starting cash? This cannot be undone. [y/N]: y
Portfolio reset.
```

⚠️ **WARNING:** Cannot be undone!

---

### **6. Service Management** (macOS Only)

These commands manage background auto-trading:

#### **Check Service Status**
```bash
python cli.py service
```

Shows:
- Service running status
- Recent log entries
- Errors (if any)

#### **Start Service**
```bash
python cli.py service-start
```

Starts background auto-trading:
- Runs automatically on login
- Trades during market hours
- Logs to `~/stock-agent/logs/`

#### **Stop Service**
```bash
python cli.py service-stop
```

Stops background service:
- Prevents auto-trading
- Service won't restart on login

**Note:** macOS only (uses launchd)

---

## 🎯 Common Workflows

### **Daily Monitoring Workflow**

```bash
# Morning: Check portfolio
python cli.py status

# Run manual cycle (if needed)
python cli.py run-cycle

# Evening: Review trades
python cli.py trades --limit 50
```

---

### **Testing Strategy Workflow**

```bash
# 1. Reset to clean state
python cli.py reset

# 2. Run manual cycle
python cli.py run-cycle

# 3. Check results
python cli.py status

# 4. Review trades
python cli.py trades

# 5. Repeat or reset
```

---

### **Auto Trading Workflow**

```bash
# Option A: Foreground (see live updates)
python cli.py auto

# Option B: Background service (macOS)
python cli.py service-start
python cli.py service  # Check status
```

---

## 💡 Pro Tips

### **1. Combine with Watch**

Monitor portfolio in real-time:
```bash
# Update every 30 seconds
watch -n 30 python cli.py status
```

### **2. Redirect Output**

Save status to file:
```bash
python cli.py status > portfolio_$(date +%Y%m%d).txt
```

### **3. Cron Jobs**

Run cycles on schedule (Unix/Linux):
```bash
# Edit crontab
crontab -e

# Add line (run every 5 minutes during market hours)
*/5 9-16 * * 1-5 cd /path/to/stock-agent && python cli.py run-cycle
```

### **4. Multiple Commands**

Chain commands:
```bash
python cli.py run-cycle && python cli.py trades --limit 10
```

---

## 🔍 Understanding the Output

### **Portfolio Status Colors**

- 🟢 **Green**: Positive P&L, profits
- 🔴 **Red**: Negative P&L, losses
- 🟡 **Yellow**: Warnings, watching
- 🔵 **Cyan**: Holdings, neutral
- ⚫ **Dim**: Inactive, no data

### **Signal Types**

- **BUY SIGNAL**: Stock down 5%+ from reference, ready to buy
- **HOLDING**: Currently own position
- **WATCHING**: Monitoring, no action yet
- **—**: No reference price set

### **Targets**

- **TP** (Take Profit): Sell at +10% gain
- **SL** (Stop Loss): Sell at -7% loss
- **Buy < $X**: Buy when price drops below threshold

---

## 🎨 Customizing the CLI

### **Tracked Stocks**

Edit `backend/config.py`:
```python
STOCKS = {
    "AAPL": "Apple Inc.",
    "TSLA": "Tesla Inc.",
    "GOOGL": "Alphabet Inc.",
    # Add your stocks here
}
```

### **Starting Cash**

Edit `backend/config.py`:
```python
STARTING_CASH = 100000  # Change to your amount
```

### **Trading Strategy**

Edit `backend/trading_engine.py`:
- Buy threshold (default: -5%)
- Take profit (default: +10%)
- Stop loss (default: -7%)

---

## 🆘 Troubleshooting

### **"No module named 'click'"**

Install dependencies:
```bash
pip install -r requirements.txt
```

### **"Permission denied"**

Make CLI executable:
```bash
chmod +x cli.py
./cli.py status  # Run directly
```

### **"Database locked"**

Another process is using database:
```bash
# Find process
lsof stock_agent.db

# Kill process (if safe)
kill -9 <PID>
```

### **No prices fetched**

Check internet connection:
```bash
python -c "from backend.data_feed import get_current_prices; print(get_current_prices(['AAPL']))"
```

---

## 📱 CLI vs API vs TradingView

### **When to Use CLI:**
- ✅ Manual testing
- ✅ Local development
- ✅ Quick portfolio checks
- ✅ Strategy development
- ✅ Background auto-trading (service)

### **When to Use API:**
- ✅ TradingView webhooks
- ✅ Custom integrations
- ✅ Mobile monitoring
- ✅ Remote access
- ✅ Web dashboards

### **When to Use TradingView:**
- ✅ Advanced charting
- ✅ Custom indicators
- ✅ Alert automation
- ✅ Mobile alerts
- ✅ Strategy backtesting

**All three can run simultaneously!**

---

## 🚀 Quick Command Reference

```bash
# Portfolio
python cli.py status                    # Show portfolio
python cli.py trades                    # Show trades (last 20)
python cli.py trades --limit 50         # Show trades (last 50)

# Trading
python cli.py run-cycle                 # Manual cycle
python cli.py auto                      # Auto mode (market hours)

# Management
python cli.py reset                     # Reset portfolio
python cli.py service                   # Service status (macOS)
python cli.py service-start             # Start service (macOS)
python cli.py service-stop              # Stop service (macOS)

# Help
python cli.py --help                    # List commands
python cli.py [command] --help          # Command help
```

---

## 🎯 Next Steps

### **For Testing:**
```bash
# 1. Check current status
python cli.py status

# 2. Run a cycle manually
python cli.py run-cycle

# 3. Review results
python cli.py trades
```

### **For Production:**
```bash
# Option A: Foreground auto-trading
python cli.py auto

# Option B: Background service (macOS)
python cli.py service-start
```

### **For TradingView Integration:**
1. Keep CLI for monitoring: `python cli.py status`
2. Use API for webhooks (see `TRADINGVIEW_SETUP.md`)
3. Best of both worlds!

---

## 📚 Related Documentation

- **TradingView Setup:** `TRADINGVIEW_SETUP.md`
- **Mobile Setup:** `MOBILE_TRADINGVIEW_SETUP.md`
- **API Reference:** `CLAUDE.md`
- **Strategy Guide:** `MY_FIRST_STRATEGY.md`

---

**Your CLI is ready to use!** Start with `python cli.py status` to see your portfolio. 📊🚀
