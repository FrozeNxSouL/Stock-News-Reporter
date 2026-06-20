"""
FastAPI dependencies for authentication: get_current_user, get_optional_user.
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from bson import ObjectId

from database import Database
from auth.utils import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> dict:
    """
    FastAPI dependency: require a valid JWT and return the authenticated user document.

    Raises 401 if the token is missing, invalid, or the user is not found.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(token)
    user_id: Optional[str] = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    try:
        user = await Database.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user identifier",
        )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    user["_id"] = str(user["_id"])
    return user


async def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme),
) -> Optional[dict]:
    """
    FastAPI dependency: return the authenticated user if a valid token is present,
    otherwise return None (does NOT raise 401).
    """
    if not token:
        return None

    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            return None
        user = await Database.users.find_one({"_id": ObjectId(user_id)})
        if user:
            user["_id"] = str(user["_id"])
        return user
    except HTTPException:
        return None
