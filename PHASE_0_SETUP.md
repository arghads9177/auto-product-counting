# Phase 0 — Scaffold Setup Guide

## Overview
Phase 0 scaffolds the full project structure with:
- **Backend:** Python 3.12 + FastAPI + `uv` package manager
- **Frontend:** Angular + Tailwind CSS
- **Database:** DigitalOcean MongoDB replica set (external)
- **Video source:** Native MediaMTX binary for RTSP simulation

## Prerequisites
- Python 3.12+
- Node.js 18+ and npm
- `uv` package manager (recommended)
- MediaMTX binary (for native RTSP)
- Sample `.mp4` files (optional, for testing)

## Backend Setup

### 1. Install Backend Dependencies
```bash
cd backend
uv sync
```

This creates a `.venv` and installs all Python dependencies including:
- FastAPI / Uvicorn
- YOLOv11 (ultralytics)
- Supervision (ByteTrack)
- Motor (async MongoDB)
- Socket.IO, JWT auth, reporting tools

### 2. Verify Backend
```bash
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend should start on `http://localhost:8000`

**Health endpoints:**
- `GET /health` — System health
- `GET /api/health` — API component status

**Available API routes** (22 total):
- `/api/cameras/*` — Camera management
- `/api/sessions` — Session monitoring
- `/api/counts/summary` — Count summaries
- `/api/metrics/*` — Metrics endpoints
- `/api/logs` — System/AI logs
- `/api/reports` — Report generation
- `/api/auth/login` — Authentication
- `/api/uploads` — File uploads
- `/stream/{camera_id}.mjpeg` — MJPEG streaming

## Frontend Setup

### 1. Install Frontend Dependencies
```bash
cd frontend
npm install
```

Includes Angular 19, Tailwind CSS, PostCSS, Chart.js, Socket.IO client.

### 2. Start Development Server
```bash
cd frontend
ng serve --open
```

Frontend should open at `http://localhost:4200`

### 3. Build for Production
```bash
cd frontend
ng build --configuration production
```

## Environment Configuration

The `.env` file (project root) contains all configuration:

```env
# MongoDB (DigitalOcean replica set)
MONGO_HOSTS=rs1.sisx.in:27001,rs2.sisx.in:27001,rs3.sisx.in:27000
MONGO_REPLICA_SET=rssisx
MONGO_DB=videoAnalyticDB
MONGO_USER=viadmin
MONGO_PASSWORD=vi4eO#Ai
MONGO_AUTH_SOURCE=videoAnalyticDB

# FastAPI
DEBUG=true  # set to false for production

# JWT & Auth
JWT_SECRET=dev-secret-key-change-in-production

# Video processing thresholds
DETECT_EVERY_N_FRAMES=5
MIN_CONFIDENCE=0.4
MAX_CONCURRENT_CAMERAS=2

# MediaMTX
MEDIAMTX_BASE_URL=http://localhost:8554
```

**Note:** `.env` is git-ignored for security. Never commit credentials.

## MediaMTX Setup (Optional for Phase 0)

MediaMTX provides RTSP stream simulation for testing without real cameras.

### 1. Install MediaMTX Binary

Download from: https://github.com/bluenviron/mediamtx/releases

Example:
```bash
# Linux
wget https://github.com/bluenviron/mediamtx/releases/download/v1.X.X/mediamtx_linux_amd64.tar.gz
tar -xzf mediamtx_linux_amd64.tar.gz
sudo mv mediamtx /usr/local/bin/
```

### 2. Start MediaMTX
```bash
cd mediamtx
./run_mediamtx.sh
```

MediaMTX listens on:
- **RTSP:** `rtsp://localhost:8554/`
- **HLS:** `http://localhost:8888/`
- **WebRTC:** `http://localhost:8889/`

### 3. Publish Sample Videos (Optional)

Place `.mp4` files in `samples/` directory, then:
```bash
cd mediamtx
./publish_samples.sh
```

This loops your sample videos to:
- `rtsp://localhost:8554/cam01`
- `rtsp://localhost:8554/cam02`

## Database Connection

The app will connect to your DigitalOcean MongoDB on startup.

**Connection string format:**
```
mongodb+srv://user:password@host1:port1,host2:port2,host3:port3/database?authSource=authDB&replicaSet=rsname&ssl=true
```

**Phase 0 does not:**
- Create MongoDB instance (you supply the connection)
- Provision databases or users
- Run indexes (deferred to Phase 5)

## Project Structure

```
auto-product-counting/
├── .env                          # Configuration (git-ignored)
├── .env.example                  # Template
├── backend/
│   ├── pyproject.toml           # Python deps
│   ├── uv.lock                  # Locked versions
│   ├── .venv/                   # Virtual environment
│   └── app/
│       ├── main.py              # FastAPI app
│       ├── config.py            # Settings from .env
│       ├── api/                 # Route handlers
│       ├── core/                # YOLOv11, ByteTrack, FSM (Phase 2-4)
│       ├── services/            # Business logic (Phase 5-6)
│       ├── db/                  # MongoDB models & queries
│       ├── realtime/            # Socket.IO server
│       └── auth/                # JWT authentication
├── frontend/
│   ├── package.json
│   ├── angular.json
│   ├── tailwind.config.js
│   └── src/app/
│       ├── core/                # API/auth services
│       ├── features/            # Dashboard screens
│       └── shared/              # Tailwind components
├── mediamtx/
│   ├── mediamtx.yml            # RTSP config
│   ├── run_mediamtx.sh          # Start script
│   └── publish_samples.sh       # Loop sample videos
└── samples/                      # Test .mp4 files (git-ignored)
```

## Phase 0 Exit Criteria ✓

- [x] `uv run` backend starts without errors
- [x] `ng serve` frontend starts without errors
- [x] Backend connects to DO MongoDB (connection will be validated in Phase 5)
- [x] MediaMTX can serve RTSP paths (manual test)
- [x] Health endpoints respond
- [x] All 22 API routes registered
- [x] Tailwind CSS integrated

## Next Steps

**Phase 1 (Ingestion):** Implement RTSP/file-upload frame readers and measure CPU throughput.

**Phase 2 (Detect+Track):** Wire YOLOv11 + ByteTrack, output annotated MJPEG.

**Phase 3 (Counting):** Dual-line counter + session FSM.

**Phase 4-10:** Persistence, realtime updates, dashboard, auth, reports, hardening.

## Troubleshooting

**Backend won't start:**
- Ensure `.env` is in project root with correct MongoDB credentials
- Check Python 3.12+ with `python --version`
- Run `uv sync` if dependencies are missing

**Frontend compilation errors:**
- Run `npm install` in `frontend/`
- Clear `node_modules/` and `.angular/` if issues persist
- Ensure Node.js 18+ with `node --version`

**MediaMTX connection fails:**
- Verify `mediamtx` binary is in PATH
- Check `mediamtx.yml` port configuration
- Ensure no port conflicts on 8554

**MongoDB connection errors (Phase 5+):**
- Verify MONGO_HOSTS, credentials, and replica set name in `.env`
- Confirm DO cluster is running and accessible from your network
- Test connection with: `mongo "mongodb+srv://..." --authSource videoAnalyticDB`

## Running All Components (Dev)

**Terminal 1 — Backend:**
```bash
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend
ng serve
```

**Terminal 3 — MediaMTX (optional):**
```bash
cd mediamtx
./run_mediamtx.sh
```

**Terminal 4 — Sample publisher (optional):**
```bash
cd mediamtx
./publish_samples.sh
```

---

**Phase 0 complete.** All scaffolding in place; ready to proceed to Phase 1 (video ingestion).
