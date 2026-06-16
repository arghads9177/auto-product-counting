# 🚀 Phase 0 Complete — Start Here

Welcome! **Phase 0 (Scaffold) is complete** and the project is ready for development.

## What's Been Done ✅

- ✅ Backend: Python 3.12 + FastAPI with 22 API routes
- ✅ Frontend: Angular 19 + Tailwind CSS
- ✅ Database: MongoDB connection configured (DigitalOcean replica set)
- ✅ Infrastructure: MediaMTX RTSP setup + sample video pipeline
- ✅ Configuration: `.env` with all required settings
- ✅ Documentation: Complete setup guides and implementation plan

## Verify Setup

Run the verification script to confirm everything is working:

```bash
bash verify_phase0.sh
```

Expected output: **✓ Phase 0 Verification PASSED**

## Run Everything (3 Terminals)

### Terminal 1 — Backend API
```bash
cd backend
uv run uvicorn app.main:app --reload --port 8000
```

→ **Backend running at `http://localhost:8000`**  
→ **OpenAPI docs at `http://localhost:8000/docs`**  
→ **All 22 routes ready to implement**

### Terminal 2 — Frontend Dashboard
```bash
cd frontend
ng serve --open
```

→ **Frontend running at `http://localhost:4200`**  
→ **Browser opens automatically**  
→ **Tailwind CSS styling active**

### Terminal 3 — MediaMTX (optional, for testing)
```bash
mediamtx mediamtx/mediamtx.yml
```

→ **RTSP server at `rtsp://localhost:8554/`**  
→ **HLS at `http://localhost:8888/`**  
→ **WebRTC at `http://localhost:8889/`**

Then in another terminal, publish sample videos:
```bash
cd mediamtx && ./publish_samples.sh
```

→ **Streams available at:**
- `rtsp://localhost:8554/cam01`
- `rtsp://localhost:8554/cam02`

## Key Files to Review

| File | Purpose |
|------|---------|
| `PHASE_0_SETUP.md` | Detailed setup & troubleshooting |
| `PHASE_0_COMPLETION.md` | What was built (inventory) |
| `IMPLEMENTATION_PLAN.md` | Full roadmap (locked decisions) |
| `.env` | Configuration (git-ignored for security) |
| `backend/app/main.py` | FastAPI entry point |
| `frontend/src/app/` | Angular app structure |
| `mediamtx/mediamtx.yml` | RTSP config |

## Your MongoDB Connection

Your DigitalOcean MongoDB is configured in `.env`:

```
MONGO_HOSTS=rs1.sisx.in:27001,rs2.sisx.in:27001,rs3.sisx.in:27000
MONGO_REPLICA_SET=rssisx
MONGO_DB=videoAnalyticDB
MONGO_USER=viadmin
MONGO_PASSWORD=vi4eO#Ai
```

**Note:** Connection testing happens in Phase 5 when persistence is implemented. For now, the connection string is built but not yet used.

## Next: Phase 1 (Ingestion)

Phase 1 will implement:

1. **RTSP Frame Reader** — Connect to MediaMTX via OpenCV
2. **File Upload Handler** — Accept `.mp4` files, stream frames
3. **CPU Benchmark** — Measure fps/camera on your hardware
4. **Frame Skip Logic** — Keep dashboard latency ≤ 2s
5. **Integration Test** — Known clip → verify frame reads

**Estimated effort:** 1-2 days  
**Exit criteria:** Can read frames from RTSP & files, measured CPU throughput documented

---

## Architecture Overview

```
┌────────────────────────────────────────────────────────────┐
│           Angular Dashboard (localhost:4200)               │
│       (Tailwind CSS, real-time updates, charts)            │
└────────────────┬─────────────────────────────────────────┘
                 │ Socket.IO / HTTP
┌────────────────▼─────────────────────────────────────────┐
│         FastAPI Backend (localhost:8000)                  │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ Camera Workers (per-process, per-camera)            │  │
│  │  Frame grab → YOLOv11 → ByteTrack → Count           │  │
│  └─────────────────────────────────────────────────────┘  │
│  ┌──────────────────────┬──────────────────────────────┐  │
│  │ MongoDB (DO replica  │ MediaMTX RTSP/HLS/WebRTC     │  │
│  │ set, external)       │ (localhost:8554)             │  │
│  └──────────────────────┴──────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

## FAQ

**Q: Do I need to install MediaMTX?**  
A: Optional for Phase 0. Required for testing in Phase 1+. Download from: https://github.com/bluenviron/mediamtx/releases

**Q: Where do I add sample videos?**  
A: Place `.mp4` files in `samples/` directory. Then run `mediamtx/publish_samples.sh` to stream them via RTSP.

**Q: Is my MongoDB already set up?**  
A: Yes, you provided the connection details. Phase 5 will test & use it.

**Q: Can I run on Windows?**  
A: Backend & frontend yes (uv + npm are cross-platform). MediaMTX native binary available for Windows. Some scripts may need adjustment.

**Q: How do I deploy this?**  
A: Containerization (Docker/Kubernetes) is outside Phase 0-10 scope. That's a future step after the POC validates the approach.

---

## Support

- **Issues with setup?** → See `PHASE_0_SETUP.md` Troubleshooting section
- **Want to understand the plan?** → Read `IMPLEMENTATION_PLAN.md` (sections 0, 1)
- **Need API details?** → Open `http://localhost:8000/docs` (interactive)
- **Questions on architecture?** → See `IMPLEMENTATION_PLAN.md` §1 (Architecture)

---

## Ready?

```bash
# Verify everything is set up
bash verify_phase0.sh

# Then pick a terminal and start:
cd backend && uv run uvicorn app.main:app --reload --port 8000
# or
cd frontend && ng serve --open
# or
mediamtx mediamtx/mediamtx.yml
```

**Phase 0 complete. Good luck with Phase 1! 🚀**

---

*Last updated: 2026-06-16*  
*Status: Ready for Phase 1 (Ingestion)*
