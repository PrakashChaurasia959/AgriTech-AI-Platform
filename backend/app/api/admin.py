"""Admin API routes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timezone
from app.core.deps import get_current_admin
from app.core.database import get_db
from bson import ObjectId

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/dashboard")
async def admin_dashboard(admin=Depends(get_current_admin)):
    """Get admin dashboard statistics."""
    db = get_db()

    total_users = await db.users.count_documents({"role": "user"})
    total_admins = await db.users.count_documents({"role": "admin"})
    total_disease = await db.disease_predictions.count_documents({})
    total_crop = await db.crop_recommendations.count_documents({})
    total_yield = await db.yield_predictions.count_documents({})
    total_activities = await db.user_history.count_documents({})

    # Disease detection stats by crop
    disease_by_crop = []
    pipeline = [
        {"$group": {"_id": "$crop_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    async for doc in db.disease_predictions.aggregate(pipeline):
        disease_by_crop.append({"crop": doc["_id"], "count": doc["count"]})

    # Recent users
    recent_users = []
    cursor = db.users.find({"role": "user"}).sort("created_at", -1).limit(5)
    async for doc in cursor:
        recent_users.append({
            "id": str(doc["_id"]),
            "full_name": doc.get("full_name", ""),
            "email": doc.get("email", ""),
            "created_at": doc.get("created_at"),
        })

    # Recent activities
    recent_activities = []
    cursor = db.user_history.find({}).sort("created_at", -1).limit(10)
    async for doc in cursor:
        user = await db.users.find_one({"_id": doc["user_id"]})
        recent_activities.append({
            "id": str(doc["_id"]),
            "user_name": user.get("full_name", "") if user else "",
            "activity_type": doc.get("activity_type", ""),
            "description": doc.get("description", ""),
            "created_at": doc.get("created_at"),
        })

    return {
        "stats": {
            "total_users": total_users,
            "total_admins": total_admins,
            "total_disease_detections": total_disease,
            "total_crop_recommendations": total_crop,
            "total_yield_predictions": total_yield,
            "total_activities": total_activities,
        },
        "disease_by_crop": disease_by_crop,
        "recent_users": recent_users,
        "recent_activities": recent_activities,
    }


@router.get("/users")
async def admin_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    search: str = Query(""),
    admin=Depends(get_current_admin),
):
    """Get paginated list of all users."""
    db = get_db()
    query = {}
    if search:
        query = {
            "$or": [
                {"full_name": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}},
            ]
        }
    query = {**query, "role": "user"} if not search else query

    total = await db.users.count_documents({"role": "user"})
    skip = (page - 1) * per_page
    cursor = db.users.find({"role": "user"}).sort("created_at", -1).skip(skip).limit(per_page)
    users = []
    async for doc in cursor:
        disease_count = await db.disease_predictions.count_documents({"user_id": doc["_id"]})
        crop_count = await db.crop_recommendations.count_documents({"user_id": doc["_id"]})
        yield_count = await db.yield_predictions.count_documents({"user_id": doc["_id"]})
        users.append({
            "id": str(doc["_id"]),
            "full_name": doc.get("full_name", ""),
            "email": doc.get("email", ""),
            "mobile_number": doc.get("mobile_number", ""),
            "is_active": doc.get("is_active", True),
            "created_at": doc.get("created_at"),
            "activity_count": disease_count + crop_count + yield_count,
        })

    return {
        "items": users,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page if per_page > 0 else 0,
    }


@router.put("/users/{user_id}/status")
async def toggle_user_status(user_id: str, admin=Depends(get_current_admin)):
    """Toggle user active/deactive status."""
    db = get_db()
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    new_status = not user.get("is_active", True)
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"is_active": new_status, "updated_at": datetime.now(timezone.utc)}},
    )
    return {
        "message": f"User {'activated' if new_status else 'deactivated'} successfully",
        "is_active": new_status,
    }
