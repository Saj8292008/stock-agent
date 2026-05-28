# TradingView Webhook Integration Guide

Complete guide to integrate TradingView alerts with your stock-agent trading system.

---

## Prerequisites

- ✅ Stock-agent API server running
- ✅ Public URL accessible to TradingView (via ngrok, CloudFlare tunnel, or public server)
- ✅ TradingView account with alert capabilities
- ✅ Secure passphrase configured

---

## Step 1: Configure Environment Variables

### 1.1 Update `.env` File

Edit your `.env` file with the following TradingView settings:

```bash
# Enable TradingView Integration
TRADINGVIEW_ENABLED=true

# Set a secure passphrase (CHANGE THIS!)
TRADINGVIEW_PASSPHRASE=your-very-secure-random-passphrase-here

# Risk Management (highly recommended)
ENABLE_RISK_MANAGER=true
EMERGENCY_STOP=false

# Broker Settings
BROKER_ENABLED=false  # Start with paper trading
ALPACA_PAPER_MODE=true
```

### 1.2 Generate Secure Passphrase

**Option A: Using OpenSSL**
```bash
openssl rand -base64 32
```

**Option B: Using Python**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Option C: Manual**
- Minimum 16 characters
- Mix of uppercase, lowercase, numbers, and special characters
- Example: `Xk9#mP2$vL8@qR5&wN3!`

⚠️ **NEVER use the default passphrase in production!**

---

## Step 2: Start the API Server

### 2.1 Start Server Locally

```bash
# Method 1: Using serve.py
python serve.py

# Method 2: Using uvicorn directly
uvicorn backend.api:app --host 0.0.0.0 --port 8000 --reload
```

The server will start on `http://localhost:8000`

### 2.2 Verify Server is Running

```bash
# Test health endpoint
curl http://localhost:8000/api/portfolio

# Expected response: JSON with portfolio data
```

---

## Step 3: Expose Server to Internet

TradingView needs a public URL to send webhooks. Choose one option:

### Option A: ngrok (Quick Testing)

```bash
# Install ngrok
brew install ngrok  # macOS
# or download from https://ngrok.com/

# Start tunnel
ngrok http 8000

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
```

### Option B: CloudFlare Tunnel (Free, Production)

```bash
# Install cloudflared
brew install cloudflare/cloudflare/cloudflared

# Start tunnel
cloudflared tunnel --url http://localhost:8000

# Copy the HTTPS URL
```

### Option C: Deploy to Public Server

Deploy to a VPS, cloud instance, or serverless platform with a public IP/domain.

**Your webhook URL will be:**
```
https://your-public-url.com/api/webhook/tradingview
```

---

## Step 4: Configure TradingView Alert

### 4.1 Create an Alert in TradingView

1. Open TradingView chart for your stock (e.g., AAPL)
2. Click the **Alert** button (alarm icon) or press `Alt + A`
3. Configure alert conditions (price, indicator, etc.)

### 4.2 Configure Webhook Settings

In the alert creation dialog:

**Webhook URL:**
```
https://your-public-url.com/api/webhook/tradingview
```

**Webhook Message (JSON):**
```json
{
  "passphrase": "your-very-secure-random-passphrase-here",
  "ticker": "{{ticker}}",
  "action": "buy",
  "strategy": "{{strategy.order.alert_message}}",
  "price": {{close}},
  "quantity": 10
}
```

### 4.3 Alert Message Parameters

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `passphrase` | ✅ Yes | Must match `.env` value | `"Xk9#mP2$vL8@qR5&"` |
| `ticker` | ✅ Yes | Stock symbol | `"AAPL"`, `"TSLA"` |
| `action` | ✅ Yes | Order side | `"buy"` or `"sell"` |
| `strategy` | No | Strategy name for logging | `"RSI Oversold"` |
| `price` | Recommended | Current price | `150.25` |
| `quantity` | No | Number of shares | `10` (default uses allocation) |
| `stop_loss` | No | Stop loss price | `145.00` |
| `take_profit` | No | Take profit price | `160.00` |

### 4.4 TradingView Variables

Use these TradingView variables in your webhook message:

