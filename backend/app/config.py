from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # FastAPI
    APP_NAME: str = "Auto Product Counting"
    DEBUG: bool = False

    # MongoDB
    MONGO_HOSTS: str
    MONGO_REPLICA_SET: str
    MONGO_DB: str
    MONGO_USER: str
    MONGO_PASSWORD: str
    MONGO_AUTH_SOURCE: str

    # JWT
    JWT_SECRET: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # MediaMTX
    MEDIAMTX_BASE_URL: str = "http://localhost:8554"

    # Video
    DETECT_EVERY_N_FRAMES: int = 5
    MIN_CONFIDENCE: float = 0.4
    FRAME_SKIP_THRESHOLD: int = 3

    # Performance
    MAX_CONCURRENT_CAMERAS: int = 2

    # Streaming
    MJPEG_QUALITY: int = 85
    MJPEG_FRAME_WIDTH: int = 640

    # Storage
    UPLOADS_DIR: str = "uploads"

    class Config:
        env_file = "../.env"
        env_file_encoding = "utf-8"


settings = Settings()
