#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# AdaptiveAgent — Cross-Platform Setup Script (macOS / Linux)
# ============================================================
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/YogendraChukka01/AdaptiveAgent/main/scripts/setup.sh | bash
#   or: bash scripts/setup.sh
# ============================================================

BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
CYAN="\033[0;36m"
NC="\033[0m"

info()    { echo -e "${CYAN}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC}   $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[ERR]${NC}  $1"; }

# ── Detect OS ────────────────────────────────────────────────
OS="$(uname -s)"
case "${OS}" in
    Linux*)   PLATFORM=linux;;
    Darwin*)  PLATFORM=macos;;
    *)        error "Unsupported OS: ${OS}"; exit 1;;
esac

echo ""
echo -e "${BOLD}╔══════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║     AdaptiveAgent — Development Setup        ║${NC}"
echo -e "${BOLD}║     Platform: ${PLATFORM}                         ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════════╝${NC}"
echo ""

# ── Check & Install Prerequisites ───────────────────────────

check_command() {
    command -v "$1" &>/dev/null
}

install_if_missing() {
    local cmd="$1"
    local install_cmd="$2"
    local check_cmd="${3:-$cmd}"

    if check_command "$check_cmd"; then
        success "$cmd is installed"
    else
        warn "$cmd not found. Installing..."
        eval "$install_cmd"
        if check_command "$check_cmd"; then
            success "$cmd installed successfully"
        else
            error "Failed to install $cmd. Please install manually."
            exit 1
        fi
    fi
}

# ── Git ──────────────────────────────────────────────────────
info "Checking Git..."
install_if_missing "Git" \
    "error 'Please install Git from https://git-scm.com' && exit 1" \
    "git"

# ── Python ───────────────────────────────────────────────────
info "Checking Python 3.11+..."
if check_command python3; then
    PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
    PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)
    if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 11 ]; then
        success "Python ${PY_VERSION} is installed"
    else
        error "Python 3.11+ required, found ${PY_VERSION}"
        exit 1
    fi
else
    if [ "$PLATFORM" = "macos" ]; then
        warn "Python3 not found. Installing via Homebrew..."
        if ! check_command brew; then
            error "Homebrew required. Install from https://brew.sh"
            exit 1
        fi
        brew install python@3.12
    else
        warn "Python3 not found. Installing via apt..."
        sudo apt-get update && sudo apt-get install -y python3.12 python3.12-venv python3-pip
    fi
    success "Python installed"
fi

# ── Node.js ──────────────────────────────────────────────────
info "Checking Node.js 20+..."
if check_command node; then
    NODE_VERSION=$(node -v | sed 's/v//' | cut -d. -f1)
    if [ "$NODE_VERSION" -ge 20 ]; then
        success "Node.js $(node -v) is installed"
    else
        warn "Node.js 20+ required, found $(node -v). Upgrading..."
        if [ "$PLATFORM" = "macos" ]; then
            brew install node@22
        else
            curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
            sudo apt-get install -y nodejs
        fi
    fi
else
    warn "Node.js not found. Installing..."
    if [ "$PLATFORM" = "macos" ]; then
        brew install node@22
    else
        curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
        sudo apt-get install -y nodejs
    fi
    success "Node.js installed"
fi

# ── Docker ───────────────────────────────────────────────────
info "Checking Docker..."
if check_command docker; then
    success "Docker is installed"
else
    warn "Docker not found."
    if [ "$PLATFORM" = "macos" ]; then
        error "Install Docker Desktop from https://docs.docker.com/docker-for-mac/install/"
    else
        error "Install Docker from https://docs.docker.com/engine/install/"
    fi
    error "Docker is required to run the full stack."
    exit 1
fi

if check_command docker; then
    info "Checking Docker Compose..."
    if docker compose version &>/dev/null; then
        success "Docker Compose is installed"
    else
        error "Docker Compose v2 required. Update Docker Desktop."
        exit 1
    fi
fi

# ── Setup Project ────────────────────────────────────────────
echo ""
info "Setting up AdaptiveAgent..."
echo ""

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# Backend setup
info "Setting up backend..."
cd backend
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    success "Created Python virtual environment"
fi

source .venv/bin/activate
pip install --upgrade pip --quiet
pip install -e ".[dev]" --quiet
success "Backend dependencies installed"

cp -n .env.example .env 2>/dev/null || true
success "Environment file ready"

cd ..

# Frontend setup
info "Setting up frontend..."
cd frontend
npm ci --silent
success "Frontend dependencies installed"

cd ..

echo ""
echo -e "${BOLD}╔══════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║          Setup Complete!                      ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Quick Start:${NC}"
echo ""
echo -e "  ${BOLD}Option 1 — Docker (recommended):${NC}"
echo "    cd infra && docker compose up -d --build"
echo ""
echo -e "  ${BOLD}Option 2 — Manual (local development):${NC}"
echo "    Terminal 1 (Backend):"
echo "      cd backend && source .venv/bin/activate && uvicorn app.main:app --reload"
echo "    Terminal 2 (Frontend):"
echo "      cd frontend && npm run dev"
echo "    Terminal 3 (Services):"
echo "      docker compose -f infra/docker-compose.yml up postgres redis ollama"
echo ""
echo -e "${CYAN}Access:${NC}"
echo "  Frontend:  http://localhost:3000"
echo "  API Docs:  http://localhost:8000/docs"
echo "  Health:    http://localhost:8000/health"
echo ""
echo -e "${CYAN}Useful Commands:${NC}"
echo "  make help        — Show all available commands"
echo "  make test        — Run backend tests"
echo "  make lint        — Run linters"
echo "  make docker-up   — Start full Docker stack"
echo ""
