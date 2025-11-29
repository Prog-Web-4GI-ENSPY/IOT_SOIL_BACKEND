from fastapi import APIRouter
from app.routers import auth_router, users_router

api_router = APIRouter()

# Authentication endpoints
api_router.include_router(
    auth_router.router,
    prefix="/auth",
    tags=["Authentication"]
)

# User management endpoints
api_router.include_router(
    users_router.router,
    prefix="/users",
    tags=["Users"]
)
