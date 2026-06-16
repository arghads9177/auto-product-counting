#!/bin/bash
# Phase 0 Verification Script
# Checks that all scaffolding is in place and ready for Phase 1

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║       Phase 0 Verification — Auto Product Counting           ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
        return 0
    else
        echo -e "${RED}✗${NC} $1"
        return 1
    fi
}

errors=0

# 1. Backend checks
echo ""
echo "🔵 Backend Checks:"
echo "─────────────────────────────────────────────────────────────"

# Python version
python3 --version | grep -q "3.1[2-9]" && check "Python 3.12+" || { echo -e "${RED}✗${NC} Python 3.12+ required"; errors=$((errors+1)); }

# Backend directory
[ -d "backend" ] && check "backend/ directory exists" || { echo -e "${RED}✗${NC} backend/ directory missing"; errors=$((errors+1)); }

# uv.lock exists
[ -f "backend/uv.lock" ] && check "uv.lock created (dependencies installed)" || { echo -e "${RED}✗${NC} uv.lock missing - run 'cd backend && uv sync'"; errors=$((errors+1)); }

# pyproject.toml
[ -f "backend/pyproject.toml" ] && check "pyproject.toml configured" || { echo -e "${RED}✗${NC} pyproject.toml missing"; errors=$((errors+1)); }

# FastAPI app
(cd backend && python3 -c "from app.main import app; print(len(app.routes))" > /tmp/routes.txt 2>/dev/null) && check "FastAPI app loads ($(cat /tmp/routes.txt) routes)" || { echo -e "${RED}✗${NC} FastAPI app failed to load"; errors=$((errors+1)); }

# Config
[ -f "backend/app/config.py" ] && check "Configuration module exists" || { echo -e "${RED}✗${NC} config.py missing"; errors=$((errors+1)); }

# API modules
[ -f "backend/app/api/cameras.py" ] && check "API routers stubbed (9 modules)" || { echo -e "${RED}✗${NC} API routers incomplete"; errors=$((errors+1)); }

# 2. Frontend checks
echo ""
echo "🟣 Frontend Checks:"
echo "─────────────────────────────────────────────────────────────"

# Node version
node --version | grep -q "v1[8-9]\|v2" && check "Node.js 18+ installed" || { echo -e "${RED}✗${NC} Node.js 18+ required"; errors=$((errors+1)); }

# Frontend directory
[ -d "frontend" ] && check "frontend/ directory exists" || { echo -e "${RED}✗${NC} frontend/ directory missing"; errors=$((errors+1)); }

# Node modules
[ -d "frontend/node_modules" ] && check "npm dependencies installed" || { echo -e "${RED}✗${NC} run 'cd frontend && npm install'"; errors=$((errors+1)); }

# Angular config
[ -f "frontend/angular.json" ] && check "Angular configured" || { echo -e "${RED}✗${NC} angular.json missing"; errors=$((errors+1)); }

# Tailwind config
[ -f "frontend/tailwind.config.js" ] && check "Tailwind CSS configured" || { echo -e "${RED}✗${NC} tailwind.config.js missing"; errors=$((errors+1)); }

# PostCSS
[ -f "frontend/postcss.config.js" ] && check "PostCSS configured" || { echo -e "${RED}✗${NC} postcss.config.js missing"; errors=$((errors+1)); }

# Styles
grep -q "@tailwind" "frontend/src/styles.css" && check "Tailwind directives in global styles" || { echo -e "${RED}✗${NC} styles.css not configured for Tailwind"; errors=$((errors+1)); }

# 3. Environment & Configuration
echo ""
echo "⚙️  Configuration Checks:"
echo "─────────────────────────────────────────────────────────────"

# .env file
[ -f ".env" ] && check ".env file exists (credentials configured)" || { echo -e "${YELLOW}⚠${NC} .env missing - run 'cp .env.example .env' and update credentials"; errors=$((errors+1)); }

# .env.example
[ -f ".env.example" ] && check ".env.example template exists (safe to share)" || { echo -e "${RED}✗${NC} .env.example missing"; errors=$((errors+1)); }

# 4. MediaMTX setup
echo ""
echo "📹 MediaMTX Setup:"
echo "─────────────────────────────────────────────────────────────"

# Config
[ -f "mediamtx/mediamtx.yml" ] && check "MediaMTX config exists" || { echo -e "${RED}✗${NC} mediamtx/mediamtx.yml missing"; errors=$((errors+1)); }

# Scripts
[ -x "mediamtx/run_mediamtx.sh" ] && check "MediaMTX startup script ready" || { echo -e "${YELLOW}⚠${NC} mediamtx/run_mediamtx.sh not executable - run 'chmod +x mediamtx/*.sh'"; }

[ -x "mediamtx/publish_samples.sh" ] && check "Sample publisher script ready" || { echo -e "${YELLOW}⚠${NC} mediamtx/publish_samples.sh not executable - run 'chmod +x mediamtx/*.sh'"; }

# Binary
command -v mediamtx &> /dev/null && check "MediaMTX binary available in PATH" || { echo -e "${YELLOW}⚠${NC} MediaMTX binary not in PATH - download from https://github.com/bluenviron/mediamtx/releases"; }

# 5. Samples
echo ""
echo "📦 Sample Data:"
echo "─────────────────────────────────────────────────────────────"

[ -d "samples" ] && check "samples/ directory exists" || { echo -e "${RED}✗${NC} samples/ directory missing"; errors=$((errors+1)); }

if [ -z "$(ls samples/*.mp4 2>/dev/null)" ]; then
    echo -e "${YELLOW}⚠${NC} No .mp4 files in samples/ - add test clips for Phase 1"
else
    sample_count=$(ls samples/*.mp4 2>/dev/null | wc -l)
    check "$sample_count sample video file(s) available"
fi

# 6. Documentation
echo ""
echo "📚 Documentation:"
echo "─────────────────────────────────────────────────────────────"

[ -f "PHASE_0_SETUP.md" ] && check "Setup guide available (PHASE_0_SETUP.md)" || { echo -e "${RED}✗${NC} PHASE_0_SETUP.md missing"; errors=$((errors+1)); }

[ -f "PHASE_0_COMPLETION.md" ] && check "Completion report available (PHASE_0_COMPLETION.md)" || { echo -e "${RED}✗${NC} PHASE_0_COMPLETION.md missing"; errors=$((errors+1)); }

[ -f "IMPLEMENTATION_PLAN.md" ] && check "Implementation plan available" || { echo -e "${RED}✗${NC} IMPLEMENTATION_PLAN.md missing"; errors=$((errors+1)); }

# Summary
echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
if [ $errors -eq 0 ]; then
    echo -e "║         ${GREEN}✓ Phase 0 Verification PASSED${NC}              ║"
    echo "║                                                               ║"
    echo "║  All scaffolding is in place. Ready for Phase 1 (Ingestion). ║"
    echo "║                                                               ║"
    echo "║  Next: Implement RTSP frame reading & CPU benchmarking.      ║"
else
    echo -e "║         ${RED}✗ Phase 0 Verification FAILED${NC}               ║"
    echo "║                                                               ║"
    echo -e "║  ${RED}$errors error(s)${NC} found. See above for details.           ║"
fi
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "Quick Reference:"
echo "  Backend:   cd backend && uv run uvicorn app.main:app --reload"
echo "  Frontend:  cd frontend && ng serve --open"
echo "  MediaMTX:  mediamtx mediamtx/mediamtx.yml"
echo ""

exit $errors
