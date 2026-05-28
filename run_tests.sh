#!/bin/bash
# Test runner script for stock-agent
#
# Usage:
#   ./run_tests.sh              # Run all tests
#   ./run_tests.sh unit         # Run unit tests only
#   ./run_tests.sh integration  # Run integration tests only
#   ./run_tests.sh coverage     # Run with coverage report

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Stock-Agent Test Runner${NC}"
echo "================================"

# Check if pytest is installed
if ! python -m pytest --version > /dev/null 2>&1; then
    echo -e "${YELLOW}pytest not found. Installing test dependencies...${NC}"
    pip install -r requirements-test.txt
fi

# Determine what to run
TEST_TARGET="${1:-all}"

case "$TEST_TARGET" in
    "unit")
        echo -e "${GREEN}Running unit tests...${NC}"
        python -m pytest tests/unit -v --tb=short
        ;;

    "integration")
        echo -e "${GREEN}Running integration tests...${NC}"
        python -m pytest tests/integration -v --tb=short
        ;;

    "coverage")
        echo -e "${GREEN}Running tests with coverage...${NC}"
        python -m pytest --cov=backend --cov-report=html --cov-report=term
        echo ""
        echo -e "${GREEN}Coverage report generated in htmlcov/index.html${NC}"
        ;;

    "quick")
        echo -e "${GREEN}Running quick test (unit tests only, no coverage)...${NC}"
        python -m pytest tests/unit -v --tb=short -x
        ;;

    "ci")
        echo -e "${GREEN}Running CI test suite...${NC}"
        python -m pytest tests/unit -v --tb=short
        python -m pytest tests/integration -v --tb=short
        python -m pytest --cov=backend --cov-report=term --cov-fail-under=80
        ;;

    "all")
        echo -e "${GREEN}Running all tests...${NC}"
        python -m pytest tests -v --tb=short
        ;;

    *)
        echo -e "${RED}Unknown test target: $TEST_TARGET${NC}"
        echo ""
        echo "Usage:"
        echo "  ./run_tests.sh [target]"
        echo ""
        echo "Available targets:"
        echo "  all          - Run all tests (default)"
        echo "  unit         - Run unit tests only"
        echo "  integration  - Run integration tests only"
        echo "  coverage     - Run tests with coverage report"
        echo "  quick        - Run unit tests only (fast)"
        echo "  ci           - Run CI test suite with coverage check"
        exit 1
        ;;
esac

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Tests passed!${NC}"
else
    echo ""
    echo -e "${RED}✗ Tests failed!${NC}"
    exit 1
fi