- `{{ticker}}` - Symbol name (e.g., "AAPL")
- `{{close}}` - Current close price
- `{{open}}` - Open price
- `{{high}}` - High price
- `{{low}}` - Low price
- `{{volume}}` - Volume
- `{{strategy.order.alert_message}}` - Custom strategy message

---

## Step 5: Test the Integration

### 5.1 Manual Webhook Test

Test with `curl` before setting up alerts:

```bash
curl -X POST http://localhost:8000/api/webhook/tradingview \
  -H "Content-Type: application/json" \
  -d '{
    "passphrase": "your-passphrase-here",
    "ticker": "AAPL",
    "action": "buy",
    "price": 150.0,
    "quantity": 5
  }'
```

**Expected Response:**
```json
{
  "status": "success",
  "message": "Signal processed successfully",
  "signal_id": 1,
  "order_id": 123
}
```

### 5.2 Check Signal Processing

```bash
# View received signals
curl http://localhost:8000/api/signals

# View created orders
curl http://localhost:8000/api/orders

# View portfolio
curl http://localhost:8000/api/portfolio
```

### 5.3 Test with Invalid Passphrase

```bash
curl -X POST http://localhost:8000/api/webhook/tradingview \
  -H "Content-Type: application/json" \
  -d '{
    "passphrase": "wrong-passphrase",
    "ticker": "AAPL",
    "action": "buy"
  }'
```

**Expected Response:** `401 Unauthorized` or `403 Forbidden`

---

## Step 6: Monitor and Verify

### 6.1 Check Logs

Monitor server logs for incoming webhooks:

```bash
# Logs will show:
# - Webhook received
# - Passphrase validation
# - Signal processing
# - Order execution
# - Risk validation
```

### 6.2 Query API Endpoints

```bash
# Get all TradingView signals
curl http://localhost:8000/api/signals

# Get signal processing status
curl http://localhost:8000/api/signals?status=processed

# Get rejected signals
curl http://localhost:8000/api/signals?status=rejected
```

### 6.3 Check Database

```bash
# Signals are stored in tradingview_signals table
sqlite3 stock_agent.db "SELECT * FROM tradingview_signals ORDER BY received_at DESC LIMIT 10;"
```

---

## Step 7: Advanced Configuration

### 7.1 Risk Management

Configure risk limits before enabling live trading:

```bash
# Get current risk limits
curl http://localhost:8000/api/risk-limits

# Update risk limits
curl -X PUT http://localhost:8000/api/risk-limits \
  -H "Content-Type: application/json" \
  -d '{
    "max_position_size": 0.10,
    "max_daily_loss": -0.02,
    "max_concentration": 0.25
  }'
```

### 7.2 Enable Broker Integration

Once tested in paper mode, enable Alpaca broker:

```bash
# Update .env
BROKER_ENABLED=true
ALPACA_PAPER_MODE=true  # Keep true for testing
ALPACA_API_KEY=your_alpaca_paper_key
ALPACA_API_SECRET=your_alpaca_paper_secret
```

### 7.3 Emergency Controls

```bash
# Enable emergency stop (blocks all trades)
curl -X POST http://localhost:8000/api/emergency-stop

# Check emergency stop status
curl http://localhost:8000/api/portfolio
```

---

## Example Alert Strategies

### Strategy 1: RSI Oversold Buy Signal

**Alert Condition:** RSI(14) crosses below 30

**Webhook Message:**
```json
{
  "passphrase": "your-passphrase",
  "ticker": "{{ticker}}",
  "action": "buy",
  "strategy": "RSI Oversold",
  "price": {{close}},
  "quantity": 10,
  "take_profit": {{close}} * 1.05
}
```

### Strategy 2: Moving Average Crossover

**Alert Condition:** SMA(50) crosses above SMA(200)

**Webhook Message:**
```json
{
  "passphrase": "your-passphrase",
  "ticker": "{{ticker}}",
  "action": "buy",
  "strategy": "Golden Cross",
  "price": {{close}},
  "quantity": 20
}
```

### Strategy 3: Take Profit Exit

**Alert Condition:** Price reaches 5% gain

