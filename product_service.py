from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import uuid
from enum import Enum
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, Float, Text, ForeignKey, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres_password@db:5432/postgres")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class ProductTypeDB(Base):
    __tablename__ = "product_types"
    id = Column(Integer, primary_key=True, index=True)  # Изменено на Integer
    name = Column(String)

class ProductDB(Base):
    __tablename__ = "products"
    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    type_id = Column(Integer, ForeignKey("product_types.id"))  # Изменено на Integer
    power = Column(String)
    lifespan = Column(String)
    price = Column(Float)
    description = Column(Text)
    image_url = Column(String)
    discount = Column(Float)

Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ProductType(str, Enum):
    LED = "LED"
    INCANDESCENT = "лампы накаливания"
    SMART = "умные лампы"

class Product(BaseModel):
    id: str
    name: str
    type_id: int  # Изменено на int
    power: str
    lifespan: str
    price: float
    description: str
    image_url: str
    discount: Optional[float] = 0

    class Config:
        orm_mode = True

class ProductCreate(BaseModel):
    name: str
    type_id: int  # Изменено на int
    power: str
    lifespan: str
    price: float
    description: str
    image_url: str
    discount: Optional[float] = 0

@app.on_event("startup")
async def startup():
    db = SessionLocal()
    try:
        # Initialize only product types if they don't exist
        if not db.query(ProductTypeDB).first():
            # Теперь используем простые числа для id
            db.add_all([
                ProductTypeDB(id=1, name=ProductType.LED),
                ProductTypeDB(id=2, name=ProductType.INCANDESCENT),
                ProductTypeDB(id=3, name=ProductType.SMART),
            ])
            db.commit()
    finally:
        db.close()

@app.get("/products", response_model=List[Product])
async def get_products(db: Session = Depends(get_db)):
    products = db.query(ProductDB).all()
    return products

@app.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str, db: Session = Depends(get_db)):
    product = db.query(ProductDB).filter(ProductDB.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.post("/products", response_model=Product)
async def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    # Проверяем существование type_id
    if not db.query(ProductTypeDB).filter(ProductTypeDB.id == product.type_id).first():
        raise HTTPException(status_code=400, detail="Invalid type_id")
    
    db_product = ProductDB(id=str(uuid.uuid4()), **product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@app.put("/products/{product_id}", response_model=Product)
async def update_product(product_id: str, product: ProductCreate, db: Session = Depends(get_db)):
    # Проверяем существование type_id
    if not db.query(ProductTypeDB).filter(ProductTypeDB.id == product.type_id).first():
        raise HTTPException(status_code=400, detail="Invalid type_id")
    
    db_product = db.query(ProductDB).filter(ProductDB.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    for key, value in product.dict().items():
        setattr(db_product, key, value)
    
    db.commit()
    db.refresh(db_product)
    return db_product

@app.delete("/products/{product_id}")
async def delete_product(product_id: str, db: Session = Depends(get_db)):
    product = db.query(ProductDB).filter(ProductDB.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}