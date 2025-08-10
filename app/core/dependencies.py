"""Common dependencies for API endpoints."""
from typing import Generator, Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError 
from app.config.database import get_db
from app.core.security import decode_access_token, JWTError
from app.models.user import User
from app.models.business import Business

# This scheme is for dependencies that REQUIRE a token
oauth2_scheme_strict = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# This scheme is for OPTIONAL tokens. It won't error if the token is missing.
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user(
    token: str = Depends(oauth2_scheme_strict),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token. This is a strict dependency
    and will raise an error if the user is not found or the token is invalid.
    """
    try:
        payload = decode_access_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id: int = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    
    return user


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Gets the current user if a token is provided, but returns None
    instead of raising an error if the token is missing or invalid.
    """
    if token is None:
        return None
    try:
        payload = decode_access_token(token)
        if not payload:
            return None

        user_id: int = payload.get("user_id")
        if not user_id:
            return None

        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            return None

        return user
    except (JWTError, Exception):
        # If any error occurs during token processing, treat as a guest user.
        return None


async def get_current_business(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Business:
    """
    Get the business associated with current user.
    """
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with any business",
        )
    
    business = db.query(Business).filter(
        Business.id == current_user.business_id
    ).first()
    
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found",
        )
    
    if not business.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Business account is inactive",
        )
    
    return business


def get_multi_tenant_filter(business: Business = Depends(get_current_business)) -> Dict[str, Any]:
    """
    Get filter dict for multi-tenant queries.
    """
    return {"business_id": business.id}