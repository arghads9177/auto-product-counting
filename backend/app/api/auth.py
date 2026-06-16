"""Authentication endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
async def login(request: LoginRequest):
    """Authenticate user and return JWT token."""
    # Placeholder - implement with real authentication
    return {"access_token": "token_placeholder", "token_type": "bearer"}
