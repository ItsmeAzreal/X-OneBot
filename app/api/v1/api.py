"""Main API router that includes all endpoints."""
from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    business,
    menu,
    tables,
    orders,
    chat,
    voice,  # New in Week 3
    whatsapp,  # New in Week 3
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

api_router.include_router(
    voice.router,
    prefix="/voice",
    tags=["Voice Calls"]
)

api_router.include_router(
    whatsapp.router,
    prefix="/whatsapp",
    tags=["WhatsApp"]
)