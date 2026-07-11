#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# AdaptiveAgent — Verification Script
# ============================================================
# Checks that all prerequisites are correctly installed.
# Usage: bash scripts/verify.sh
# ============================================================

BOLD="\033[1m"
GREEN="\033[0;32m"
RED="\033[0;31m"
CYAN="\033[0;36m"
NC="\033[0m"

PASS=0
FAIL=0

check() {
    local name="$1"
    local cmd="$2"
    if eval "$cmd" &>/dev/null; then
        echo -e "  ${GREEN}✓${NC} $name"
        ((PASS++))
    else
        echo -e "  ${RED}✗${NC} $name"
        ((FAIL++))
    fi
}

echo ""
echo -e "${BOLD}AdaptiveAgent — Environment Verification${NC}"
echo ""

# ── System Tools ─────────────────────────────────────────────
echo -e "${CYAN}System Tools:${NC}"
check "Git" "git --version"
check "Python 3.11+" "python3 -c 'import sys; exit(0 if sys.version_info >= (3,11) else 1)'"
check "Node.js 20+" "node -e 'process.exit(0 if parseInt(process.version.slice(1)) >= 20 else 1)'"
check "npm" "npm --version"
check "Docker" "docker --version"
check "Docker Compose" "docker compose version"

# ── Backend ──────────────────────────────────────────────────
echo ""
echo -e "${CYAN}Backend:${NC}"
if [ -d "backend/.venv" ]; then
    check "Virtual environment" "true"
    check "FastAPI installed" "backend/.venv/bin/python -c 'import fastapi'"
    check "LangGraph installed" "backend/.venv/bin/python -c 'import langgraph'"
    check "Backend tests" "cd backend && .venv/bin/python -m pytest tests/ -q --tb=no 2>/dev/null"
else
    echo -e "  ${RED}✗${NC} Virtual environment (run setup.sh first)"
    ((FAIL++))
fi

# ── Frontend ─────────────────────────────────────────────────
echo ""
echo -e "${CYAN}Frontend:${NC}"
if [ -d "frontend/node_modules" ]; then
    check "node_modules installed" "true"
    check "TypeScript compiles" "cd frontend && npx tsc --noEmit 2>/dev/null"
else
    echo -e "  ${RED}✗${NC} node_modules (run setup.sh first)"
    ((FAIL++))
fi

# ── Configuration ────────────────────────────────────────────
echo ""
echo -e "${CYAN}Configuration:${NC}"
check ".env file exists" "test -f backend/.env"
check "Docker Compose valid" "docker compose -f infra/docker-compose.yml config --quiet 2>/dev/null"

# ── Summary ──────────────────────────────────────────────────
echo ""
echo -e "${BOLD}Results: ${GREEN}${PASS} passed${NC}, ${RED}${FAIL} failed${NC}"
echo ""

if [ "$FAIL" -gt 0 ]; then
    echo -e "${RED}Some checks failed. Run 'bash scripts/setup.sh' to fix.${NC}"
    exit 1
else
    echo -e "${GREEN}All checks passed! You're ready to go.${NC}"
    echo ""
    echo -e "  ${CYAN}Start the stack:${NC}"
    echo "    cd infra && docker compose up -d --build"
    echo ""
fi
