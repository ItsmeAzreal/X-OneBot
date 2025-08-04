"""Menu management endpoints."""
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.core.dependencies import get_current_business, get_multi_tenant_filter
from app.models import MenuCategory, MenuItem, Business
from app.schemas.menu import (
    MenuCategoryCreate,
    MenuCategoryUpdate,
    MenuCategoryResponse,
    MenuItemCreate,
    MenuItemUpdate,
    MenuItemResponse
)

router = APIRouter()


# ============= MENU CATEGORIES =============

@router.get("/categories", response_model=List[MenuCategoryResponse])
async def get_categories(
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business)
) -> Any:
    """Get all menu categories for current business."""
    categories = db.query(MenuCategory).filter(
        MenuCategory.business_id == business.id
    ).order_by(MenuCategory.display_order).all()
    
    return categories


@router.post("/categories", response_model=MenuCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: MenuCategoryCreate,
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business)
) -> Any:
    """Create new menu category."""
    # Create category
    category = MenuCategory(
        **category_data.dict(),
        business_id=business.id
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    
    return category


@router.put("/categories/{category_id}", response_model=MenuCategoryResponse)
async def update_category(
    category_id: int,
    category_data: MenuCategoryUpdate,
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business)
) -> Any:
    """Update menu category."""
    # Get category (with multi-tenant check)
    category = db.query(MenuCategory).filter(
        MenuCategory.id == category_id,
        MenuCategory.business_id == business.id
    ).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Update fields
    update_data = category_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)
    
    db.commit()
    db.refresh(category)
    
    return category


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business)
) -> None:
    """Delete menu category."""
    # Get category
    category = db.query(MenuCategory).filter(
        MenuCategory.id == category_id,
        MenuCategory.business_id == business.id
    ).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Delete (will cascade to items if configured)
    db.delete(category)
    db.commit()


# ============= MENU ITEMS =============

@router.get("/items", response_model=List[MenuItemResponse])
async def get_menu_items(
    category_id: Optional[int] = None,
    is_available: Optional[bool] = None,
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business)
) -> Any:
    """
    Get menu items with optional filters.
    
    Query parameters:
    - category_id: Filter by category
    - is_available: Filter by availability
    """
    # Base query
    query = db.query(MenuItem).filter(
        MenuItem.business_id == business.id
    )
    
    # Apply filters
    if category_id is not None:
        query = query.filter(MenuItem.category_id == category_id)
    
    if is_available is not None:
        query = query.filter(MenuItem.is_available == is_available)
    
    # Order by category and display order
    items = query.order_by(
        MenuItem.category_id,
        MenuItem.display_order
    ).all()
    
    return items


@router.get("/items/{item_id}", response_model=MenuItemResponse)
async def get_menu_item(
    item_id: int,
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business)
) -> Any:
    """Get specific menu item."""
    item = db.query(MenuItem).filter(
        MenuItem.id == item_id,
        MenuItem.business_id == business.id
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu item not found"
        )
    
    return item


@router.post("/items", response_model=MenuItemResponse, status_code=status.HTTP_201_CREATED)
async def create_menu_item(
    item_data: MenuItemCreate,
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business)
) -> Any:
    """Create new menu item."""
    # Verify category belongs to business if provided
    if item_data.category_id:
        category = db.query(MenuCategory).filter(
            MenuCategory.id == item_data.category_id,
            MenuCategory.business_id == business.id
        ).first()
        
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid category ID"
            )
    
    # Create item
    item = MenuItem(
        **item_data.dict(),
        business_id=business.id
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    
    return item


@router.put("/items/{item_id}", response_model=MenuItemResponse)
async def update_menu_item(
    item_id: int,
    item_data: MenuItemUpdate,
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business)
) -> Any:
    """Update menu item."""
    # Get item
    item = db.query(MenuItem).filter(
        MenuItem.id == item_id,
        MenuItem.business_id == business.id
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu item not found"
        )
    
    # Update fields
    update_data = item_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)
    
    db.commit()
    db.refresh(item)
    
    return item


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_menu_item(
    item_id: int,
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business)
) -> None:
    """Delete menu item."""
    # Get item
    item = db.query(MenuItem).filter(
        MenuItem.id == item_id,
        MenuItem.business_id == business.id
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu item not found"
        )
    
    db.delete(item)
    db.commit()