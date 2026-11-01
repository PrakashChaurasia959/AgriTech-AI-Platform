"""User profile API routes."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.deps import get_current_user
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash
from app.schemas.user import UserProfileUpdate
from pydantic import BaseModel

router = APIRouter(prefix="/users", tags=["User Profile"])


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


@router.get("/profile")
async def get_profile(user=Depends(get_current_user)):
    return {
        "id": str(user["_id"]),
        "full_name": user["full_name"],
        "email": user["email"],
        "mobile_number": user.get("mobile_number", ""),
        "role": user.get("role", "user"),
        "farm_name": user.get("farm_name"),
        "location": user.get("location"),
        "avatar_url": user.get("avatar_url"),
        "created_at": user.get("created_at"),
    }


@router.put("/profile")
async def update_profile(data: UserProfileUpdate, user=Depends(get_current_user)):
    db = get_db()
    update_fields = {}
    for field, value in data.model_dump(exclude_unset=True).items():
        if value is not None:
            update_fields[field] = value
    update_fields["updated_at"] = datetime.now(timezone.utc)

    if update_fields:
        await db.users.update_one({"_id": user["_id"]}, {"$set": update_fields})

    updated = await db.users.find_one({"_id": user["_id"]})
    return {
        "id": str(updated["_id"]),
        "full_name": updated["full_name"],
        "email": updated["email"],
        "mobile_number": updated.get("mobile_number", ""),
        "role": updated.get("role", "user"),
        "farm_name": updated.get("farm_name"),
        "location": updated.get("location"),
        "avatar_url": updated.get("avatar_url"),
        "message": "Profile updated successfully",
    }


@router.put("/change-password")
async def change_password(data: PasswordChange, user=Depends(get_current_user)):
    db = get_db()
    if not verify_password(data.current_password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"password_hash": get_password_hash(data.new_password)}},
    )
    return {"message": "Password changed successfully"}
