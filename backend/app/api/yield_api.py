"""Yield prediction API routes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from app.core.deps import get_current_user
from app.schemas.yield_pred import YieldPredictionRequest
from app.services.yield_service import predict_yield, get_yield_history, delete_yield_prediction
from app.services.report_service import generate_yield_report

router = APIRouter(prefix="/yield", tags=["Yield Prediction"])


@router.post("/predict")
async def predict(data: YieldPredictionRequest, user=Depends(get_current_user)):
    """Predict crop yield based on input parameters."""
    return await predict_yield(data.model_dump(), str(user["_id"]))


@router.get("/history")
async def history(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    user=Depends(get_current_user),
):
    """Get paginated yield prediction history."""
    return await get_yield_history(str(user["_id"]), page, per_page)


@router.delete("/history/{record_id}")
async def delete_record(record_id: str, user=Depends(get_current_user)):
    """Delete a yield prediction record."""
    deleted = await delete_yield_prediction(record_id, str(user["_id"]))
    if not deleted:
        raise HTTPException(status_code=404, detail="Record not found")
    return {"message": "Record deleted successfully"}


@router.get("/report/{record_id}")
async def download_report(record_id: str, user=Depends(get_current_user)):
    """Download a PDF report for a yield prediction."""
    from app.core.database import get_db
    from bson import ObjectId
    db = get_db()
    record = await db.yield_predictions.find_one({
        "_id": ObjectId(record_id),
        "user_id": ObjectId(str(user["_id"])),
    })
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    record["id"] = str(record["_id"])
    pdf_bytes = generate_yield_report(record, user)
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=yield_report_{record_id}.pdf"},
    )


@router.get("/options")
async def get_options():
    """Return available options for yield prediction form."""
    return {
        "crops": ["Rice", "Wheat", "Maize", "Cotton", "Sugarcane", "Potato",
                  "Tomato", "Soybean", "Groundnut", "Chickpea", "Onion", "Banana",
                  "Apple", "Mango", "Orange", "Grapes", "Papaya", "Coffee", "Coconut", "Jute"],
        "seasons": ["Kharif", "Rabi", "Summer", "Whole Year"],
        "states": ["Andhra Pradesh", "Assam", "Bihar", "Gujarat", "Haryana",
                   "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra",
                   "Punjab", "Rajasthan", "Tamil Nadu", "Telangana",
                   "Uttar Pradesh", "West Bengal", "Odisha"],
        "soil_types": ["Loamy", "Sandy", "Clayey", "Black", "Red", "Alluvial", "Laterite"],
    }
