from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from enum import Enum

class OrderStatus(str, Enum):
    CREATED = "оформлен"
    ASSEMBLED = "собран"
    RECEIVED = "получен"

class OrderItemBase(BaseModel):
    product_id: UUID
    quantity: int
    price: float

class OrderItemCreate(OrderItemBase):
    pass

class OrderItem(OrderItemBase):
    id: UUID
    order_id: UUID
    
    class Config:
        orm_mode = True

class OrderBase(BaseModel):
    user_id: UUID
    total_amount: float
    status: Optional[OrderStatus] = OrderStatus.CREATED
    delivery_method: Optional[str] = "самовывоз"
    payment_method: Optional[str] = "при получении"

class OrderCreate(OrderBase):
    items: List[OrderItemCreate]

class Order(OrderBase):
    id: UUID
    created_at: datetime
    items: List[OrderItem]
    
    class Config:
        orm_mode = True