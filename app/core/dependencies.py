"""Common dependencies for API endpoints."""
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.models.business import Business

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.
    
    This dependency:
    1. Extracts token from Authorization header
    2. Decodes the JWT
    3. Fetches user from database
    4. Validates user exists and is active
    
    Raises:
        HTTPException: If token invalid or user not found
    """
    # Decode token
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user info from token
    user_id: int = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    # Fetch user from database
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    
    return user


async def get_current_business(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Business:
    """
    Get the business associated with current user.
    
    This ensures:
    1. User has a business (is staff/owner)
    2. Business is active
    
    Raises:
        HTTPException: If user has no business or business inactive
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
    
    Use this to ensure queries only return data for the current business:
    
    Example:
        @app.get("/items")
        def get_items(
            filter: Dict = Depends(get_multi_tenant_filter),
            db: Session = Depends(get_db)
        ):
            return db.query(Item).filter_by(**filter).all()
    """
    return {"business_id": business.id}