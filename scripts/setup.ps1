#Requires -Version 5.1
<#
.SYNOPSIS
    AdaptiveAgent — Windows Setup Script

.DESCRIPTION
    Sets up the AdaptiveAgent development environment on Windows.
    Checks prerequisites, installs dependencies, and configures the project.

.EXAMPLE
    .\scripts\setup.ps1
    or: powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
#>

$ErrorActionPreference = "Stop"

# ── Helpers ──────────────────────────────────────────────────
function Write-Info    { param([string]$msg) Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Ok      { param([string]$msg) Write-Host "[OK]   $msg" -ForegroundColor Green }
function Write-Warn    { param([string]$msg) Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err     { param([string]$msg) Write-Host "[ERR]  $msg" -ForegroundColor Red }

function Test-Command {
    param([string]$cmd)
    $null -ne (Get-Command $cmd -ErrorAction SilentlyContinue)
}

function Install-IfMissing {
    param(
        [string]$Name,
        [string]$CheckCmd,
        [scriptblock]$InstallBlock
    )
    if (Test-Command $CheckCmd) {
        Write-Ok "$Name is installed"
    } else {
        Write-Warn "$Name not found. Installing..."
        & $InstallBlock
        if (Test-Command $CheckCmd) {
            Write-Ok "$Name installed successfully"
        } else {
            Write-Err "Failed to install $Name. Please install manually."
            exit 1
        }
    }
}

# ── Banner ───────────────────────────────────────────────────
Write-Host ""
Write-Host "===============================================" -ForegroundColor White
Write-Host "     AdaptiveAgent — Development Setup         " -ForegroundColor White
Write-Host "     Platform: Windows                         " -ForegroundColor White
Write-Host "===============================================" -ForegroundColor White
Write-Host ""

# ── Git ──────────────────────────────────────────────────────
Write-Info "Checking Git..."
Install-IfMissing "Git" "git" {
    Write-Err "Please install Git from https://git-scm.com/download/win"
    exit 1
}

# ── Python ───────────────────────────────────────────────────
Write-Info "Checking Python 3.11+..."
if (Test-Command "python") {
    $pyVer = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    $pyMajor = [int]($pyVer.Split('.')[0])
    $pyMinor = [int]($pyVer.Split('.')[1])
    if ($pyMajor -ge 3 -and $pyMinor -ge 11) {
        Write-Ok "Python $pyVer is installed"
    } else {
        Write-Err "Python 3.11+ required, found $pyVer"
        Write-Info "Download from https://www.python.org/downloads/"
        exit 1
    }
} else {
    Write-Warn "Python not found."
    Write-Info "Please install Python 3.12+ from https://www.python.org/downloads/"
    Write-Info "IMPORTANT: Check 'Add Python to PATH' during installation."
    exit 1
}

# ── Node.js ──────────────────────────────────────────────────
Write-Info "Checking Node.js 20+..."
if (Test-Command "node") {
    $nodeVer = node -v
    $nodeMajor = [int]($nodeVer.TrimStart('v').Split('.')[0])
    if ($nodeMajor -ge 20) {
        Write-Ok "Node.js $nodeVer is installed"
    } else {
        Write-Warn "Node.js 20+ required, found $nodeVer."
        Write-Info "Download from https://nodejs.org/"
        exit 1
    }
} else {
    Write-Warn "Node.js not found."
    Write-Info "Please install Node.js 22+ from https://nodejs.org/"
    exit 1
}

# ── Docker ───────────────────────────────────────────────────
Write-Info "Checking Docker..."
if (Test-Command "docker") {
    Write-Ok "Docker is installed"
    try {
        docker compose version | Out-Null
        Write-Ok "Docker Compose is installed"
    } catch {
        Write-Err "Docker Compose v2 required. Update Docker Desktop."
        exit 1
    }
} else {
    Write-Err "Docker not found."
    Write-Info "Install Docker Desktop from https://docs.docker.com/docker-for-windows/install/"
    exit 1
}

# ── Setup Project ────────────────────────────────────────────
Write-Host ""
Write-Info "Setting up AdaptiveAgent..."
Write-Host ""

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

# Backend setup
Write-Info "Setting up backend..."
Set-Location backend

if (-not (Test-Path ".venv")) {
    python -m venv .venv
    Write-Ok "Created Python virtual environment"
}

# Activate venv
& ".venv\Scripts\Activate.ps1"

python -m pip install --upgrade pip --quiet
pip install -e ".[dev]" --quiet
Write-Ok "Backend dependencies installed"

if (-not (Test-Path ".env")) {
    Copy-Item .env.example .env
    Write-Ok "Environment file created from template"
}

Set-Location ..

# Frontend setup
Write-Info "Setting up frontend..."
Set-Location frontend

npm ci --silent
Write-Ok "Frontend dependencies installed"

Set-Location ..

Write-Host ""
Write-Host "===============================================" -ForegroundColor Green
Write-Host "          Setup Complete!                       " -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Quick Start:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Option 1 - Docker (recommended):" -ForegroundColor White
Write-Host "    cd infra; docker compose up -d --build"
Write-Host ""
Write-Host "  Option 2 - Manual (local development):" -ForegroundColor White
Write-Host "    Terminal 1 (Backend):"
Write-Host "      cd backend; .venv\Scripts\activate; uvicorn app.main:app --reload"
Write-Host "    Terminal 2 (Frontend):"
Write-Host "      cd frontend; npm run dev"
Write-Host "    Terminal 3 (Services):"
Write-Host "      docker compose -f infra/docker-compose.yml up postgres redis ollama"
Write-Host ""
Write-Host "Access:" -ForegroundColor Cyan
Write-Host "  Frontend:  http://localhost:3000"
Write-Host "  API Docs:  http://localhost:8000/docs"
Write-Host "  Health:    http://localhost:8000/health"
Write-Host ""
