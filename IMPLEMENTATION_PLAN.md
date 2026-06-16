# Implementation Plan — Auto Product Counting (POC/MVP)
### YOLOv11 + ByteTrack Loading/Unloading Monitoring System

> Companion to [`project_spec.md`](./project_spec.md). This document is the build plan; the spec is the requirements source of truth.

---

## 0. Decisions & Constraints (locked for the POC)

These were confirmed before planning and drive every choice below:

| Topic | Decision |
|---|---|
| **Backend stack** | **Python + FastAPI** consolidates Video Processing + Event Processing + API. (Node.js/Express/TypeScript event service from the spec is dropped to reduce moving parts.) |
| **Python tooling** | **`uv`** initializes the project and manages the virtual environment, pinned to **Python 3.12+**. |
| **Frontend** | **Angular** + **Tailwind CSS** (for a highly professional look & feel) + RxJS + Socket.IO client + Chart.js. |
| **Database** | **MongoDB** running on a **DigitalOcean managed replica set** — *external, not containerized*. Connection details (URI/credentials) supplied by the user via `.env`. |
| **Video input** | No real CCTV. **Simulate RTSP with MediaMTX run natively (standalone binary, not Docker)** — loop sample clips to `rtsp://...`. Also support **`.mp4` upload** for testing. |
| **Hardware** | **CPU only** → YOLOv11**n** (nano) baseline, aggressive frame-skipping, per-camera worker processes. |
| **Detection** | **Pretrained YOLOv11 (COCO)** first — map `person`/`truck` to spec entities. Custom training is a *contingency phase*, not a baseline milestone. |

**Open items to confirm** (see §13): realistic concurrent-camera target on CPU, whether "forklift" must be a custom class from day one (COCO has no forklift), and source of sample loading/unloading clips.

---

## 1. Architecture (as adapted for the POC)

```text
   MediaMTX (native binary on host, NOT Docker)
   - ffmpeg loops sample .mp4 → rtsp://localhost:8554/camNN
   - also accepts pushed streams
                  │ RTSP / uploaded .mp4 file
                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│  FastAPI Backend (Python 3.12 via uv, CPU)                             │
│                                                                        │
│  ┌────────────────────────┐   one OS process per camera               │
│  │ Camera Worker (×N)      │   (multiprocessing)                       │
│  │  Frame grab (OpenCV)    │                                           │
│  │  → YOLOv11n detect      │                                           │
│  │  → ByteTrack (supervision)                                          │
│  │  → Activity/Session FSM │                                           │
│  │  → Dual-line counting   │                                           │
│  │  → Annotated MJPEG out  │                                           │
│  └────────┬───────────────┘                                           │
│           │ events (count / activity / session / log)                  │
│           ▼  via multiprocessing Queue                                 │
│  ┌────────────────────────┐   ┌───────────────────────────────┐       │
│  │ Event Service           │   │ REST API + Socket.IO server   │       │
│  │  Session mgmt           │──▶│  /api/* config & reports      │       │
│  │  Aggregation / metrics  │   │  /ws live counts & events     │       │
│  │  Persistence            │   │  /stream/{cam}.mjpeg          │       │
│  └────────┬───────────────┘   └───────────────┬───────────────┘       │
└───────────┼───────────────────────────────────┼───────────────────────┘
            ▼                                   ▼
  ┌──────────────────────────┐         ┌──────────────────┐
  │  MongoDB                  │         │ Angular Dashboard │
  │  (DigitalOcean managed    │         │ (Tailwind/Chart)  │
  │   replica set, external)  │         └──────────────────┘
  └──────────────────────────┘
```

**Why one process per camera:** CPU-only YOLO is the bottleneck. Python's GIL makes threads insufficient for parallel inference, so each camera runs in its own process. The main FastAPI process owns the API, Socket.IO, and DB writes; workers communicate results back over `multiprocessing.Queue`.

