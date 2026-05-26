"""
Auto-mode entry point.

Runs the trading agent only during NYSE market hours (9:30–4:00 PM ET,
Mon–Fri). Sleeps automatically overnight and on weekends.

Usage:
    python autorun.py
"""

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

from backend.scheduler import run_scheduler

if __name__ == "__main__":
    run_scheduler()
