"""Crop recommendation service."""
import logging
from datetime import datetime, timezone
from bson import ObjectId
from app.core.database import get_db
from app.ml.crop_model import recommender, CROP_INFO

logger = logging.getLogger(__name__)

SOIL_INFO = {
    "Loamy": {"description": "Balanced soil with good drainage and nutrient retention", "ph_range": "6.0-7.0", "characteristics": ["Good water retention", "Well-aerated", "Rich in nutrients"]},
    "Sandy": {"description": "Fast-draining soil with low nutrient retention", "ph_range": "5.5-6.5", "characteristics": ["Drains quickly", "Low nutrient content", "Easy to work"]},
    "Clayey": {"description": "Heavy soil with high water retention", "ph_range": "6.0-7.5", "characteristics": ["High water retention", "Rich in nutrients", "Slow drainage"]},
    "Black": {"description": "Fertile soil ideal for cotton and sugarcane", "ph_range": "6.5-8.0", "characteristics": ["High fertility", "Good moisture retention", "Rich in minerals"]},
    "Red": {"description": "Iron-rich soil with moderate fertility", "ph_range": "5.5-7.0", "characteristics": ["Moderate fertility", "Good drainage", "Iron rich"]},
    "Alluvial": {"description": "Fertile river-deposit soil", "ph_range": "6.5-8.0", "characteristics": ["High fertility", "Good structure", "Easy to cultivate"]},
    "Laterite": {"description": "Tropical soil with low fertility", "ph_range": "5.0-6.0", "characteristics": ["Low fertility", "Rich in iron oxide", "Needs amendments"]},
}


async def recommend_crop(data: dict, user_id: str) -> dict:
    """Get crop recommendations and save to history."""
    recommendations = recommender.recommend(
        N=data["nitrogen"],
        P=data["phosphorus"],
        K=data["potassium"],
        temperature=data["temperature"],
        humidity=data["humidity"],
        ph=data["ph"],
        rainfall=data["rainfall"],
        top_k=3,
    )

    soil_info = SOIL_INFO.get(data.get("soil_type", "Loamy"), SOIL_INFO["Loamy"])
    top_crop = recommendations[0]["crop"] if recommendations else "Unknown"

    db = get_db()
    prediction_doc = {
        "user_id": ObjectId(user_id),
        "nitrogen": data["nitrogen"],
        "phosphorus": data["phosphorus"],
        "potassium": data["potassium"],
        "temperature": data["temperature"],
        "humidity": data["humidity"],
        "ph": data["ph"],
        "rainfall": data["rainfall"],
        "soil_type": data.get("soil_type", "Loamy"),
        "location": data.get("location", ""),
        "recommendations": recommendations,
        "top_recommendation": top_crop,
        "created_at": datetime.now(timezone.utc),
    }
    insert_result = await db.crop_recommendations.insert_one(prediction_doc)

    await db.user_history.insert_one({
        "user_id": ObjectId(user_id),
        "activity_type": "crop_recommendation",
        "description": f"Crop recommendation: {top_crop} based on soil analysis",
        "record_id": insert_result.inserted_id,
        "created_at": datetime.now(timezone.utc),
    })

    return {
        "recommendations": recommendations,
        "top_recommendation": top_crop,
        "soil_info": soil_info,
        "prediction_id": str(insert_result.inserted_id),
        "created_at": prediction_doc["created_at"],
    }


async def get_crop_history(user_id: str, page: int = 1, per_page: int = 10) -> dict:
    """Get paginated crop recommendation history."""
    db = get_db()
    query = {"user_id": ObjectId(user_id)}
    total = await db.crop_recommendations.count_documents(query)
    skip = (page - 1) * per_page
    cursor = db.crop_recommendations.find(query).sort("created_at", -1).skip(skip).limit(per_page)
    items = []
    async for doc in cursor:
        items.append({
            "id": str(doc["_id"]),
            "top_recommendation": doc.get("top_recommendation", ""),
            "nitrogen": doc.get("nitrogen", 0),
            "phosphorus": doc.get("phosphorus", 0),
            "potassium": doc.get("potassium", 0),
            "temperature": doc.get("temperature", 0),
            "humidity": doc.get("humidity", 0),
            "ph": doc.get("ph", 0),
            "rainfall": doc.get("rainfall", 0),
            "created_at": doc.get("created_at"),
        })
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page if per_page > 0 else 0,
    }


async def delete_crop_recommendation(record_id: str, user_id: str) -> bool:
    """Delete a crop recommendation record."""
    db = get_db()
    result = await db.crop_recommendations.delete_one({
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
