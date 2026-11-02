"""
Smart Agriculture Backend - FastAPI Application Entry Point.

This module creates the FastAPI app, configures CORS, connects to MongoDB,
bootstraps an admin user, and registers all API routers.
"""
import logging
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection, get_db
from app.core import database as db_module
from app.core.security import get_password_hash

from app.api import auth, users, disease, crop, yield_api, weather, admin, system_status

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def create_admin_user() -> None:
    """Create the bootstrap admin user if it doesn't exist."""
    db = get_db()
    existing = await db.users.find_one({"email": settings.ADMIN_EMAIL.lower()})
    if existing:
        logger.info("Admin user already exists.")
        return
    admin_doc = {
        "full_name": "System Admin",
        "email": settings.ADMIN_EMAIL.lower(),
        "mobile_number": "0000000000",
        "password_hash": get_password_hash(settings.ADMIN_PASSWORD),
        "role": "admin",
        "is_active": True,
        "farm_name": None,
        "location": None,
        "avatar_url": None,
        "created_at": datetime.now(timezone.utc),
    }
    await db.users.insert_one(admin_doc)
    logger.info("Admin user created: %s", settings.ADMIN_EMAIL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: connect to DB on startup, close on shutdown."""
    import asyncio, os
    logger.info("=== Smart Agriculture API Starting ===")
    await connect_to_mongo()
    await create_admin_user()

    # Pre-load ML models (all run in a thread to avoid blocking the event loop)
    from app.ml.crop_model import recommender
    from app.ml.yield_model import predictor
    logger.info("Loading crop + yield ML models...")
    await asyncio.to_thread(recommender.load_or_train)
    await asyncio.to_thread(predictor.load_or_train)
    logger.info("Crop + yield models ready.")

    # Pre-load disease CNN if production mode is configured
    from app.core.config import settings as cfg
    if cfg.DISEASE_MODEL_MODE.lower() == "production":
        from app.ml.disease_model import _load_keras_model, _keras_model, _model_load_error
        logger.info("Production mode: loading Keras CNN disease model at startup â€¦")
        await asyncio.to_thread(_load_keras_model)
        # Re-import to get updated values after the thread ran
        from app.ml import disease_model as dm
        if dm._keras_model is not None:
            logger.info(
                "CNN disease model loaded â€” input: %s | classes: %s",
                dm._keras_model.input_shape,
                dm._keras_model.output_shape[-1],
            )
        else:
            logger.warning(
                "CNN disease model could NOT be loaded: %s â€” demo fallback active.",
                dm._model_load_error,
            )
    else:
        logger.info("Disease detection: demo mode (set DISEASE_MODEL_MODE=production to use CNN).")

    logger.info("=== Smart Agriculture API Ready ===")
    yield
    await close_mongo_connection()
    logger.info("=== Smart Agriculture API Stopped ===")


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Powered Smart Agriculture & Crop Disease Detection System API",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers under /api prefix
API_PREFIX = settings.API_V1_PREFIX
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(users.router, prefix=API_PREFIX)
app.include_router(disease.router, prefix=API_PREFIX)
app.include_router(crop.router, prefix=API_PREFIX)
app.include_router(yield_api.router, prefix=API_PREFIX)
app.include_router(weather.router, prefix=API_PREFIX)
app.include_router(admin.router, prefix=API_PREFIX)
app.include_router(system_status.router)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "auth": f"{API_PREFIX}/auth",
            "users": f"{API_PREFIX}/users",
            "disease": f"{API_PREFIX}/disease",
            "crop": f"{API_PREFIX}/crop",
            "yield": f"{API_PREFIX}/yield",
            "weather": f"{API_PREFIX}/weather",
            "admin": f"{API_PREFIX}/admin",
        },
    }


@app.get("/health", tags=["Health"])
async def health():
    """Health check endpoint â€” reports database connection status."""
    db = get_db()
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "database": db_module.active_connection,
        "database_connected": db is not None,
    }