**Live video in the dashboard:** the backend serves an **annotated MJPEG** stream per camera (boxes, track IDs, counting lines, live count overlay) via `StreamingResponse`. MJPEG is the simplest browser-native option and avoids WebRTC complexity for the POC. (MediaMTX HLS/WebRTC remains available later for raw, low-latency views.)

---

## 2. Repository Structure

```text
auto-product-counting/
├── .env.example                  # Mongo URI (DO replica set), JWT secret, paths
├── mediamtx/
│   ├── mediamtx.yml              # stream paths, RTSP config (native run)
│   ├── run_mediamtx.sh           # start native MediaMTX binary
│   └── publish_samples.sh        # ffmpeg loop sample.mp4 → RTSP
├── samples/                      # test .mp4 clips (gitignored if large)
├── backend/
│   ├── pyproject.toml            # uv-managed, requires-python = ">=3.12"
│   ├── uv.lock
│   ├── .python-version           # 3.12
│   ├── app/
│   │   ├── main.py               # FastAPI app, lifespan, router mount
│   │   ├── config.py             # settings (pydantic-settings, reads .env)
│   │   ├── api/                  # routers: cameras, sessions, counts,
│   │   │                          #          reports, logs, auth, streams
│   │   ├── core/
│   │   │   ├── detector.py       # YOLOv11 wrapper (ultralytics)
│   │   │   ├── tracker.py        # ByteTrack via supervision
│   │   │   ├── counter.py        # dual-line counting + dedup
│   │   │   ├── activity.py       # loading/unloading detection FSM
│   │   │   ├── zones.py          # zone & line geometry
│   │   │   └── worker.py         # per-camera process loop
│   │   ├── services/
│   │   │   ├── session_service.py
│   │   │   ├── metrics_service.py
│   │   │   ├── event_bus.py      # Queue → Socket.IO + DB fan-out
│   │   │   └── report_service.py # CSV/Excel/PDF
│   │   ├── db/
│   │   │   ├── mongo.py          # motor client → DO replica set
│   │   │   └── models.py         # pydantic schemas / indexes
│   │   ├── realtime/
│   │   │   └── socketio_server.py
│   │   └── auth/                 # JWT, roles
│   └── tests/
└── frontend/
    ├── package.json
    ├── tailwind.config.js
    ├── postcss.config.js
    └── src/app/
        ├── core/                 # api & socket services, auth guard
        ├── features/
        │   ├── dashboard/        # summary + camera grid
        │   ├── sessions/
        │   ├── metrics/
        │   ├── timeline/
        │   ├── logs/
        │   ├── reports/
        │   └── admin/            # camera config, users
        └── shared/               # Tailwind UI components (cards, tables, badges)
```

---

## 3. Data Model (MongoDB — DigitalOcean managed replica set)

Connection is via the user-supplied `MONGODB_URI` (replica-set connection string, TLS) in `.env`. The app creates indexes on startup but does **not** provision the cluster. Collections per spec; key shapes:

```jsonc
// cameras
{ "_id", "camera_id": "CAM01", "name", "rtsp_url" | "source_file",
  "status": "ONLINE|OFFLINE|BUFFERING|PROCESSING|ERROR",
  "enabled": true, "created_at" }

// camera_configurations  (one active config per camera; geometry normalized 0..1)
{ "camera_id": "CAM01",
  "zones": { "truck": [[x,y]...], "loading_area": [...], "buffer": [...] },
  "lines": { "A": [[x1,y1],[x2,y2]], "B": [[x1,y1],[x2,y2]] },
  "direction_map": { "loading": "A->B", "unloading": "B->A" },
  "thresholds": { "activity_start_sec": 10, "session_idle_end_sec": 300,
                  "min_confidence": 0.4 },
  "version": 1, "updated_at" }

// sessions
{ "session_id": "LOAD_20260616_001", "camera_id",
  "type": "LOADING|UNLOADING", "status": "ACTIVE|COMPLETED",
  "start_time", "end_time", "count": 245, "created_by_rule" }

// count_events
{ "event_id", "camera_id", "session_id", "track_id": 101,
  "direction": "LOADING|UNLOADING", "timestamp" }

// activity_events  (FSM transitions: truck_detected, forklift_active, session_start/end…)
{ "camera_id", "session_id", "kind", "payload", "timestamp" }

// system_logs / ai_logs (single collection w/ category + severity)
{ "category": "SYSTEM|AI", "type", "severity": "INFO|WARN|ERROR",
  "camera_id", "session_id", "message", "timestamp" }

// users
{ "username", "password_hash", "role": "ADMIN|SUPERVISOR|OPERATOR" }
```

