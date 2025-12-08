#!/bin/bash
#
# Automated Test Runner for Key-Face-Frame
#
# This script runs the complete test suite including:
# 1. Code quality checks (black, flake8, isort)
# 2. Type checking (mypy)
# 3. Unit tests with coverage
# 4. Integration tests
#
# Usage:
#   ./run_tests.sh              # Run all tests
#   ./run_tests.sh --fast       # Skip integration tests
#   ./run_tests.sh --unit-only  # Only unit tests
#

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse command line arguments
FAST_MODE=false
UNIT_ONLY=false

for arg in "$@"; do
    case $arg in
        --fast)
            FAST_MODE=true
            shift
            ;;
        --unit-only)
            UNIT_ONLY=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --fast       Skip integration tests (faster)"
            echo "  --unit-only  Run only unit tests"
            echo "  --help       Show this help message"
            exit 0
            ;;
    esac
done

# Print header
echo ""
echo "======================================="
echo -e "${BLUE}Key-Face-Frame Test Suite${NC}"
echo "======================================="
echo ""

# Check virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠ Warning: Virtual environment not activated${NC}"
    echo "  Run: source .venv/bin/activate"
    echo ""
    exit 1
fi

# 1. Code quality checks
echo -e "${BLUE}1. Running code quality checks...${NC}"
echo ""

echo -e "   ${YELLOW}→${NC} Black (formatting)"
if black --check backend/ tests/ 2>&1 | grep -q "would be reformatted"; then
    echo -e "   ${RED}✗ Black failed - files need formatting${NC}"
    echo "   Run: black backend/ tests/"
    exit 1
else
    echo -e "   ${GREEN}✓ Black passed${NC}"
fi

echo ""
echo -e "   ${YELLOW}→${NC} Flake8 (linting)"
if flake8 backend/ tests/ --max-line-length=100 --exclude=.venv,__pycache__,.git --extend-ignore=E203,W503 > /dev/null 2>&1; then
    echo -e "   ${GREEN}✓ Flake8 passed${NC}"
else
    echo -e "   ${RED}✗ Flake8 failed${NC}"
    echo "   Running flake8 to show errors:"
    flake8 backend/ tests/ --max-line-length=100 --exclude=.venv,__pycache__,.git --extend-ignore=E203,W503 || true
    exit 1
fi

echo ""
echo -e "   ${YELLOW}→${NC} isort (imports)"
if isort --check-only backend/ tests/ > /dev/null 2>&1; then
    echo -e "   ${GREEN}✓ isort passed${NC}"
else
    echo -e "   ${RED}✗ isort failed - imports need sorting${NC}"
    echo "   Run: isort backend/ tests/"
    exit 1
fi

echo ""
echo -e "${GREEN}✓ Code quality checks passed${NC}"
echo ""

# 2. Type checking
echo -e "${BLUE}2. Running type checking...${NC}"
echo ""

if mypy backend/ --ignore-missing-imports --no-error-summary 2>&1 | grep -q "error:"; then
    echo -e "   ${RED}✗ Mypy failed${NC}"
    echo "   Running mypy to show errors:"
    mypy backend/ --ignore-missing-imports || true
    exit 1
else
    echo -e "   ${GREEN}✓ Type checking passed${NC}"
fi

echo ""

# 3. Unit tests
echo -e "${BLUE}3. Running unit tests...${NC}"
echo ""

if [ "$UNIT_ONLY" = true ]; then
    # Run only unit tests with coverage
    if pytest tests/unit/ -v --cov=backend --cov-report=term-missing --cov-report=html; then
        echo ""
        echo -e "${GREEN}✓ Unit tests passed${NC}"
    else
        echo ""
        echo -e "${RED}✗ Unit tests failed${NC}"
        exit 1
    fi
else
    # Run unit tests without coverage report (coverage will be in final run)
    if pytest tests/unit/ -v -q; then
        echo ""
        echo -e "${GREEN}✓ Unit tests passed${NC}"
    else
        echo ""
        echo -e "${RED}✗ Unit tests failed${NC}"
        exit 1
    fi
fi

echo ""

# 4. Integration tests (skip if --fast or --unit-only)
if [ "$FAST_MODE" = false ] && [ "$UNIT_ONLY" = false ]; then
    echo -e "${BLUE}4. Running integration tests...${NC}"
    echo -e "${YELLOW}   (This may take a few minutes...)${NC}"
    echo ""

    if pytest tests/integration/ -v --slow; then
        echo ""
        echo -e "${GREEN}✓ Integration tests passed${NC}"
    else
        echo ""
        echo -e "${RED}✗ Integration tests failed${NC}"
        exit 1
    fi

    echo ""
else
    if [ "$FAST_MODE" = true ]; then
        echo -e "${YELLOW}⊘ Skipping integration tests (--fast mode)${NC}"
        echo ""
    fi
fi

# 5. Generate coverage report (if not unit-only)
if [ "$UNIT_ONLY" = false ]; then
    echo -e "${BLUE}5. Generating coverage report...${NC}"
    echo ""

    if pytest --cov=backend --cov-report=term-missing --cov-report=html -q tests/unit/; then
        echo ""
        echo -e "${GREEN}✓ Coverage report generated${NC}"
        echo -e "   View at: ${BLUE}htmlcov/index.html${NC}"
    else
        echo ""
        echo -e "${YELLOW}⚠ Coverage report generation had issues${NC}"
    fi

    echo ""
fi

# Final summary
echo "======================================="
echo -e "${GREEN}ALL TESTS PASSED ✓${NC}"
echo "======================================="
echo ""

# Print summary
echo "Summary:"
echo -e "  ${GREEN}✓${NC} Code formatting (black)"
echo -e "  ${GREEN}✓${NC} Linting (flake8)"
echo -e "  ${GREEN}✓${NC} Import sorting (isort)"
echo -e "  ${GREEN}✓${NC} Type checking (mypy)"
echo -e "  ${GREEN}✓${NC} Unit tests"

if [ "$FAST_MODE" = false ] && [ "$UNIT_ONLY" = false ]; then
    echo -e "  ${GREEN}✓${NC} Integration tests"
fi

echo ""

# Show coverage summary if available
if [ -f ".coverage" ] && [ "$UNIT_ONLY" = false ]; then
    echo "Coverage Summary:"
    coverage report --skip-empty --skip-covered 2>/dev/null | tail -n 3 || true
    echo ""
fi

# Additional tips
echo "Next steps:"
echo "  • View detailed coverage: open htmlcov/index.html"
echo "  • Run E2E tests: pytest tests/e2e/ -v --slow"
echo "  • Test API: ./test_api.sh"
echo ""

exit 0