**Webhook Message:**
```json
{
  "passphrase": "your-passphrase",
  "ticker": "{{ticker}}",
  "action": "sell",
  "strategy": "Take Profit 5%",
  "price": {{close}}
}
```

---

## Troubleshooting

### Issue: Webhook Returns 401/403

**Cause:** Passphrase mismatch

**Solution:**
1. Check `.env` file for correct `TRADINGVIEW_PASSPHRASE`
2. Verify TradingView alert webhook message has matching passphrase
3. Restart server after changing `.env`

### Issue: Signal Rejected by Risk Manager

**Cause:** Order violates risk limits

**Solution:**
1. Check risk status: `curl http://localhost:8000/api/risk-status`
2. Review risk limits: `curl http://localhost:8000/api/risk-limits`
3. Adjust limits or reduce position size

### Issue: Order Not Executing

**Cause:** Broker disabled or misconfigured

**Solution:**
1. Check `BROKER_ENABLED` in `.env`
2. Verify Alpaca credentials
3. Check order logs: `curl http://localhost:8000/api/orders`

### Issue: Webhook Not Received

**Cause:** Public URL not accessible

**Solution:**
1. Verify tunnel (ngrok/cloudflare) is running
2. Test URL manually: `curl https://your-url.com/api/webhook/tradingview`
3. Check firewall/security settings

---

## Security Best Practices

1. ✅ **Strong Passphrase**: Use 32+ character random passphrase
2. ✅ **HTTPS Only**: Always use HTTPS for webhook URL (ngrok/cloudflare provide this)
3. ✅ **Rate Limiting**: Consider adding rate limiting to webhook endpoint
4. ✅ **Audit Logging**: Monitor `audit_log` table for suspicious activity
5. ✅ **Risk Limits**: Always enable risk manager in production
6. ✅ **Paper Trading First**: Test thoroughly before live trading
7. ✅ **Environment Variables**: Never commit `.env` file to git
8. ✅ **Emergency Stop**: Know how to quickly stop all trading

---

## Production Deployment Checklist

- [ ] Secure passphrase configured (32+ characters)
- [ ] Risk manager enabled
- [ ] Risk limits configured appropriately
- [ ] Tested in paper trading mode (2+ weeks)
- [ ] TradingView alerts tested and verified
- [ ] Server deployed with public HTTPS URL
- [ ] Monitoring and alerting configured
- [ ] Emergency stop procedure documented
- [ ] Database backed up regularly
- [ ] Logs being written and reviewed

---

## API Endpoints Reference

### TradingView Webhook

**POST** `/api/webhook/tradingview`

Receive and process TradingView alert signals.

**Request Body:**
```json
{
  "passphrase": "string (required)",
  "ticker": "string (required)",
  "action": "buy | sell (required)",
  "strategy": "string (optional)",
  "price": "number (optional)",
  "quantity": "number (optional)",
  "stop_loss": "number (optional)",
  "take_profit": "number (optional)"
}
```

**Response:**
```json
{
  "status": "success | error",
  "message": "string",
  "signal_id": "integer",
  "order_id": "integer (if processed)"
}
```

### Query Signals

**GET** `/api/signals`

Retrieve TradingView signals history.

**Query Parameters:**
- `status`: Filter by status (pending, processed, rejected)
- `limit`: Number of signals to return (default: 100)

### Query Orders

**GET** `/api/orders`

Retrieve order history.

**Query Parameters:**
- `status`: Filter by status (pending, filled, canceled)
- `limit`: Number of orders to return (default: 100)

---

## Support and Documentation

- **Main Documentation**: `CLAUDE.md`
- **Testing Guide**: `TESTING_GUIDE.md`
- **API Documentation**: Start server and visit `http://localhost:8000/docs`
- **Issue Tracker**: GitHub Issues

---

## Next Steps

1. ✅ Configure secure passphrase
2. ✅ Start API server
3. ✅ Expose server with tunnel
4. ✅ Create test alert in TradingView
5. ✅ Verify signal processing
6. ✅ Monitor for 1-2 weeks in paper mode
7. ✅ Enable broker integration (paper mode)
8. ✅ Test with real broker in paper mode
9. ⚠️ Consider live trading only after extensive testing

---

**Happy Trading!** 🚀📈