**Indexes:** `count_events(camera_id, timestamp)`, `sessions(camera_id, status)`, `count_events(session_id, track_id)` unique-ish for dedup, `system_logs(timestamp, category)`. Use `motor` (async) with the replica-set URI and `readPreference`/write-concern defaults appropriate for the managed cluster.

---

## 4. Core Algorithms

### 4.1 Detection → Tracking
- **Detector:** `ultralytics` YOLOv11n on CPU. Inference on resized frames (e.g. 640px), every Nth frame (configurable `detect_every_n`), confidence ≥ `min_confidence`.
- **Class mapping:** COCO `person`→Worker, `truck`/`bus`→Truck, generic boxes in buffer/loading zone→Product candidate. **Forklift has no COCO class** → flagged as a likely custom-training trigger (§9).
- **Tracking:** `supervision.ByteTrack` consumes detections, yields stable `tracker_id` across frames.

### 4.2 Dual-Line Counting (deterministic)
- Two virtual lines **A** and **B** (`supervision.LineZone`).
- For each `track_id`, record the **ordered sequence** of line crossings.
- **Loading:** crossed A then B (A→B) ⇒ `+1 loading`. **Unloading:** B→A ⇒ `+1 unloading` (separate tally).
- **Dedup:** maintain `{track_id: counted}` per session; a track counts **once**. Persisted in `count_events` keyed by `(session_id, track_id)`.
- Dual lines reject pauses/reversals/oscillation (single-line failure modes called out in spec §5).

### 4.3 Activity / Session Detection FSM
State machine per camera:

```text
IDLE
  └─(truck present AND forklift/worker active AND sustained directional
     product movement ≥ activity_start_sec)─▶ ACTIVE(type=LOADING|UNLOADING)
ACTIVE
  ├─ count products via dual-line logic
  └─(no product movement AND no forklift activity for session_idle_end_sec)
        ─▶ COMPLETED  (persist session, reset to IDLE)
```

- **Direction of movement** derived from tracked-object centroid trajectories relative to truck zone (toward truck = loading; away = unloading).
- Thresholds (`activity_start_sec=10`, `session_idle_end_sec=300`) come from `camera_configurations` so they're tunable without code changes.

### 4.4 CPU Performance Strategy
- YOLOv11n + 640px input + `detect_every_n` frames (tracker interpolates between).
- Per-camera process; cap concurrent cameras based on measured throughput (validate in Phase 1/10).
- Drop-to-latest frame policy (never queue stale frames) to keep dashboard latency ≤ 2s.
- Optional ONNX/OpenVINO export of YOLOv11n for CPU speedup (stretch).

---

## 5. API Surface (FastAPI)

```text
Auth
  POST /api/auth/login                 → JWT
REST
  GET    /api/cameras                  list + live status
  POST   /api/cameras                  (admin) add camera
  GET/PUT /api/cameras/{id}/config     zones, lines, thresholds
  POST   /api/cameras/{id}/start|stop  control worker
  POST   /api/uploads                  upload .mp4 → registers as a source
  GET    /api/sessions?status=&camera= active/historical
  GET    /api/counts/summary           top-summary tiles
  GET    /api/metrics/camera/{id}      per-camera metrics
  GET    /api/metrics/plant            plant-level + shift/hourly
  GET    /api/logs?filters…            system+AI logs w/ search
  GET    /api/reports?range=&format=   CSV | Excel | PDF
Streaming
  GET    /stream/{camera_id}.mjpeg     annotated live MJPEG
Realtime (Socket.IO)
  ws events: count_event, activity_event, session_update,
             camera_status, summary_tick
```

