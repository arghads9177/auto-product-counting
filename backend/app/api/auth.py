"""Authentication endpoints — login, register, profile."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    require_role,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "OPERATOR"


@router.post("/login")
async def login(body: LoginRequest):
    """Authenticate user and return JWT token."""
    from app.db.mongo import mongo_connection
    db = mongo_connection.db
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    user = await db["users"].find_one({"username": body.username})
    if user is None or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user["username"], user["role"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user["username"],
        "role": user["role"],
    }


@router.post("/register")
async def register(
    body: RegisterRequest,
    _user: dict = Depends(require_role("ADMIN")),
):
    """Register a new user (admin only)."""
    from app.db.mongo import mongo_connection
    db = mongo_connection.db
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    if body.role not in ("ADMIN", "SUPERVISOR", "OPERATOR"):
        raise HTTPException(status_code=400, detail="Invalid role")

    existing = await db["users"].find_one({"username": body.username})
    if existing:
        raise HTTPException(status_code=409, detail="Username already exists")

    await db["users"].insert_one({
        "username": body.username,
        "password_hash": hash_password(body.password),
        "role": body.role,
    })
    return {"username": body.username, "role": body.role}


@router.get("/me")
async def get_profile(user: dict = Depends(get_current_user)):
    """Get current user profile from token."""
    return {"username": user["sub"], "role": user["role"]}
