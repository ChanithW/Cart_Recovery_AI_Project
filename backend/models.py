from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class CartStatus(str, Enum):
    active = "active"
    abandoned = "abandoned"
    recovered = "recovered"
    completed = "completed"

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime
    last_active: datetime

class ProductResponse(BaseModel):
    id: int
    name: str
    description: str
    price: float
    image_url: str
    stock_quantity: int
    category: str
    created_at: datetime

class CartItemCreate(BaseModel):
    product_id: int
    quantity: int

class CartItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    price: float
    product_name: str
    product_image: str

class CartUpdate(BaseModel):
    user_id: Optional[int] = None
    session_id: str
    items: List[CartItemCreate]

class CartResponse(BaseModel):
    id: int
    user_id: Optional[int]
    session_id: str
    status: CartStatus
    total_value: float
    items: List[CartItemResponse]
    created_at: datetime
    updated_at: datetime

class RecoveryEmailRequest(BaseModel):
    cart_id: int
    template_id: Optional[int] = None

class RecoveryEmailResponse(BaseModel):
    email: Dict[str, str]
    offer: Dict[str, Any]
    cart_value: float
    message: str

class AbandonedCartAnalytics(BaseModel):
    total_abandoned: int
    total_value: float
    carts: List[Dict[str, Any]]
    
class OfferCreate(BaseModel):
    offer_type: str
    offer_value: float
    offer_description: str
    valid_until: Optional[datetime] = None

class RecoveryAttemptResponse(BaseModel):
    id: int
    cart_id: int
    email_subject: str
    email_content: str
    offer_type: str
    offer_value: float
    email_sent_at: datetime
    opened: bool
    clicked: bool
    recovered: bool

class UserBehaviorEvent(BaseModel):
    user_id: Optional[int] = None
    session_id: str
    action: str
    page_url: str
    product_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

class EmailTemplate(BaseModel):
    id: int
    name: str
    subject_template: str
    body_template: str
    template_type: str
    is_active: bool

class EmailTemplateCreate(BaseModel):
    name: str
    subject_template: str
    body_template: str
    template_type: str = "recovery"