---

## 6. Frontend (Angular + Tailwind CSS) — screens mapped to spec §6

Tailwind provides the design system (utility classes + a small set of shared components in `shared/`: cards, status badges, data tables, stat tiles) for a clean, professional, responsive dashboard. Chart.js for visualizations; Socket.IO client for live updates.

1. **Top Summary** — stat tiles: online cameras, active/loading/unloading sessions, today's count, system health (Socket.IO `summary_tick`).
2. **Live Camera Grid** — responsive Tailwind grid; card per camera: MJPEG `<img>`, name, color-coded status badge (ONLINE/OFFLINE/BUFFERING/PROCESSING/ERROR), session type, current count, last-activity; controls (fullscreen, snapshot, refresh/reconnect, pause). *(Audio mute/unmute is a stub — RTSP samples are video-only; N/A for POC.)*
3. **Session Monitoring Panel** — Tailwind data table of active sessions.
4. **Count Metrics Panel** — per-camera + plant-level Chart.js (hourly trend, camera distribution, shift-wise).
5. **Event Timeline** — live feed of events.
6. **Logs Module** — system + AI logs with date/camera/session/type/severity filters.
7. **Historical Reports** — daily/weekly/monthly/custom + CSV/Excel/PDF export.
8. **Auth & Roles** — route guards for Admin / Supervisor / Operator.

---

## 7. Infrastructure & Runtime

No single docker-compose owns everything; components run as follows:

- **MediaMTX** — **native binary on the host** (not Docker). `mediamtx/run_mediamtx.sh` starts it; `publish_samples.sh` uses `ffmpeg -re -stream_loop -1 -i samples/clip.mp4 -c copy -f rtsp rtsp://localhost:8554/cam01` to fake a live CCTV feed.
- **MongoDB** — **external DigitalOcean managed replica set**, reached via `MONGODB_URI` in `.env`. Not provisioned or run locally.
- **Backend** — Python project initialized and run with **`uv`**:
  - `uv init` / `uv venv --python 3.12` → `requires-python = ">=3.12"` in `pyproject.toml`.
  - `uv add fastapi uvicorn ultralytics supervision opencv-python motor python-socketio pydantic-settings python-jose passlib openpyxl reportlab …`
  - Run: `uv run uvicorn app.main:app --reload`.
- **Frontend** — Angular + Tailwind via npm (`ng serve` in dev). Tailwind wired through `tailwind.config.js` + PostCSS, imported in global styles.
- **`.env`** holds: `MONGODB_URI`, `JWT_SECRET`, MediaMTX base URL, sample paths.

(Containerizing backend/frontend for deployment is a later, optional step; the POC runs them directly.)

---

## 8. Build Phases & Milestones

