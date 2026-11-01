"""
Disease detection API routes.

New endpoint:
  GET /api/disease/model-info
    Returns whether a real CNN is loaded (production mode) or the
    demo OpenCV fallback is active, so the frontend can display the
    correct label without hard-coding it.
"""
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.core.deps import get_current_user
from app.services.disease_service import (
    validate_image_file,
    predict_disease,
    get_disease_history,
    get_disease_prediction_detail,
    delete_disease_prediction,
)
from app.services.report_service import generate_disease_report

router = APIRouter(prefix="/disease", tags=["Disease Detection"])


# ── Model info ────────────────────────────────────────────────────────────────

@router.get("/model-info")
async def model_info():
    """
    Return the current state of the disease detection model.

    Response fields:
      mode          "production" | "demo"
      model_loaded  True when a real Keras CNN is in memory
      model_path    Configured path (may not exist if demo mode)
      num_classes   Number of output classes the model was trained on
      input_size    Expected image input dimension (e.g. 224)
    """
    from app.core.config import settings
    from app.ml.disease_model import _keras_model, _model_load_error

    model_loaded = _keras_model is not None
    return {
        "mode":           "production" if model_loaded else "demo",
        "model_loaded":   model_loaded,
        "model_path":     settings.DISEASE_MODEL_PATH,
        "num_classes":    settings.DISEASE_MODEL_NUM_CLASSES,
        "input_size":     settings.DISEASE_MODEL_INPUT_SIZE,
        "error_message":  _model_load_error if not model_loaded else None,
    }


# ── Prediction ────────────────────────────────────────────────────────────────

@router.post("/predict")
async def predict(
    file:      UploadFile = File(...),
    crop_type: str        = Form(default=""),
    user=Depends(get_current_user),
):
    """
    Upload a leaf image and receive a disease classification.

    - In **production mode** (DISEASE_MODEL_MODE=production + valid model file):
      the image is preprocessed and passed through a Keras CNN.
      `is_demo_mode` will be `false` in the response.

    - In **demo mode** (default or when model is missing):
      OpenCV colour statistics drive the prediction.
      `is_demo_mode` will be `true` in the response.
    """
    content = await file.read()
    error = validate_image_file(file.filename or "", len(content))
    if error:
        raise HTTPException(status_code=400, detail=error)
    return await predict_disease(content, crop_type, str(user["_id"]))


# ── History ───────────────────────────────────────────────────────────────────

@router.get("/history")
async def history(
    page:     int = Query(1,  ge=1),
    per_page: int = Query(10, ge=1, le=50),
    search:   str = Query(""),
    user=Depends(get_current_user),
):
    """Paginated disease prediction history for the current user."""
    return await get_disease_history(str(user["_id"]), page, per_page, search)


@router.get("/history/{prediction_id}")
async def history_detail(prediction_id: str, user=Depends(get_current_user)):
    """Full details of a single disease prediction."""
    result = await get_disease_prediction_detail(prediction_id, str(user["_id"]))
    if not result:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return result


@router.delete("/history/{prediction_id}")
async def delete_history(prediction_id: str, user=Depends(get_current_user)):
    """Delete a disease prediction record."""
    deleted = await delete_disease_prediction(prediction_id, str(user["_id"]))
    if not deleted:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return {"message": "Prediction deleted successfully"}


# ── PDF report ────────────────────────────────────────────────────────────────

@router.get("/report/{prediction_id}")
async def download_report(prediction_id: str, user=Depends(get_current_user)):
    """Stream a PDF report for a disease prediction."""
    prediction = await get_disease_prediction_detail(prediction_id, str(user["_id"]))
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    pdf_bytes = generate_disease_report(prediction, user)
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=disease_report_{prediction_id}.pdf"},
    )


# ── Supported crops ───────────────────────────────────────────────────────────

@router.get("/crops")
async def supported_crops():
    """List of crop types supported by the disease detection model."""
    return {
        "crops": [
            {"value": "Tomato",  "label": "Tomato",       "icon": "🍅"},
            {"value": "Potato",  "label": "Potato",       "icon": "🥔"},
            {"value": "Corn",    "label": "Corn / Maize", "icon": "🌽"},
            {"value": "Apple",   "label": "Apple",        "icon": "🍎"},
            {"value": "Grape",   "label": "Grape",        "icon": "🍇"},
            {"value": "Pepper",  "label": "Pepper",       "icon": "🫑"},
            {"value": "Peach",   "label": "Peach",        "icon": "🍑"},
            {"value": "Cherry",  "label": "Cherry",       "icon": "🍒"},
            {"value": "Squash",  "label": "Squash",       "icon": "🎃"},
            {"value": "Strawberry", "label": "Strawberry","icon": "🍓"},
        ]
    }
