"""System status + API keys audit."""
import logging
from pathlib import Path

import httpx
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(prefix="/api-status", tags=["System Status"])
logger = logging.getLogger(__name__)


@router.get("/keys")
async def api_keys_status():
    owm_key = settings.OPENWEATHER_API_KEY
    kaggle_token = settings.KAGGLE_API_TOKEN
    model_path = Path(settings.DISEASE_MODEL_PATH)
    class_names_path = model_path.with_name(f"{model_path.stem}.classes.json")
    metrics_path = model_path.with_name(f"{model_path.stem}.metrics.json")
    model_trained = class_names_path.is_file() and metrics_path.is_file()

    return {
        "keys": {
            "openweather": {
                "name": "OpenWeatherMap",
                "configured": bool(owm_key),
                "status": "configured" if owm_key else "not_configured",
                "signup_url": "https://home.openweathermap.org/api_keys",
                "required_for": ["Live weather auto-fill on Crop Recommendation page"],
            },
            "mongodb": {
                "name": "MongoDB Atlas",
                "configured": "mongodb+srv" in settings.MONGODB_URL,
                "cluster": settings.MONGODB_URL.split("@")[-1].split("/")[0] if "@" in settings.MONGODB_URL else "local",
                "database": settings.MONGODB_DB_NAME,
                "note": "Connected via standard SRV",
                "required_for": ["All database operations"],
            },
            "kaggle": {
                "name": "Kaggle API v2",
                "configured": bool(kaggle_token),
                "status": "configured" if kaggle_token else "not_configured",
                "auth_method": "Authorization Bearer header",
                "training_script": "backend/train_plant_disease_cnn.py",
                "required_for": ["PlantVillage CNN training"],
            },
        },
        "models": {
            "disease_cnn": {
                "mode": settings.DISEASE_MODEL_MODE,
                "path": settings.DISEASE_MODEL_PATH,
                "input_size": settings.DISEASE_MODEL_INPUT_SIZE,
                "num_classes": settings.DISEASE_MODEL_NUM_CLASSES,
                "training_status": "trained" if model_trained else "not_verified",
                "action_needed": None if model_trained else "Run: python train_plant_disease_cnn.py",
            },
            "crop_recommender": {"type": "RandomForest", "status": "auto_trained", "features": "N,P,K,temp,humidity,pH,rainfall"},
            "yield_predictor":  {"type": "RandomForest Regressor", "status": "auto_trained", "features": "crop,state,season,area,rainfall,temp,soil,fertiliser"},
        },
        "security": {
            "jwt_custom_secret": settings.JWT_SECRET != "CHANGE_ME_TO_A_RANDOM_SECRET_KEY_AT_LEAST_64_CHARS_LONG",
            "jwt_secret_length": len(settings.JWT_SECRET),
        },
    }


@router.get("/health-detailed")
async def health_detailed():
    from app.core.database import get_db, active_connection
    from app.ml import disease_model as dm
    db = get_db()
    model_loaded = dm._keras_model is not None
    try:
        users_count = await db.users.count_documents({})
        db_ok = True
    except Exception:
        users_count = 0
        db_ok = False

    return {
        "api": "healthy",
        "database": {
            "status": "connected" if db_ok else "error",
            "connection_type": active_connection,
            "users_in_db": users_count,
        },
        "ml_models": {
            "disease_cnn": {
                "mode": settings.DISEASE_MODEL_MODE,
                "loaded": model_loaded,
                "classes": settings.DISEASE_MODEL_NUM_CLASSES,
            },
            "crop_recommender": "ready",
            "yield_predictor": "ready",
        },
        "integrations": {
            "open_meteo": "active_no_key_needed",
            "openweathermap": "configured" if settings.OPENWEATHER_API_KEY else "not_configured",
            "kaggle": "configured" if settings.KAGGLE_API_TOKEN else "not_configured",
        },
    }


@router.get("/kaggle-test")
async def kaggle_live_test():
    """Verify Kaggle API v2 auth and search for PlantVillage datasets."""
    token = settings.KAGGLE_API_TOKEN
    if not token:
        return {"status": "NOT_CONFIGURED", "error": "KAGGLE_API_TOKEN not set in .env"}
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                "https://www.kaggle.com/api/v1/datasets/list",
                params={"search": "plantvillage plant disease", "page": 1},
                headers={"Authorization": f"Bearer {token}"},
            )
        if response.is_error:
            logger.warning("Kaggle API v2 returned HTTP %s.", response.status_code)
            return {
                "status": "FAILED",
                "error": "Kaggle API authentication or dataset search failed.",
                "http_status": response.status_code,
            }
        datasets = response.json()
        if not isinstance(datasets, list):
            return {"status": "FAILED", "error": "Kaggle returned an invalid dataset list."}
        results = [
            {"ref": item.get("ref", ""), "title": item.get("title", "")}
            for item in datasets[:5]
            if isinstance(item, dict)
        ]
        return {
            "status": "WORKING",
            "auth": "SUCCESS",
            "datasets_found": len(results),
            "sample_datasets": results,
            "download_method": "dataset_download_files()",
            "training_command": "cd backend && .\\venv\\Scripts\\python.exe train_plant_disease_cnn.py",
        }
    except httpx.RequestError as exc:
        logger.error("Kaggle API v2 request failed (%s)", type(exc).__name__)
        return {"status": "FAILED", "error": "Kaggle API request could not be completed."}
    except ValueError:
        logger.error("Kaggle API v2 returned invalid JSON.")
        return {"status": "FAILED", "error": "Kaggle returned an invalid response."}
