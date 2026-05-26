STOCKS = {
    "GOOGL": "Google",
    "RIVN":  "Rivian",
    "META":  "Meta",
    "NVDA":  "Nvidia",
    "GLD":   "Gold (ETF)",
    "SLV":   "Silver (ETF)",
    "TSLA":  "Tesla",
    "GS":    "Goldman Sachs",
    "MU":    "Micron Technology",
}

STARTING_CASH        = 100_000.0
ALLOCATION_PER_STOCK = 0.10   # 10 % of portfolio per position

BUY_DIP_THRESHOLD    = -0.05  # buy when price dips 5 % below rolling ref
TAKE_PROFIT          =  0.10  # sell when +10 % from entry
STOP_LOSS            = -0.07  # sell when -7 % from entry

POLL_INTERVAL        = 300    # seconds between agent cycles
DB_PATH              = "portfolio.db"
