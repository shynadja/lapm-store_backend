from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import uuid

class ProductType(Base):
    __tablename__ = "product_types"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), nullable=False, unique=True)
    
    products = relationship("Product", back_populates="product_type")

class Product(Base):
    __tablename__ = "products"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    type_id = Column(UUID(as_uuid=True), ForeignKey("product_types.id"))
    power = Column(String(20))
    lifespan = Column(String(50))
    price = Column(Float, nullable=False)
    description = Column(Text)
    image_url = Column(String(255))
    discount = Column(Float, default=0.0)
    
    product_type = relationship("ProductType", back_populates="products")