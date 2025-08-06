"""Authentication endpoints."""
from app.core.dependencies import get_current_user
from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.config.settings import settings
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.exceptions import DuplicateError
from app.models import Business, User, UserRole
from app.schemas.auth import Token, RegisterBusinessRequest, LoginRequest

router = APIRouter()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register_business(
    request: RegisterBusinessRequest,
    db: Session = Depends(get_db)
) -> Any:
    """
    Register a new business with admin user.
    
    This endpoint:
    1. Creates a new business
    2. Creates an admin user for that business
    3. Returns JWT token for immediate login
    """
    # Check if business slug already exists
    existing_business = db.query(Business).filter(
        Business.slug == request.business_slug
    ).first()
    
    if existing_business:
        raise DuplicateError("Business", "slug", request.business_slug)
    
    # Check if email already exists
    existing_user = db.query(User).filter(
        User.email == request.admin_email
    ).first()
    
    if existing_user:
        raise DuplicateError("User", "email", request.admin_email)
    
    # Create business
    business = Business(
        name=request.business_name,
        slug=request.business_slug,
        subscription_plan="basic",  # Start with basic plan
        is_active=True
    )
    db.add(business)
    db.commit()
    db.refresh(business)
    
    # Create admin user
    admin_user = User(
        email=request.admin_email,
        hashed_password=get_password_hash(request.admin_password),
        name=request.admin_name,
        role=UserRole.OWNER,
        business_id=business.id,
        is_active=True,
        is_verified=True  # Auto-verify business owners
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "user_id": admin_user.id,
            "email": admin_user.email,
            "business_id": business.id,
            "role": admin_user.role
        },
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Any:
    """
    Login with email and password.
    
    OAuth2PasswordRequestForm expects:
    - username (we use email)
    - password
    """
    # Find user by email
    user = db.query(User).filter(
        User.email == form_data.username
    ).first()
    
    # Verify user exists and password is correct
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is inactive"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "user_id": user.id,
            "email": user.email,
            "business_id": user.business_id,
            "role": user.role
        },
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/test-token")
async def test_token(current_user: User = Depends(get_current_user)) -> Any:
    """
    Test if token is valid.
    
    Returns current user info.
    """
    return {
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role,
        "business_id": current_user.business_id
    }