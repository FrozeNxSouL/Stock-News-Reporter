"""
Authentication routes: register, login, refresh, profile.
"""
import logging
import traceback
from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, timezone
from bson import ObjectId

from database import Database
from models.user import (
    UserSignup,
    UserLogin,
    TokenResponse,
    RefreshRequest,
    UserProfileUpdate,
    UserResponse,
)
from auth.utils import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from auth.dependencies import get_current_user

logger = logging.getLogger("auth")

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/signup", response_model=TokenResponse, status_code=201)
async def signup(body: UserSignup):
    """
    Register a new user account.

    Returns access + refresh tokens on success.
    """
    db = Database.users

    # Check for existing email
    existing = await db.find_one({"email": body.email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    # Check for existing username
    existing_user = await db.find_one({"username": body.username})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This username is already taken",
        )

    now = datetime.now(timezone.utc)

    try:
        hashed = hash_password(body.password)
    except Exception as e:
        logger.error(f"Password hashing failed: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process password. Please try again.",
        )

    user_doc = {
        "email": body.email,
        "username": body.username,
        "hashed_password": hashed,
        "watchlist": [],
        "pinned": [],
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }

    try:
        result = await db.insert_one(user_doc)
    except Exception as e:
        logger.error(f"Database insert failed: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create account. Please try again.",
        )

    user_id = str(result.inserted_id)

    # Issue tokens
    token_data = {"sub": user_id, "email": body.email, "username": body.username}
    try:
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
    except Exception as e:
        logger.error(f"Token creation failed: {e}\n{traceback.format_exc()}")
        # Clean up: delete the user we just created since token issuance failed
        await db.delete_one({"_id": result.inserted_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Account created but session could not be started. Please try logging in.",
        )

    logger.info(f"New user registered: {body.username} ({body.email})")
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin):
    """
    Authenticate with email + password.

    Returns access + refresh tokens on success.
    """
    db = Database.users

    try:
        user = await db.find_one({"email": body.email})
    except Exception as e:
        logger.error(f"Database query failed during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Service temporarily unavailable. Please try again.",
        )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    try:
        pw_ok = verify_password(body.password, user["hashed_password"])
    except Exception as e:
        logger.error(f"Password verification failed: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed. Please try again.",
        )

    if not pw_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    user_id = str(user["_id"])
    token_data = {
        "sub": user_id,
        "email": user["email"],
        "username": user["username"],
    }
    try:
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
    except Exception as e:
        logger.error(f"Token creation during login failed: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again.",
        )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest):
    """
    Exchange a valid refresh token for a new access + refresh token pair.
    """
    payload = decode_token(body.refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is not a refresh token",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    # Verify user still exists
    try:
        user = await Database.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user")

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    if not user.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account deactivated")

    token_data = {
        "sub": user_id,
        "email": user["email"],
        "username": user["username"],
    }
    access_token = create_access_token(token_data)
    refresh_token_new = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_new,
    )


@router.get("/me", response_model=UserResponse)
async def get_profile(current_user: dict = Depends(get_current_user)):
    """
    Get the authenticated user's profile.
    """
    return UserResponse(
        _id=current_user["_id"],
        email=current_user["email"],
        username=current_user["username"],
        watchlist=current_user.get("watchlist", []),
        pinned=current_user.get("pinned", []),
        created_at=current_user["created_at"],
        updated_at=current_user["updated_at"],
    )


@router.patch("/me", response_model=UserResponse)
async def update_profile(
    body: UserProfileUpdate,
    current_user: dict = Depends(get_current_user),
):
    """
    Update the authenticated user's profile (username, watchlist).
    """
    db = Database.users
    updates = {}
    update_set = {}

    if body.username is not None:
        # Check uniqueness
        existing = await db.find_one({
            "username": body.username,
            "_id": {"$ne": ObjectId(current_user["_id"])},
        })
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This username is already taken",
            )
        update_set["username"] = body.username

    if body.watchlist is not None:
        # Normalize tickers to uppercase
        update_set["watchlist"] = [t.upper().strip() for t in body.watchlist if t.strip()]

    if body.pinned is not None:
        # Only keep pinned tickers that exist in user's watchlist
        current_wl = update_set.get("watchlist") or current_user.get("watchlist", [])
        update_set["pinned"] = [t.upper().strip() for t in body.pinned if t.strip().upper() in current_wl]

    if update_set:
        update_set["updated_at"] = datetime.now(timezone.utc)
        updates["$set"] = update_set
        await db.update_one(
            {"_id": ObjectId(current_user["_id"])},
            updates,
        )

    # Re-fetch updated user
    user = await db.find_one({"_id": ObjectId(current_user["_id"])})
    user["_id"] = str(user["_id"])

    return UserResponse(
        _id=user["_id"],
        email=user["email"],
        username=user.get("username", current_user.get("username", "")),
        watchlist=user.get("watchlist", []),
        pinned=user.get("pinned", []),
        created_at=user["created_at"],
        updated_at=user.get("updated_at", datetime.now(timezone.utc)),
    )