| Phase | Goal | Exit criteria |
|---|---|---|
| **P0 — Scaffold** | `uv`-initialized backend (Python 3.12 venv), Angular+Tailwind skeleton, `.env` wiring, connect to DO MongoDB, native MediaMTX setup, health endpoints | `uv run` backend + `ng serve` frontend both up; backend connects to DO replica set; MediaMTX serving a looped sample over RTSP |
| **P1 — Ingestion** | RTSP read from native MediaMTX + `.mp4` upload; frame-reader abstraction; **CPU throughput benchmark** | Frames read from RTSP and uploaded file; documented fps/camera on target CPU |
| **P2 — Detect+Track** | YOLOv11n + supervision ByteTrack; annotated MJPEG endpoint | Live MJPEG shows boxes + stable track IDs in browser |
| **P3 — Counting** | Dual-line counter + per-track dedup + `count_events` | Known clip counts within ±2% of manual count |
| **P4 — Activity FSM** | Zone config + loading/unloading start/end detection | Sessions auto-open/close correctly on test clips |
| **P5 — Persistence+Events** | Mongo models/indexes on DO cluster; session/metrics services; event bus | All event types persisted; metrics queries return |
| **P6 — Realtime API** | REST + Socket.IO; summary/metrics/logs/sessions endpoints | Dashboard data flows live, latency ≤ 2s |
| **P7 — Dashboard** | All Angular+Tailwind screens (§6) | Full monitoring UX working end-to-end |
| **P8 — Auth/Roles** | JWT + 3 roles + guards | Role-gated access verified |
| **P9 — Reports** | CSV/Excel/PDF export, date ranges | Reports download in all 3 formats |
| **P10 — Hardening** | Multi-camera concurrency tuning, reconnection, success-criteria validation | §11 metrics measured & documented |

---

## 9. Detection Contingency (custom training)

Triggered only if pretrained accuracy < spec thresholds (esp. **forklift**, which COCO lacks, and "product" boxes):
1. Collect/annotate frames (Roboflow/CVAT) for `product, forklift, worker, truck`.
2. Fine-tune YOLOv11n/s.
3. Swap weights via config — no pipeline code change. Budget this as a separate workstream.

---

## 10. Testing Strategy

- **Unit:** counting dedup, line-crossing direction, FSM transitions (deterministic, no model needed — feed synthetic track sequences).
- **Integration:** known sample clip → asserted count & session lifecycle.
- **Accuracy harness:** manually-labeled clips → detection/tracking/counting accuracy vs §11.
- **Load:** N simulated MediaMTX cameras → measure max concurrent streams + dashboard latency on CPU.

---

## 11. MVP Success Criteria (from spec §831) — how we validate each

| Criterion | Target | Validation |
|---|---|---|
| Detection accuracy | ≥ 95% | Labeled-clip harness (P10) |
| Tracking stability | ≥ 95% | ID-switch rate on clips |
| Counting accuracy | ≥ 98% | Manual vs system count |
| Dashboard latency | ≤ 2s | Timestamp event→render |
| Auto session detection | ≥ 90% | FSM vs annotated start/end |
| Multi-camera concurrency | Supported | Load test (P1 baseline, P10 final) |

> **CPU-only risk:** hitting ≥95% detection *and* multi-camera concurrency simultaneously on CPU is the principal risk. P1's benchmark will set a realistic camera count; if accuracy needs a larger model, concurrency drops. This trade-off is surfaced early, not at the end.

---

## 12. Key Risks

1. **CPU throughput** vs accuracy + concurrency (mitigation: YOLOv11n, frame-skip, ONNX/OpenVINO, document realistic N).
2. **Forklift not in COCO** → may force custom training (Phase 9).
3. **"Product" is ill-defined for a generic detector** → zone-constrained heuristics first, custom class if needed.
4. **MJPEG bandwidth** with many cameras → cap stream resolution/fps for dashboard, full-res only on fullscreen.
5. **Managed-Mongo latency/limits** (network round-trips to DO, connection pool size) → tune `motor` pool, batch writes from the event bus.

---

## 13. Questions to confirm before P0

1. **Target concurrent cameras** for the POC on the available CPU (2? 4? 8?) — sets concurrency design and benchmark goal.
2. **Forklift detection** — acceptable to skip forklift as an explicit class for the first pass (rely on worker+truck+movement), or is forklift mandatory from day one (→ custom training in scope now)?
3. Do you have **sample loading/unloading clips** to drop into `samples/`, or should I source/synthesize stand-ins for early development?
4. **MongoDB connection details** — please supply the DO replica-set `MONGODB_URI` (and whether a dedicated database/user exists for this app) so P0/P5 can wire persistence.
```