"""Socket.IO real-time event server."""
from __future__ import annotations

import socketio


sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
sio_app = socketio.ASGIApp(sio)


@sio.event
async def connect(sid, environ):
    print(f"[Socket.IO] client connected: {sid}")
    from app.core.worker_manager import worker_manager
    summary = worker_manager.get_summary()
    cameras = worker_manager.list_cameras()
    sessions = worker_manager.get_active_sessions()
    await sio.emit("initial_state", {
        "summary": summary,
        "cameras": cameras,
        "active_sessions": sessions,
    }, to=sid)


@sio.event
async def disconnect(sid):
    print(f"[Socket.IO] client disconnected: {sid}")


@sio.event
async def subscribe_camera(sid, data):
    """Join a room for camera-specific events."""
    camera_id = data.get("camera_id") if isinstance(data, dict) else data
    if camera_id:
        sio.enter_room(sid, f"cam:{camera_id}")
        await sio.emit("subscribed", {"camera_id": camera_id}, to=sid)


@sio.event
async def unsubscribe_camera(sid, data):
    """Leave a camera-specific room."""
    camera_id = data.get("camera_id") if isinstance(data, dict) else data
    if camera_id:
        sio.leave_room(sid, f"cam:{camera_id}")
