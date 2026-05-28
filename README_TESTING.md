# Testing Guide for Stock-Agent

This document describes the comprehensive test suite for the stock-agent trading system.

## Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Test Coverage](#test-coverage)
- [Writing Tests](#writing-tests)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)

---

## Overview

The stock-agent test suite provides comprehensive coverage of all system components:

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test multi-component interactions
- **End-to-End Tests**: Test complete workflows
- **Mocked External Services**: No live broker/API calls required

### Test Statistics

- **Total Test Files**: 10+
- **Test Cases**: 150+
- **Target Coverage**: 80%+
- **Core Modules Covered**:
  - `backend/trading_engine.py`
  - `backend/broker_client.py`
  - `backend/risk_manager.py`
  - `backend/portfolio.py`
  - `backend/api.py`
  - `backend/migrations.py`
  - `backend/broker_feed.py`

---

## Test Structure

```
tests/
├── __init__.py
├── conftest.py                 # Shared fixtures and configuration
├── unit/                       # Unit tests
│   ├── test_config.py         # Configuration management
│   ├── test_portfolio.py      # Database operations
│   ├── test_risk_manager.py   # Risk validation (all 5 checks)
│   └── test_migrations.py     # Database migrations
├── integration/                # Integration tests
│   ├── test_trading_engine.py # Trading logic
│   ├── test_broker_client.py  # Alpaca API integration
│   ├── test_broker_feed.py    # Data synchronization
│   └── test_api.py            # FastAPI endpoints
└── fixtures/                   # Test data and mocks
    ├── mock_broker_responses.py
    └── sample_signals.py
```

---

## Running Tests

### Setup

1. **Install test dependencies**:
   ```bash
   pip install -r requirements-test.txt
   ```

2. **Verify installation**:
   ```bash
   pytest --version
   ```

### Run All Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with detailed output on failures
pytest -vv --tb=long
```

### Run Specific Test Types

```bash
# Unit tests only
pytest tests/unit -v

# Integration tests only
pytest tests/integration -v

# End-to-end tests only
pytest -m e2e -v

# Slow tests (skipped by default)
pytest -m slow -v
```

### Run Specific Test Files

```bash
# Test risk manager
pytest tests/unit/test_risk_manager.py -v

# Test trading engine
pytest tests/integration/test_trading_engine.py -v

# Test API endpoints
pytest tests/integration/test_api.py -v
```

### Run Specific Test Cases

```bash
# Run single test class
pytest tests/unit/test_risk_manager.py::TestPositionSizeValidation -v

# Run single test method
pytest tests/unit/test_risk_manager.py::TestPositionSizeValidation::test_position_size_within_limit -v
```

### Parallel Execution

```bash
# Run tests in parallel (4 workers)
pytest -n 4
```

---

## Test Coverage

### Generate Coverage Report

```bash
# Run tests with coverage
pytest --cov=backend --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Coverage Targets

| Module | Target Coverage | Critical Functions |
|--------|----------------|-------------------|
| `risk_manager.py` | 90%+ | All 5 risk checks |
| `trading_engine.py` | 85%+ | run_cycle, execute_signal |
| `broker_client.py` | 85%+ | Order submission, status polling |
| `portfolio.py` | 90%+ | All database operations |
| `api.py` | 80%+ | All endpoints |
| `migrations.py` | 85%+ | Migration functions |

### Check Coverage Threshold

```bash
# Fail if coverage < 80%
pytest --cov=backend --cov-report=term --cov-fail-under=80
```

---

## Writing Tests

### Test Naming Conventions

- Test files: `test_<module>.py`
- Test classes: `Test<Feature>`
- Test methods: `test_<behavior>`

### Example Test

```python
import pytest
from backend.risk_manager import RiskManager

@pytest.mark.unit
class TestPositionSizeValidation:
    """Test maximum position size validation."""

    def test_position_size_within_limit(self, test_db):
        """Test that trade within position size limit is approved."""
        rm = RiskManager(db_path=test_db)

        # 10% limit, portfolio = $100k, max position = $10k
        # Buying $5k worth (50 shares @ $100) should pass
        result = rm.validate_trade("AAPL", "buy", 50, 100.0, 100000.0)

        assert result['approved'] is True
        assert 'position_size' not in result.get('violations', [])
```

### Using Fixtures

```python
def test_with_test_db(test_db):
    """Test database is automatically created and cleaned up."""
    cursor = test_db.cursor()
    cursor.execute("SELECT * FROM portfolio")
    # Test database is pre-populated

def test_with_mock_broker(mock_broker_client):
    """Mock broker client is pre-configured."""
    account = mock_broker_client.get_account()
    assert account is not None

def test_with_sample_signal(sample_buy_signal):
    """Sample TradingView signal payload."""
    assert sample_buy_signal['action'] == 'buy'
```

### Mocking External Services

```python
from unittest.mock import patch, MagicMock

def test_with_mocked_yfinance(mock_yfinance):
    """yfinance is automatically mocked."""
    # No actual network calls made

@responses.activate
def test_broker_api_call():
    """Mock HTTP responses for Alpaca API."""
    responses.add(
        responses.GET,
        "https://paper-api.alpaca.markets/v2/account",
        json={"cash": "100000.0"},
        status=200
    )
    # Test makes mocked HTTP call
```

---

## Critical Test Scenarios

### 1. Position Accumulation (Bug Fix Verification)

**File**: `tests/integration/test_trading_engine.py`

**Test**: `test_buying_same_stock_twice_accumulates`

**Verifies**: Commit d780722 fix - buying same stock twice accumulates shares rather than overwriting.

```bash
pytest tests/integration/test_trading_engine.py::TestPositionAccumulationFix -v
```

### 2. Risk Manager - All 5 Checks

**File**: `tests/unit/test_risk_manager.py`

**Tests**:
- `TestPositionSizeValidation` - Max position size
- `TestConcentrationValidation` - Max concentration
- `TestTotalExposureValidation` - Max exposure
- `TestDailyLossLimit` - Daily loss enforcement
- `TestDailyTradeCountLimit` - Trade count limit

```bash
pytest tests/unit/test_risk_manager.py -v
```

### 3. Emergency Stop

**Files**:
- `tests/integration/test_trading_engine.py`
- `tests/integration/test_api.py`

**Verifies**: Emergency stop blocks all trades and persists across restarts.

```bash
pytest -k emergency_stop -v
```

### 4. TradingView Webhook Security

**File**: `tests/integration/test_api.py`

**Test**: `test_webhook_invalid_passphrase`

**Verifies**: Invalid passphrase is rejected.

```bash
pytest tests/integration/test_api.py::TestTradingViewWebhook -v
```

### 5. Database Migrations

**File**: `tests/unit/test_migrations.py`

**Tests**:
- Migration from v0 to v1
- Idempotency
- Data preservation

```bash
pytest tests/unit/test_migrations.py -v
```

---

## CI/CD Integration

### GitHub Actions Workflow

The test suite runs automatically on:
- Push to `main` or `develop`
- Pull requests to `main` or `develop`

**Workflow**: `.github/workflows/tests.yml`

**Jobs**:
1. **test**: Run unit and integration tests (Python 3.9, 3.10, 3.11)
2. **test-e2e**: Run end-to-end tests (main branch only)
3. **security**: Run security scans with bandit
4. **notify**: Report test results

### Local CI Simulation

```bash
# Run the same tests as CI
pytest tests/unit -v
pytest tests/integration -v
pytest --cov=backend --cov-report=term --cov-fail-under=80
```

### Coverage Upload

Coverage reports are automatically uploaded to Codecov on CI runs.

---

## Test Markers

Tests are marked for selective execution:

```python
@pytest.mark.unit          # Unit test
@pytest.mark.integration   # Integration test
@pytest.mark.e2e           # End-to-end test
@pytest.mark.slow          # Slow test (skipped by default)
@pytest.mark.requires_broker  # Requires broker API (skip in CI)
```

### Run by Marker

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"

# Run unit and integration (not e2e)
pytest -m "unit or integration"
```

---

## Troubleshooting

### Tests Fail with Database Errors

**Problem**: Database connection or schema errors.

**Solution**:
```bash
# Check test database fixture
pytest tests/conftest.py -v

# Run migrations test to verify schema
pytest tests/unit/test_migrations.py -v
```

### Import Errors

**Problem**: Cannot import backend modules.

**Solution**:
```bash
# Ensure you're in project root
pwd

# Install package in editable mode
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Mock Fixtures Not Working

**Problem**: Mock fixtures return None or unexpected values.

**Solution**:
```python
# Check fixture is imported in conftest.py
from tests.fixtures.mock_broker_responses import mock_account_response

# Verify fixture is being used
def test_example(mock_broker_client):
    print(mock_broker_client)  # Should not be None
```

### Tests Pass Locally but Fail in CI

**Problem**: Environment differences.

**Solution**:
```bash
# Check environment variables
env | grep -E "(BROKER|TRADINGVIEW|DB_PATH)"

# Run with CI environment
BROKER_ENABLED=false TRADINGVIEW_ENABLED=false pytest
```

### Coverage Below Threshold

**Problem**: Coverage < 80%.

**Solution**:
```bash
# Identify uncovered lines
pytest --cov=backend --cov-report=term-missing

# Focus on critical modules first
pytest --cov=backend/risk_manager --cov=backend/trading_engine
```

---

## Test Data Management

### Test Database

- **Location**: Temporary file (auto-cleanup)
- **Schema**: v1 (latest)
- **Initial Data**:
  - Portfolio: $100,000 cash
  - Risk limits: Default values
  - Positions: Sample data in `test_portfolio` fixture

### Sample Signals

**File**: `tests/fixtures/sample_signals.py`

Available fixtures:
- `valid_buy_signal()`
- `valid_sell_signal()`
- `signal_with_stop_loss()`
- `signal_with_take_profit()`
- `invalid_passphrase_signal()`
- `missing_required_fields_signal()`

### Mock Broker Responses

**File**: `tests/fixtures/mock_broker_responses.py`

Available mocks:
- `mock_account_response()`
- `mock_order_response()`
- `mock_position_response()`
- `mock_quote_response()`
- Error responses (rate limit, insufficient funds, etc.)

---

## Performance Testing

### Run Performance Tests

```bash
# Run slow tests (marked with @pytest.mark.slow)
pytest -m slow -v

# Profile test execution time
pytest --durations=10
```

### Optimize Slow Tests

1. Use `@pytest.mark.slow` for tests > 5 seconds
2. Mock external API calls
3. Use smaller datasets
4. Run slow tests in parallel

---

## Best Practices

### DO

✅ Write tests before fixing bugs
✅ Test edge cases and error conditions
✅ Use descriptive test names
✅ Keep tests isolated (no dependencies between tests)
✅ Mock external services (broker API, yfinance)
✅ Clean up resources (database connections, temp files)
✅ Use fixtures for common setup
✅ Assert specific values, not just truthiness

### DON'T

❌ Make real API calls in tests
❌ Depend on test execution order
❌ Use sleep() for timing (use mocks instead)
❌ Test multiple things in one test
❌ Ignore failing tests
❌ Commit with failing tests
❌ Skip cleanup in fixtures

---

## Continuous Improvement

### Adding New Tests

When adding a new feature:

1. Write unit tests for core logic
2. Write integration tests for component interactions
3. Add fixtures for test data
4. Update this documentation
5. Verify coverage doesn't decrease

### Maintaining Tests

- Review and update tests when requirements change
- Remove obsolete tests
- Refactor duplicate test code into fixtures
- Keep test documentation current

---

## Support

For questions or issues with tests:

1. Check this documentation
2. Review existing tests for examples
3. Check CI logs for failures
4. Consult pytest documentation: https://docs.pytest.org/

---

## Summary

The stock-agent test suite provides comprehensive coverage of all critical components:

- ✅ 150+ test cases
- ✅ 80%+ code coverage
- ✅ All 5 risk checks tested
- ✅ Critical bug fixes verified
- ✅ CI/CD integration
- ✅ No external dependencies in tests

Run tests frequently during development to catch issues early and ensure system reliability.
