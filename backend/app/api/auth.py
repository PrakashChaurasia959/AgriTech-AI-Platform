"""Authentication API routes."""
from fastapi import APIRouter, Depends
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    TokenResponse,
    ForgotPasswordResponse,
    ResetPasswordResponse,
)
from app.services.auth_service import (
    register_user,
    authenticate_user,
    create_token_response,
    request_password_reset,
    reset_password,
)
from app.core.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(data: UserRegister):
    user = await register_user(
        full_name=data.full_name,
        email=data.email,
        mobile_number=data.mobile_number,
        password=data.password,
    )
    return await create_token_response(user)


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin):
    user = await authenticate_user(data.email, data.password)
    return await create_token_response(user)


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(data: ForgotPasswordRequest):
    return await request_password_reset(data.email)


@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password_route(data: ResetPasswordRequest):
    return await reset_password(data.token, data.new_password)


@router.get("/me")
async def get_me(user=Depends(get_current_user)):
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
