# Testing Quick Reference

Quick commands and tips for running tests in stock-agent.

## Installation

```bash
pip install -r requirements-test.txt
```

## Running Tests

### Quick Commands

```bash
# Run all tests
pytest

# Run specific test type
pytest tests/unit
pytest tests/integration

# Run specific file
pytest tests/unit/test_risk_manager.py

# Run specific test
pytest tests/unit/test_risk_manager.py::TestPositionSizeValidation::test_position_size_within_limit

# Run with coverage
pytest --cov=backend --cov-report=html

# Quick test (fail fast)
pytest -x

# Verbose output
pytest -v

# Very verbose (show full diff)
pytest -vv
```

### Using Test Runner Script

```bash
./run_tests.sh              # All tests
./run_tests.sh unit         # Unit tests only
./run_tests.sh integration  # Integration tests only
./run_tests.sh coverage     # With coverage report
./run_tests.sh quick        # Fast (unit only)
./run_tests.sh ci           # CI test suite
```

## Test Markers

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"

# Run tests that require broker (usually skipped)
pytest -m requires_broker
```

## Coverage

```bash
# Generate HTML coverage report
pytest --cov=backend --cov-report=html
open htmlcov/index.html

# Terminal coverage report
pytest --cov=backend --cov-report=term

# Coverage with missing lines
pytest --cov=backend --cov-report=term-missing

# Fail if coverage < 80%
pytest --cov=backend --cov-fail-under=80
```

## Debugging Tests

```bash
# Show print statements
pytest -s

# Drop into debugger on failure
pytest --pdb

# Drop into debugger on error
pytest --pdb --pdbcls=IPython.terminal.debugger:Pdb

# Show local variables on failure
pytest -l

# Detailed traceback
pytest --tb=long
```

## Useful Options

```bash
# Run tests in parallel (4 workers)
pytest -n 4

# Stop after first failure
pytest -x

# Stop after N failures
pytest --maxfail=3

# Run last failed tests
pytest --lf

# Run failed first, then rest
pytest --ff

# Show slowest 10 tests
pytest --durations=10

# Timeout after 60 seconds per test
pytest --timeout=60
```

## Test Files Quick Reference

### Unit Tests
- `tests/unit/test_risk_manager.py` - All 5 risk checks
- `tests/unit/test_portfolio.py` - Database operations
- `tests/unit/test_migrations.py` - Schema migrations
- `tests/unit/test_config.py` - Configuration

### Integration Tests
- `tests/integration/test_trading_engine.py` - Trading logic
- `tests/integration/test_broker_client.py` - Alpaca API
- `tests/integration/test_api.py` - FastAPI endpoints
- `tests/integration/test_broker_feed.py` - Data sync

### Fixtures
- `tests/fixtures/mock_broker_responses.py` - Alpaca mocks
- `tests/fixtures/sample_signals.py` - TradingView signals
- `tests/conftest.py` - Shared fixtures

## Common Test Patterns

### Using Fixtures

```python
def test_with_database(test_db):
    """Automatically uses test database fixture."""
    cursor = test_db.cursor()
    # Database is already initialized

def test_with_mock_broker(mock_broker_client):
    """Automatically uses mock broker."""
    account = mock_broker_client.get_account()
    # Returns mock data, no real API calls

def test_with_sample_data(test_portfolio):
    """Pre-populated portfolio data."""
    # Portfolio has sample positions
```

### Running Specific Tests

```bash
# Test a specific risk check
pytest tests/unit/test_risk_manager.py::TestPositionSizeValidation -v

# Test TradingView webhook
pytest tests/integration/test_api.py::TestTradingViewWebhook -v

# Test position accumulation fix
pytest tests/integration/test_trading_engine.py::TestPositionAccumulationFix -v

# Test emergency stop
pytest -k emergency_stop -v

# Test all API endpoints
pytest tests/integration/test_api.py -v
```

## Critical Test Scenarios

```bash
# Verify position accumulation bug fix
pytest tests/integration/test_trading_engine.py::TestPositionAccumulationFix::test_buying_same_stock_twice_accumulates -v

# Verify all 5 risk checks
pytest tests/unit/test_risk_manager.py -v

# Verify emergency stop
pytest -k emergency_stop -v

# Verify TradingView security
pytest tests/integration/test_api.py::TestTradingViewWebhook::test_webhook_invalid_passphrase -v

# Verify migrations
pytest tests/unit/test_migrations.py -v
```

## Environment Variables

```bash
# Set environment for testing
export DB_PATH=/tmp/test.db
export BROKER_ENABLED=false
export TRADINGVIEW_ENABLED=false

# Run tests with custom env
DB_PATH=/tmp/test.db pytest
```

## Fixtures Available

- `test_db` - Initialized SQLite test database
- `test_db_path` - Path to temporary database file
- `mock_broker_client` - Mocked Alpaca API client
- `mock_yfinance` - Mocked yfinance
- `test_portfolio` - Pre-populated portfolio
- `sample_buy_signal` - TradingView buy signal
- `sample_sell_signal` - TradingView sell signal
- `test_app` - FastAPI TestClient
- `reset_environment` - Auto-reset env vars

## Common Issues

### Import Errors
```bash
# Add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or install in editable mode
pip install -e .
```

### Database Errors
```bash
# Check schema
pytest tests/unit/test_migrations.py -v

# Clean test databases
find /tmp -name "*.db" -delete
```

### Fixture Not Found
```bash
# Check conftest.py is present
ls tests/conftest.py

# Check fixture is imported
grep -r "def test_db" tests/
```

## CI/CD

Tests run automatically on:
- Push to main/develop
- Pull requests to main/develop

View workflow: `.github/workflows/tests.yml`

## Coverage Goals

| Module | Target |
|--------|--------|
| risk_manager.py | 90%+ |
| trading_engine.py | 85%+ |
| broker_client.py | 85%+ |
| portfolio.py | 90%+ |
| api.py | 80%+ |

## Documentation

- Full guide: `README_TESTING.md`
- Implementation summary: `TESTING_IMPLEMENTATION_SUMMARY.md`
- This reference: `TESTING_QUICK_REFERENCE.md`

## Getting Help

1. Check `README_TESTING.md` for detailed info
2. Look at existing tests for examples
3. Check pytest docs: https://docs.pytest.org/
4. Review conftest.py for available fixtures

## Pre-Commit Checklist

Before committing:
```bash
# Run quick tests
./run_tests.sh quick

# Run full test suite
./run_tests.sh ci

# Check coverage
pytest --cov=backend --cov-fail-under=80
```

## Performance

```bash
# Identify slow tests
pytest --durations=10

# Run tests in parallel
pytest -n auto

# Profile test execution
pytest --profile
```

## Writing New Tests

1. Choose appropriate directory (`unit/` or `integration/`)
2. Create test file: `test_<module>.py`
3. Use existing tests as templates
4. Use fixtures from conftest.py
5. Add test markers (`@pytest.mark.unit` or `@pytest.mark.integration`)
6. Run your new tests: `pytest path/to/test_file.py -v`
7. Verify coverage didn't decrease

## Test Maintenance

- Update tests when requirements change
- Remove obsolete tests
- Refactor duplicate code into fixtures
- Keep documentation current
- Review coverage regularly

---

**Quick Start**: `./run_tests.sh quick`

**Full Suite**: `./run_tests.sh ci`

**Coverage Report**: `./run_tests.sh coverage && open htmlcov/index.html`
