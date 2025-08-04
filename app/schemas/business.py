"""Business schemas."""
from typing import Optional, Dict, Any
from datetime import datetime
from app.schemas.base import BaseSchema, TimestampSchema, IDSchema
from app.models.business import SubscriptionPlan


class BusinessBase(BaseSchema):
    """Base business fields."""
    name: str
    slug: str
    description: Optional[str] = None


class BusinessCreate(BusinessBase):
    """Create new business."""
    contact_info: Optional[Dict[str, Any]] = {}
    settings: Optional[Dict[str, Any]] = {}


class BusinessUpdate(BaseSchema):
    """Update business fields."""
    name: Optional[str] = None
    description: Optional[str] = None
    contact_info: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None
    branding_config: Optional[Dict[str, Any]] = None


class BusinessResponse(BusinessBase, IDSchema, TimestampSchema):
    """Business response with all fields."""
    subscription_plan: SubscriptionPlan
    is_active: bool
    contact_info: Dict[str, Any]
    settings: Dict[str, Any]
    branding_config: Dict[str, Any]
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Sunrise Cafe",
                "slug": "sunrise-cafe",
                "description": "Best coffee in town",
                "subscription_plan": "pro",
                "is_active": True,
                "contact_info": {
                    "phone": "+1234567890",
                    "email": "hello@sunrisecafe.com",
                    "address": "123 Main St"
                },
                "settings": {
                    "working_hours": {
                        "mon": "9:00-17:00",
                        "tue": "9:00-17:00"
                    },
                    "languages": ["en", "es"]
                },
                "branding_config": {
                    "primary_color": "#FF6B6B",
                    "logo_url": "https://example.com/logo.png"
                },
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }


### 19. `app/schemas/menu.py` - Menu Schemas
**Purpose**: Menu category and item validation

```python
"""Menu schemas."""
from typing import Optional, List, Dict, Any
from app.schemas.base import BaseSchema, TimestampSchema, IDSchema


class MenuCategoryBase(BaseSchema):
    """Base category fields."""
    name: str
    description: Optional[str] = None
    display_order: int = 0
    is_active: bool = True
    icon: Optional[str] = None
    image_url: Optional[str] = None


class MenuCategoryCreate(MenuCategoryBase):
    """Create new category."""
    pass


class MenuCategoryUpdate(BaseSchema):
    """Update category fields."""
    name: Optional[str] = None
    description: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None
    icon: Optional[str] = None
    image_url: Optional[str] = None


class MenuCategoryResponse(MenuCategoryBase, IDSchema, TimestampSchema):
    """Category response."""
    business_id: int


class MenuItemBase(BaseSchema):
    """Base menu item fields."""
    name: str
    description: Optional[str] = None
    base_price: float
    category_id: Optional[int] = None
    is_available: bool = True
    preparation_time: int = 10
    dietary_tags: List[str] = []
    allergens: List[str] = []
    calories: Optional[int] = None
    image_url: Optional[str] = None
    display_order: int = 0
    customizations: List[Dict[str, Any]] = []


class MenuItemCreate(MenuItemBase):
    """Create new menu item."""
    pass


class MenuItemUpdate(BaseSchema):
    """Update menu item fields."""
    name: Optional[str] = None
    description: Optional[str] = None
    base_price: Optional[float] = None
    category_id: Optional[int] = None
    is_available: Optional[bool] = None
    preparation_time: Optional[int] = None
    dietary_tags: Optional[List[str]] = None
    allergens: Optional[List[str]] = None
    calories: Optional[int] = None
    image_url: Optional[str] = None
    display_order: Optional[int] = None
    customizations: Optional[List[Dict[str, Any]]] = None


class MenuItemResponse(MenuItemBase, IDSchema, TimestampSchema):
    """Menu item response."""
    business_id: int
    category: Optional[MenuCategoryResponse] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Cappuccino",
                "description": "Rich espresso with steamed milk foam",
                "base_price": 4.50,
                "category_id": 1,
                "is_available": True,
                "preparation_time": 5,
                "dietary_tags": ["vegetarian"],
                "allergens": ["milk"],
                "calories": 120,
                "image_url": "https://example.com/cappuccino.jpg",
                "customizations": [
                    {
                        "name": "Size",
                        "options": ["Small", "Medium", "Large"],
                        "price_diff": [0, 1.0, 2.0]
                    },
                    {
                        "name": "Milk",
                        "options": ["Regular", "Oat", "Almond", "Soy"],
                        "price_diff": [0, 0.5, 0.5, 0.5]
                    }
                ],
                "business_id": 1,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }