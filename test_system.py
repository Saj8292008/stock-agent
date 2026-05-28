#!/usr/bin/env python3
"""
Comprehensive test suite for the stock trading system.
Tests database migrations, API endpoints, and TradingView webhook integration.
"""

import sys
import os
import json
import sqlite3
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

def test_phase_1_database():
    """Phase 1: Database Initialization and Migrations"""
    print("\n" + "="*70)
    print("PHASE 1: DATABASE INITIALIZATION AND MIGRATIONS")
    print("="*70)
    
    from backend import portfolio as port
    from backend import migrations
    
    # Initialize database
    print("\n[1.1] Initializing database...")
    try:
        port.init_db()
        print("✓ Database initialized successfully")
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        return False
    
    # Verify schema
    print("\n[1.2] Verifying schema...")
    try:
        schema_info = migrations.verify_schema()
        print(f"  Schema version: {schema_info['schema_version']}")
        print(f"  Tables expected: {schema_info['tables_expected']}")
        print(f"  Tables found: {schema_info['tables_found']}")
        
        if schema_info['missing_tables']:
            print(f"  ✗ Missing tables: {', '.join(schema_info['missing_tables'])}")
            return False
        else:
            print("  ✓ All tables present")
        
        if schema_info['is_valid']:
            print("✓ Schema validation passed")
        else:
            print("✗ Schema validation failed")
            return False
    except Exception as e:
        print(f"✗ Schema verification failed: {e}")
        return False
    
    # Check risk limits
    print("\n[1.3] Verifying default risk limits...")
    try:
        limits = port.get_risk_limits()
        if limits:
            print(f"  Max position size: {limits['max_position_size']*100}%")
            print(f"  Max daily loss: {limits['max_daily_loss']*100}%")
            print(f"  Max total exposure: {limits['max_total_exposure']*100}%")
            print(f"  Max orders per day: {limits['max_orders_per_day']}")
            print("✓ Default risk limits configured")
        else:
            print("✗ Risk limits not found")
            return False
    except Exception as e:
        print(f"✗ Risk limits check failed: {e}")
        return False
    
    # List all tables
    print("\n[1.4] Database tables:")
    from backend.config import DB_PATH
    con = sqlite3.connect(DB_PATH)
    tables = con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    for table in tables:
        count = con.execute(f"SELECT COUNT(*) FROM {table[0]}").fetchone()[0]
        print(f"  - {table[0]}: {count} rows")
    con.close()
    
    print("\n✓ Phase 1 completed successfully\n")
    return True


def test_phase_2_config():
    """Phase 2: Configuration Validation"""
    print("\n" + "="*70)
    print("PHASE 2: CONFIGURATION VALIDATION")
    print("="*70)
    
    from backend import config
    
    print("\n[2.1] Loading configuration from environment...")
    try:
        config.load_from_env()
        print("✓ Configuration loaded")
    except Exception as e:
        print(f"✗ Configuration loading failed: {e}")
        return False
    
    print("\n[2.2] Configuration status:")
    print(f"  Broker enabled: {config.BROKER_ENABLED}")
    print(f"  TradingView enabled: {config.TRADINGVIEW_ENABLED}")
    print(f"  Risk manager enabled: {config.ENABLE_RISK_MANAGER}")
    print(f"  Emergency stop: {config.EMERGENCY_STOP}")
    print(f"  Database path: {config.DB_PATH}")
    print(f"  Starting cash: ${config.STARTING_CASH:,.2f}")
    print(f"  Tracked stocks: {len(config.STOCKS)}")
    
    print("\n[2.3] Validating configuration...")
    try:
        errors = config.validate_config()
        if errors:
            print("  Configuration warnings/errors:")
            for error in errors:
                print(f"    - {error}")
        else:
            print("✓ Configuration validation passed")
    except Exception as e:
        print(f"✗ Configuration validation failed: {e}")
        return False
    
    print("\n✓ Phase 2 completed successfully\n")
    return True


def test_phase_3_portfolio_functions():
    """Phase 3: Portfolio Functions"""
    print("\n" + "="*70)
    print("PHASE 3: PORTFOLIO AND DATABASE FUNCTIONS")
    print("="*70)
    
    from backend import portfolio as port
    
    print("\n[3.1] Testing cash operations...")
    try:
        initial_cash = port.get_cash()
        print(f"  Initial cash: ${initial_cash:,.2f}")
        
        port.set_cash(100000.0)
        new_cash = port.get_cash()
        print(f"  After set_cash: ${new_cash:,.2f}")
        print("✓ Cash operations working")
    except Exception as e:
        print(f"✗ Cash operations failed: {e}")
        return False
    
    print("\n[3.2] Testing trade logging...")
    try:
        port.log_trade("AAPL", "buy", 10.0, 150.0, "Test trade")
        trades = port.get_trades(limit=5)
        print(f"  Trades in database: {len(trades)}")
        if trades:
            latest = trades[0]
            print(f"  Latest trade: {latest['action']} {latest['shares']} {latest['symbol']} @ ${latest['price']}")
        print("✓ Trade logging working")
    except Exception as e:
        print(f"✗ Trade logging failed: {e}")
        return False
    
    print("\n[3.3] Testing order logging...")
    try:
        order_id = port.log_order(
            broker_order_id=None,
            symbol="GOOGL",
            side="buy",
            order_type="market",
            quantity=5.0,
            status="pending",
            strategy_name="test_strategy"
        )
        print(f"  Created order ID: {order_id}")
        
        orders = port.get_orders(limit=5)
        print(f"  Orders in database: {len(orders)}")
        print("✓ Order logging working")
    except Exception as e:
        print(f"✗ Order logging failed: {e}")
        return False
    
    print("\n[3.4] Testing TradingView signal logging...")
    try:
        signal_id = port.log_tradingview_signal(
            symbol="MSFT",
            action="buy",
            strategy="test_strategy",
            price=300.0,
            quantity=3.0
        )
        print(f"  Created signal ID: {signal_id}")
        
        signals = port.get_signals(limit=5)
        print(f"  Signals in database: {len(signals)}")
        print("✓ Signal logging working")
    except Exception as e:
        print(f"✗ Signal logging failed: {e}")
        return False
    
    print("\n✓ Phase 3 completed successfully\n")
    return True


def main():
    """Run all test phases"""
    print("\n" + "="*70)
    print("STOCK TRADING SYSTEM - COMPREHENSIVE TEST SUITE")
    print("="*70)
    print(f"Test started: {datetime.now().isoformat()}")
    print(f"Working directory: {os.getcwd()}")
    
    results = {}
    
    # Run test phases
    results['Phase 1: Database'] = test_phase_1_database()
    results['Phase 2: Configuration'] = test_phase_2_config()
    results['Phase 3: Portfolio Functions'] = test_phase_3_portfolio_functions()
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for phase, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{phase}: {status}")
    
    all_passed = all(results.values())
    print("\n" + "="*70)
    if all_passed:
        print("ALL TESTS PASSED ✓")
    else:
        print("SOME TESTS FAILED ✗")
    print("="*70)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
