"""Main API router that includes all endpoints."""
from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    business,
    menu,
    tables,
    orders,
    chat,
    universal,    # NEW
    dashboard,    # NEW
    kitchen,      # NEW
    onboarding,   # NEW
)

# Create main router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

api_router.include_router(
    business.router,
    prefix="/business",
    tags=["Business Management"]
)

api_router.include_router(
    menu.router,
    prefix="/menu",
    tags=["Menu Management"]
)

api_router.include_router(
    tables.router,
    prefix="/tables",
    tags=["Table Management"]
)

api_router.include_router(
    orders.router,
    prefix="/orders",
    tags=["Order Management"]
)

api_router.include_router(
    chat.router,
    prefix="/chat",
    tags=["Chat System"]
)

# NEW ROUTERS FOR WEEK 4
api_router.include_router(
    universal.router,
    prefix="/universal",
    tags=["Universal System"]
)

api_router.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["Admin Dashboard"]
)

api_router.include_router(
    kitchen.router,
    prefix="/kitchen",
    tags=["Kitchen Management"]
)

api_router.include_router(
    onboarding.router,
    prefix="/onboarding",
    tags=["Onboarding"]
)