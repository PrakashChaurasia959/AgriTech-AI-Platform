"""Yield prediction service."""
import logging
from datetime import datetime, timezone
from bson import ObjectId
from app.core.database import get_db
from app.ml.yield_model import predictor

logger = logging.getLogger(__name__)


async def predict_yield(data: dict, user_id: str) -> dict:
    """Predict crop yield and save to history."""
    result = predictor.predict(
        crop=data["crop_type"],
        state=data["state"],
        season=data["season"],
        area=data["area"],
        rainfall=data["rainfall"],
        temperature=data["temperature"],
        soil_type=data.get("soil_type", "Loamy"),
        fertilizer=data.get("fertilizer_usage", 0),
    )

    db = get_db()
    prediction_doc = {
        "user_id": ObjectId(user_id),
        "crop_type": data["crop_type"],
        "state": data["state"],
        "season": data["season"],
        "area": data["area"],
        "rainfall": data["rainfall"],
        "temperature": data["temperature"],
        "soil_type": data.get("soil_type", "Loamy"),
        "fertilizer_usage": data.get("fertilizer_usage", 0),
        "predicted_yield": result["predicted_yield"],
        "predicted_production": result["predicted_production"],
        "suitability": result["suitability"],
        "improvement_suggestions": result["improvement_suggestions"],
        "created_at": datetime.now(timezone.utc),
    }
    insert_result = await db.yield_predictions.insert_one(prediction_doc)

    await db.user_history.insert_one({
        "user_id": ObjectId(user_id),
        "activity_type": "yield_prediction",
        "description": f"Yield prediction: {data['crop_type']} - {result['predicted_yield']:.0f} kg/hectare",
        "record_id": insert_result.inserted_id,
        "created_at": datetime.now(timezone.utc),
    })

    return {
        "crop_type": data["crop_type"],
        "predicted_yield": result["predicted_yield"],
        "predicted_production": result["predicted_production"],
        "yield_unit": result["yield_unit"],
        "confidence": result["confidence"],
        "suitability": result["suitability"],
        "conditions_summary": result["conditions_summary"],
        "improvement_suggestions": result["improvement_suggestions"],
        "prediction_id": str(insert_result.inserted_id),
        "created_at": prediction_doc["created_at"],
        "is_estimate": True,
    }


async def get_yield_history(user_id: str, page: int = 1, per_page: int = 10) -> dict:
    """Get paginated yield prediction history."""
    db = get_db()
    query = {"user_id": ObjectId(user_id)}
    total = await db.yield_predictions.count_documents(query)
    skip = (page - 1) * per_page
    cursor = db.yield_predictions.find(query).sort("created_at", -1).skip(skip).limit(per_page)
    items = []
    async for doc in cursor:
        items.append({
            "id": str(doc["_id"]),
            "crop_type": doc.get("crop_type", ""),
            "state": doc.get("state", ""),
            "season": doc.get("season", ""),
            "area": doc.get("area", 0),
            "predicted_yield": doc.get("predicted_yield", 0),
            "created_at": doc.get("created_at"),
        })
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page if per_page > 0 else 0,
    }


async def delete_yield_prediction(record_id: str, user_id: str) -> bool:
    """Delete a yield prediction record."""
    db = get_db()
    result = await db.yield_predictions.delete_one({
        "_id": ObjectId(record_id),
        "user_id": ObjectId(user_id),
    })
    if result.deleted_count > 0:
        await db.user_history.delete_many({
            "record_id": ObjectId(record_id),
            "user_id": ObjectId(user_id),
        })
        return True
    return False
