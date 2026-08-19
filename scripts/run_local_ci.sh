#!/bin/bash
# =========================================================================
# FingerSwipe Local CI Pipeline Simulator
# Replicates the exact steps executed in .github/workflows/ci.yml
# =========================================================================

set -e

# Color helpers
GREEN="\033[0;32m"
RED="\033[0;31m"
BLUE="\033[0;34m"
CYAN="\033[0;36m"
BOLD="\033[1m"
NC="\033[0m"

log_step() {
    echo -e "\n${BLUE}${BOLD}[STEP $1/$2]${NC} ${CYAN}$3${NC}"
}

log_pass() {
    echo -e "${GREEN}✓ $1${NC}"
}

log_fail() {
    echo -e "${RED}✗ $1${NC}"
    exit 1
}

TOTAL_STEPS=8
START_TIME=$(date +%s)

echo -e "${BOLD}======================================================${NC}"
echo -e "${BOLD}   FingerSwipe — Local CI Pipeline Simulator          ${NC}"
echo -e "${BOLD}======================================================${NC}"

# Step 1: Clean & Compile Native C Library (-Werror)
log_step 1 $TOTAL_STEPS "Compiling Native C Library (C23 with -Werror)"
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --clean-first --parallel
log_pass "Native C library compiled successfully."

# Step 2: Environment Check
log_step 2 $TOTAL_STEPS "Verifying Python 3.13 Virtual Environment & UV"
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment with uv..."
    uv venv --python 3.13 .venv
fi
uv pip install --python .venv/bin/python -e ".[dev]" --quiet
log_pass "Python environment and dev dependencies verified."

# Step 3: Linting with Ruff
log_step 3 $TOTAL_STEPS "Running Ruff Code Quality Linter"
.venv/bin/ruff check src tests install
log_pass "Ruff static analysis passed (0 issues)."

# Step 4: Type Checking with Mypy
log_step 4 $TOTAL_STEPS "Running Mypy Type Checker"
.venv/bin/mypy src tests
log_pass "Mypy type checking passed (0 issues across all source files)."

# Step 5: Test Suite Execution with Pytest
log_step 5 $TOTAL_STEPS "Running Pytest Unit & Integration Suite"
.venv/bin/pytest -v --tb=short
log_pass "All test cases passed."

# Step 6: Build Python Wheel Distribution
log_step 6 $TOTAL_STEPS "Building Python Wheel & Sdist via uv"
mkdir -p dist
uv build
log_pass "Python wheel & source distribution built successfully."

# Step 7: Build Debian Package
log_step 7 $TOTAL_STEPS "Building & Verifying Debian Package (.deb)"
chmod +x ./build_deb.sh
./build_deb.sh
log_pass "Debian package built and verified."

# Step 8: Build Universal Linux Package
log_step 8 $TOTAL_STEPS "Building & Verifying Universal Linux Package (.tar.gz)"
chmod +x ./install/build_universal.sh
./install/build_universal.sh
log_pass "Universal Linux package built and verified."

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo -e "\n${BOLD}======================================================${NC}"
echo -e "${GREEN}${BOLD}🎉 ALL CI CHECKS PASSED IN ${DURATION}s — READY FOR PUSH!${NC}"
echo -e "${BOLD}======================================================${NC}\n"
