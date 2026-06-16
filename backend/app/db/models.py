"""Pydantic models for MongoDB documents."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class Camera(BaseModel):
    """Camera document."""

    camera_id: str
    name: str
    rtsp_url: Optional[str] = None
    source_file: Optional[str] = None
    status: str = "OFFLINE"
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CameraConfiguration(BaseModel):
    """Camera configuration document."""

    camera_id: str
    zones: Dict[str, List[List[float]]] = Field(default_factory=dict)
    lines: Dict[str, List[List[float]]] = Field(default_factory=dict)
    direction_map: Dict[str, str] = Field(default_factory=dict)
    thresholds: Dict[str, Any] = Field(
        default_factory=lambda: {
            "activity_start_sec": 10,
            "session_idle_end_sec": 300,
            "min_confidence": 0.4,
        }
    )
    version: int = 1
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Session(BaseModel):
    """Session document."""

    session_id: str
    camera_id: str
    type: str  # LOADING or UNLOADING
    status: str  # ACTIVE or COMPLETED
    start_time: datetime
    end_time: Optional[datetime] = None
    count: int = 0
    created_by_rule: Optional[str] = None


class CountEvent(BaseModel):
    """Count event document."""

    event_id: str
    camera_id: str
    session_id: str
    track_id: int
    direction: str  # LOADING or UNLOADING
    timestamp: datetime


class ActivityEvent(BaseModel):
    """Activity event document."""

    camera_id: str
    session_id: Optional[str] = None
    kind: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime


class SystemLog(BaseModel):
    """System/AI log document."""

    category: str  # SYSTEM or AI
    type: str
    severity: str  # INFO, WARN, ERROR
    camera_id: Optional[str] = None
    session_id: Optional[str] = None
    message: str
    timestamp: datetime


class User(BaseModel):
    """User document."""

    username: str
    password_hash: str
    role: str  # ADMIN, SUPERVISOR, OPERATOR
