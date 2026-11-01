"""Disease detection service - handles prediction and history persistence."""
import logging
from datetime import datetime, timezone
from bson import ObjectId
from app.core.database import get_db
from app.ml.disease_model import classify_disease, DISEASE_DATABASE

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def validate_image_file(filename: str, file_size: int) -> str | None:
    """Validate uploaded image. Returns error message or None if valid."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        return f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
    if file_size > MAX_FILE_SIZE:
        return "File too large. Maximum size is 10 MB."
    return None


async def predict_disease(image_bytes: bytes, crop_type: str, user_id: str) -> dict:
    """Run disease detection and save result to database."""
    result = classify_disease(image_bytes, crop_type)

    db = get_db()
    prediction_doc = {
        "user_id": ObjectId(user_id),
        "crop_type": result["crop"],
        "disease_name": result["disease_name"],
        "disease_key": result["disease_key"],
        "confidence": result["confidence"],
        "is_healthy": result["is_healthy"],
        "is_demo_mode": result["is_demo_mode"],
        "symptoms": result["symptoms"],
        "causes": result["causes"],
        "treatment": result["treatment"],
        "prevention": result["prevention"],
        "image_size": len(image_bytes),
        "created_at": datetime.now(timezone.utc),
    }
    insert_result = await db.disease_predictions.insert_one(prediction_doc)

    # Also add to user history
    await db.user_history.insert_one({
        "user_id": ObjectId(user_id),
        "activity_type": "disease_detection",
        "description": f"Disease scan: {result['crop']} - {result['disease_name']} ({result['confidence']*100:.1f}% confidence)",
        "record_id": insert_result.inserted_id,
        "created_at": datetime.now(timezone.utc),
    })

    return {
        "disease_name": result["disease_name"],
        "confidence": result["confidence"],
        "is_healthy": result["is_healthy"],
        "crop_type": result["crop"],
        "symptoms": result["symptoms"],
        "causes": result["causes"],
        "treatment": result["treatment"],
        "prevention": result["prevention"],
        "prediction_id": str(insert_result.inserted_id),
        "is_demo_mode": result["is_demo_mode"],
        "created_at": prediction_doc["created_at"],
    }


async def get_disease_history(user_id: str, page: int = 1, per_page: int = 10,
                               search: str = "") -> dict:
    """Get paginated disease prediction history for a user."""
    db = get_db()
    query = {"user_id": ObjectId(user_id)}
    if search:
        query["disease_name"] = {"$regex": search, "$options": "i"}

    total = await db.disease_predictions.count_documents(query)
    skip = (page - 1) * per_page
    cursor = db.disease_predictions.find(query).sort("created_at", -1).skip(skip).limit(per_page)
    items = []
    async for doc in cursor:
        items.append({
            "id": str(doc["_id"]),
            "crop_type": doc.get("crop_type", ""),
            "disease_name": doc.get("disease_name", ""),
            "confidence": doc.get("confidence", 0),
            "is_healthy": doc.get("is_healthy", False),
            "is_demo_mode": doc.get("is_demo_mode", True),
            "created_at": doc.get("created_at"),
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page if per_page > 0 else 0,
    }


async def get_disease_prediction_detail(prediction_id: str, user_id: str) -> dict | None:
    """Get a single disease prediction record."""
    db = get_db()
    doc = await db.disease_predictions.find_one({
        "_id": ObjectId(prediction_id),
        "user_id": ObjectId(user_id),
    })
    if not doc:
        return None
    return {
        "id": str(doc["_id"]),
        "crop_type": doc.get("crop_type", ""),
        "disease_name": doc.get("disease_name", ""),
        "disease_key": doc.get("disease_key", ""),
        "confidence": doc.get("confidence", 0),
        "is_healthy": doc.get("is_healthy", False),
        "is_demo_mode": doc.get("is_demo_mode", True),
        "symptoms": doc.get("symptoms", []),
        "causes": doc.get("causes", []),
        "treatment": doc.get("treatment", []),
        "prevention": doc.get("prevention", []),
        "created_at": doc.get("created_at"),
    }


async def delete_disease_prediction(prediction_id: str, user_id: str) -> bool:
    """Delete a disease prediction record."""
    db = get_db()
    result = await db.disease_predictions.delete_one({
        "_id": ObjectId(prediction_id),
        "user_id": ObjectId(user_id),
    })
    if result.deleted_count > 0:
        await db.user_history.delete_many({
            "record_id": ObjectId(prediction_id),
            "user_id": ObjectId(user_id),
        })
        return True
    return False
