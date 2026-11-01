"""Authentication service - user registration, login, password reset."""
import logging
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from app.core.database import get_db
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    generate_reset_token,
)
from app.core.config import settings
from app.services.email_service import send_reset_email
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

RESET_TOKEN_EXPIRE_HOURS = 1


async def register_user(full_name: str, email: str, mobile_number: str, password: str) -> dict:
    """Register a new user. Returns user dict on success."""
    db = get_db()
    existing = await db.users.find_one({"email": email.lower()})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )
    user_doc = {
        "full_name": full_name,
        "email": email.lower(),
        "mobile_number": mobile_number,
        "password_hash": get_password_hash(password),
        "role": "user",
        "is_active": True,
        "farm_name": None,
        "location": None,
        "avatar_url": None,
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id
    return user_doc


async def authenticate_user(email: str, password: str) -> dict:
    """Authenticate a user by email and password."""
    db = get_db()
    user = await db.users.find_one({"email": email.lower()})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not verify_password(password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )
    return user


async def create_token_response(user: dict) -> dict:
    """Build a login response with JWT token."""
    token = create_access_token(str(user["_id"]))
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": str(user["_id"]),
        "full_name": user["full_name"],
        "email": user["email"],
        "role": user.get("role", "user"),
    }


async def request_password_reset(email: str) -> dict:
    """Generate a password reset token and send it via email (or return for dev mode)."""
    db = get_db()
    user = await db.users.find_one({"email": email.lower()})
    if not user:
        # Don't reveal whether email exists
        return {"message": "If the email is registered, a reset link has been sent."}

    raw_token = generate_reset_token()
    hashed_token = get_password_hash(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=RESET_TOKEN_EXPIRE_HOURS)

    await db.password_reset_tokens.insert_one(
        {
            "user_id": user["_id"],
            "email": user["email"],
            "token": hashed_token,
            "expires_at": expires_at,
            "used": False,
            "created_at": datetime.now(timezone.utc),
        }
    )

    reset_link = f"/reset-password?token={raw_token}"

    # Try to send email
    email_sent = await send_reset_email(user["email"], user["full_name"], reset_link)

    if email_sent:
        return {"message": "A password reset link has been sent to your email."}
    else:
        # Development mode: return the token/link in the response
        logger.info("DEV MODE: Password reset link generated for %s", user["email"])
        return {
            "message": "Email service not configured. Use the reset link below (development mode).",
            "reset_link": reset_link,
            "reset_token": raw_token,
        }


async def reset_password(token: str, new_password: str) -> dict:
    """Reset a user's password using a valid reset token."""
    db = get_db()
    now = datetime.now(timezone.utc)

    # Find unused, non-expired tokens
    cursor = db.password_reset_tokens.find({"used": False, "expires_at": {"$gt": now}})
    async for token_doc in cursor:
        if verify_password(token, token_doc["token"]):
            # Mark token as used (one-time use)
            await db.password_reset_tokens.update_one(
                {"_id": token_doc["_id"]}, {"$set": {"used": True}}
            )
            # Update user password
            new_hash = get_password_hash(new_password)
            await db.users.update_one(
                {"_id": token_doc["user_id"]},
                {"$set": {"password_hash": new_hash}},
            )
            return {"message": "Password has been reset successfully."}

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid, expired, or already used reset token",
    )


async def get_user_by_id(user_id: str) -> dict | None:
    db = get_db()
    return await db.users.find_one({"_id": ObjectId(user_id)})
