from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class ProductTypeBase(BaseModel):
    name: str

class ProductTypeCreate(ProductTypeBase):
    pass

class ProductType(ProductTypeBase):
    id: UUID
    
    class Config:
        orm_mode = True

class ProductBase(BaseModel):
    name: str
    type_id: UUID
    power: Optional[str] = None
    lifespan: Optional[str] = None
    price: float
    description: Optional[str] = None
    image_url: Optional[str] = None
    discount: Optional[float] = 0.0

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: UUID
    
    class Config:
        orm_mode = True