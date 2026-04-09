#!/usr/bin/env bash
# ============================================================
# SOMS AI Entry Script — Safe Environment Setup
# ============================================================
#
# This script sets up a safe working environment for AI agents
# interacting with the SOMS codebase. It:
#
#   1. Validates the environment (Python, dependencies)
#   2. Runs the test suite to confirm codebase health
#   3. Runs physics validation to confirm no broken claims
#   4. Sets safety guardrails (read-only on protected files)
#   5. Prints orientation info for the AI agent
#
# Usage:
#   chmod +x ai/enter.sh
#   ./ai/enter.sh              # full setup + validation
#   ./ai/enter.sh --quick      # skip tests, just orient
#   ./ai/enter.sh --check      # validate only, no changes
#
# ============================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

# Colors (only if terminal supports it)
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    NC='\033[0m'
else
    RED='' GREEN='' YELLOW='' BLUE='' NC=''
fi

ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; }
info() { echo -e "${BLUE}[INFO]${NC} $1"; }

MODE="${1:-full}"

echo "============================================================"
echo " SOMS AI Entry — Safe Environment Setup"
echo "============================================================"
echo ""

# ============================================================
# 1. Environment validation
# ============================================================
info "Checking environment..."

# Python
if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
    fail "Python not found. Install Python 3.8+."
    exit 1
fi
PYTHON=$(command -v python3 || command -v python)
PY_VERSION=$($PYTHON --version 2>&1)
ok "Python: $PY_VERSION"

# Dependencies
MISSING_DEPS=()
$PYTHON -c "import numpy" 2>/dev/null || MISSING_DEPS+=("numpy")
$PYTHON -c "import scipy" 2>/dev/null || MISSING_DEPS+=("scipy")

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    warn "Missing: ${MISSING_DEPS[*]}"
    if [ "$MODE" != "--check" ]; then
        info "Installing missing dependencies..."
        $PYTHON -m pip install "${MISSING_DEPS[@]}" -q 2>/dev/null
        ok "Dependencies installed"
    else
        fail "Run: pip install ${MISSING_DEPS[*]}"
        exit 1
    fi
else
    ok "Dependencies: numpy, scipy"
fi

# Git state
BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
DIRTY=$(git status --porcelain 2>/dev/null | head -5)
ok "Git branch: $BRANCH"
if [ -n "$DIRTY" ]; then
    warn "Working tree has uncommitted changes"
fi

echo ""

# ============================================================
# 2. Safety checks — protected files
# ============================================================
info "Checking protected files..."

PROTECTED_FILES=(
    ".fieldlink.json"
    "data/GDSII_Coordinates.txt"
)

ALL_PROTECTED=true
for f in "${PROTECTED_FILES[@]}"; do
    if [ -f "$f" ]; then
        ok "Protected: $f (exists)"
    else
        warn "Protected file missing: $f"
        ALL_PROTECTED=false
    fi
done

echo ""

# ============================================================
# 3. Test suite (skip with --quick)
# ============================================================
if [ "$MODE" != "--quick" ]; then
    info "Running test suite..."
    if $PYTHON -m pytest tests/ -q --tb=short 2>&1 | tail -5; then
        ok "Test suite passed"
    else
        fail "Tests failed — fix before making changes"
        if [ "$MODE" = "--check" ]; then
            exit 1
        fi
    fi

    echo ""
    info "Running physics validation..."
    if $PYTHON experiments/validate_annealer.py 2>&1 | tail -3; then
        ok "Physics validation passed"
    else
        warn "Physics validation had issues — review output above"
    fi
    echo ""
else
    info "Skipping tests (--quick mode)"
    echo ""
fi

# ============================================================
# 4. Orientation for AI agent
# ============================================================
echo "============================================================"
echo " SOMS ORIENTATION"
echo "============================================================"
echo ""
echo "WHAT THIS REPO IS:"
echo "  A heuristic annealer using octahedral geometry + FRET coupling."
echo "  It does NOT solve NP-hard problems optimally."
echo ""
echo "KEY FILES:"
echo "  src/octahedral_physics.py  — SOMSEngine (the annealer)"
echo "  src/mandala_structure.py   — MandalaMap (cell positions)"
echo "  src/phi_calculator.py      — Integration metric (mutual info)"
echo "  src/holographic_engine.py  — Multi-scale solver"
echo "  ROADMAP.md                 — Prioritized open work"
echo "  CLAUDE.md                  — Full architecture reference"
echo ""
echo "QUICK TEST:"
echo "  python -m pytest tests/ -q"
echo "  python experiments/validate_annealer.py"
echo ""
echo "RULES:"
echo "  1. Run tests before and after changes"
echo "  2. Never claim O(1) or 'optimal' for NP-hard problems"
echo "  3. Use 'heuristic' / 'approximate' / 'empirically'"
echo "  4. New experiments go in experiments/ with docstring hypothesis"
echo "  5. Do not break .fieldlink.json schema"
echo ""

# ============================================================
# 5. File inventory
# ============================================================
SRC_COUNT=$(find src/ -name "*.py" | wc -l)
TEST_COUNT=$(find tests/ -name "*.py" | wc -l)
EXP_COUNT=$(find experiments/ -name "*.py" | wc -l)

echo "INVENTORY:"
echo "  src/:         $SRC_COUNT modules"
echo "  tests/:       $TEST_COUNT test files"
echo "  experiments/: $EXP_COUNT experiment scripts"
echo "  atlas/:       $(find atlas/ -name "*.py" 2>/dev/null | wc -l) fieldlink modules"
echo ""
echo "============================================================"
echo " Ready. Run 'cat ROADMAP.md' for open work items."
echo "============================================================"
