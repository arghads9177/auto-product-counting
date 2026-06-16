# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

YOLOv11 + ByteTrack loading/unloading product counting system. Monitors warehouse cameras to auto-detect and count products during truck loading/unloading sessions.

**Stack (locked for POC — do not change):**
- Backend: Python 3.12 + FastAPI managed by `uv`
- Frontend: Angular 19 + Tailwind CSS
- Database: MongoDB on DigitalOcean managed replica set (external — never local)
- Video: Native MediaMTX binary for RTSP simulation (never Docker)
- Detection: YOLOv11n (CPU-only, pretrained COCO)

## Commands

### Backend

Run from the `backend/` directory. The `.env` file is one level up (project root).

```bash
# Install / sync deps
cd backend && uv sync

# Run dev server
cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run a single test file
cd backend && uv run pytest tests/test_foo.py -v

# Verify app loads
cd backend && python -c "from app.main import app; print(len(app.routes), 'routes')"
```

### Frontend

```bash
cd frontend && npm install        # install deps
cd frontend && ng serve --open    # dev server → http://localhost:4200
cd frontend && ng build           # production build
cd frontend && ng test            # Karma/Jasmine unit tests
```

### MediaMTX (RTSP simulation)

```bash
mediamtx mediamtx/mediamtx.yml          # start RTSP server (requires binary in PATH)
cd mediamtx && ./publish_samples.sh      # loop samples/*.mp4 → rtsp://localhost:8554/cam01|cam02
```

### Verification

```bash
bash verify_phase0.sh   # checks all components are wired up
```

## Architecture

### Data Flow

```
MediaMTX (RTSP :8554)
    │ frames
    ▼
CameraWorker (multiprocessing, one OS process per camera)
    │ YOLO detect → ByteTrack → dual-line count → FSM
    │ events via multiprocessing.Queue
    ▼
EventBus (app/services/event_bus.py)
    ├── persist → MongoDB (motor async)
    └── broadcast → Socket.IO (python-socketio)
                        │
                        ▼
                Angular Dashboard (Socket.IO client)
```

### Key Design Choices

**Per-camera OS processes:** Python GIL makes threads insufficient for parallel YOLOv11 inference on CPU. Each `CameraWorker` runs in its own `multiprocessing.Process`; the main FastAPI process owns the event bus, API, and DB writes. Workers communicate via `multiprocessing.Queue`.

**MJPEG streaming:** Annotated frames (bounding boxes, track IDs, counting lines) are served as `StreamingResponse` with `multipart/x-mixed-replace` — browser-native, no WebRTC. Endpoint: `GET /stream/{camera_id}.mjpeg`.

**Dual-line counting:** Two virtual lines A and B per camera. A crossing sequence A→B counts as loading; B→A as unloading. A `{track_id: counted}` dict deduplicates per session. This rejects single-frame jitter and oscillations.

**Activity FSM (per camera):** `IDLE → ACTIVE(LOADING|UNLOADING) → COMPLETED`. Transitions are triggered by truck presence + sustained directional product movement (thresholds in `camera_configurations` collection, tunable without code changes).

**MongoDB connection:** The `MongoConnection` singleton in `app/db/mongo.py` builds the URI from env vars at startup. The `.env` is in the project root; `config.py` reads it with `env_file = "../.env"` (relative to `backend/`). The app never provisions the cluster — indexes are created on startup.

### Module Map

| Module | Responsibility |
|--------|---------------|
| `app/main.py` | FastAPI app, lifespan, router registration |
| `app/config.py` | Pydantic-settings; all config from `../.env` |
| `app/api/` | Thin route handlers (9 modules) — no business logic here |
| `app/core/worker.py` | Per-camera process loop (frame grab → detect → track → count) |
| `app/core/detector.py` | YOLOv11n wrapper (ultralytics) |
| `app/core/tracker.py` | ByteTrack via supervision |
| `app/core/counter.py` | Dual-line crossing + per-track dedup |
| `app/core/activity.py` | Loading/unloading FSM |
| `app/core/zones.py` | Zone & line geometry (normalized 0..1 coords) |
| `app/services/event_bus.py` | Queue → Socket.IO + DB fan-out |
| `app/services/session_service.py` | Session lifecycle |
| `app/db/mongo.py` | Motor async client, `mongo_db` singleton |
| `app/db/models.py` | Pydantic schemas for all 7 collections |
| `app/realtime/socketio_server.py` | Socket.IO server (python-socketio) |
| `app/auth/auth.py` | JWT create/verify, bcrypt password hashing |

### MongoDB Collections

`cameras`, `camera_configurations`, `sessions`, `count_events`, `activity_events`, `system_logs`, `users`

All zone/line geometry is stored normalized 0..1 (relative to frame dimensions).

### API Routes (22 total)

```
POST  /api/auth/login
GET|POST       /api/cameras
GET|PUT        /api/cameras/{id}/config
POST           /api/cameras/{id}/start|stop
POST           /api/uploads
GET            /api/sessions
GET            /api/counts/summary
GET            /api/metrics/camera/{id}
GET            /api/metrics/plant
GET            /api/logs
GET            /api/reports
GET            /stream/{camera_id}.mjpeg
GET            /health
GET            /api/health
```

Socket.IO events: `count_event`, `activity_event`, `session_update`, `camera_status`, `summary_tick`

## Environment

All config lives in `.env` at **project root** (not inside `backend/`). Required vars:

```
MONGO_HOSTS, MONGO_REPLICA_SET, MONGO_DB, MONGO_USER, MONGO_PASSWORD, MONGO_AUTH_SOURCE
JWT_SECRET
```

Optional (have defaults): `DETECT_EVERY_N_FRAMES=5`, `MIN_CONFIDENCE=0.4`, `MAX_CONCURRENT_CAMERAS=2`, `MJPEG_QUALITY=85`, `MJPEG_FRAME_WIDTH=640`

## Current Status

Phase 0 (scaffold) is complete. All modules in `core/`, `services/`, and `api/` are **stubs** — method bodies are `pass`. Phases 1–10 will fill them in. See `IMPLEMENTATION_PLAN.md` for the full roadmap.

When implementing a new phase, wire the logic into `app/main.py`'s lifespan (for startup/shutdown), connect the `EventBus` to the relevant `CameraWorker`, and update the corresponding API router to return real data.
