# Auto Product Counting

AI-based automatic product loading/unloading monitoring system using YOLOv11 + ByteTrack.

## Quick Start (Phase 0 Complete ✅)

### Backend
```bash
cd backend && uv run uvicorn app.main:app --reload --port 8000
```
→ `http://localhost:8000` | Docs: `/docs`

### Frontend
```bash
cd frontend && ng serve --open
```
→ `http://localhost:4200`

### MediaMTX (optional, for RTSP simulation)
```bash
mediamtx mediamtx/mediamtx.yml
```
→ `rtsp://localhost:8554/cam01`

## Documentation

- **[PHASE_0_SETUP.md](PHASE_0_SETUP.md)** — Installation & troubleshooting guide
- **[PHASE_0_COMPLETION.md](PHASE_0_COMPLETION.md)** — What was built in Phase 0
- **[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)** — Full roadmap (locked decisions)
- **[project_spec.md](project_spec.md)** — Original requirements

## Architecture

**Backend:** Python 3.12 + FastAPI (YOLOv11, ByteTrack, MongoDB)  
**Frontend:** Angular 19 + Tailwind CSS  
**Database:** DigitalOcean MongoDB replica set  
**Video:** Native MediaMTX for RTSP + .mp4 upload  
**Detection:** YOLOv11n (nano) on CPU  

## Project Status

| Phase | Task | Status |
|-------|------|--------|
| 0 | Scaffold (Python/Angular/MongoDB/MediaMTX setup) | ✅ Complete |
| 1 | Ingestion (RTSP + file upload, CPU benchmark) | ⏳ Next |
| 2 | Detect+Track (YOLOv11 + ByteTrack + MJPEG) | 📋 Planned |
| 3 | Counting (Dual-line counter + dedup) | 📋 Planned |
| 4 | Activity FSM (Loading/unloading detection) | 📋 Planned |
| 5 | Persistence (MongoDB + indexes) | 📋 Planned |
| 6 | Realtime API (REST + Socket.IO) | 📋 Planned |
| 7 | Dashboard (Angular + Tailwind screens) | 📋 Planned |
| 8 | Auth (JWT + 3 roles) | 📋 Planned |
| 9 | Reports (CSV/Excel/PDF) | 📋 Planned |
| 10 | Hardening (Concurrency tuning, validation) | 📋 Planned |

## Structure

```
auto-product-counting/
├── backend/          # Python 3.12 + FastAPI
├── frontend/         # Angular 19 + Tailwind
├── mediamtx/         # RTSP streaming config
├── samples/          # Test .mp4 files (user-provided)
├── .env              # Configuration (git-ignored)
└── docs/             # Setup guides
```

## Requirements

- Python 3.12+
- Node.js 18+, npm
- MongoDB (DigitalOcean managed replica set)
- MediaMTX binary (optional, for testing)
