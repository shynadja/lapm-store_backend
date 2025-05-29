from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import uuid
from enum import Enum
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, Float, Integer, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres_password@db:5432/postgres")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class OrderStatus(str, Enum):
    CREATED = "оформлен"
    ASSEMBLED = "собран"
    RECEIVED = "получен"

class DeliveryMethod(str, Enum):
    PICKUP = "самовывоз"

class PaymentMethod(str, Enum):
    CASH_ON_DELIVERY = "при получении"

class OrderDB(Base):
    __tablename__ = "orders"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String)
    total_amount = Column(Float)
    status = Column(SQLEnum(OrderStatus))
    delivery_method = Column(SQLEnum(DeliveryMethod))
    payment_method = Column(SQLEnum(PaymentMethod))
    created_at = Column(DateTime, default=datetime.utcnow)
    items = relationship("OrderItemDB", back_populates="order")

class OrderItemDB(Base):
    __tablename__ = "order_items"
    id = Column(String, primary_key=True, index=True)
    order_id = Column(String, ForeignKey("orders.id"))
    product_id = Column(String)
    quantity = Column(Integer)
    price = Column(Float)
    order = relationship("OrderDB", back_populates="items")

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class OrderItem(BaseModel):
    product_id: str
    quantity: int
    price: float

    class Config:
        orm_mode = True

class OrderCreate(BaseModel):
    user_id: str
    items: List[OrderItem]
    delivery_method: DeliveryMethod = DeliveryMethod.PICKUP
    payment_method: PaymentMethod = PaymentMethod.CASH_ON_DELIVERY

class Order(BaseModel):
    id: str
    user_id: str
    total_amount: float
    status: OrderStatus
    delivery_method: str
    payment_method: str
    created_at: datetime
    items: List[OrderItem]

    class Config:
        orm_mode = True

class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    items: Optional[List[OrderItem]] = None

@app.get("/orders", response_model=List[Order])
async def get_orders(db: Session = Depends(get_db)):
    orders = db.query(OrderDB).all()
    return orders

@app.get("/orders/{order_id}", response_model=Order)
async def get_order(order_id: str, db: Session = Depends(get_db)):
    order = db.query(OrderDB).filter(OrderDB.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.post("/orders", response_model=Order)
async def create_order(order_data: OrderCreate, db: Session = Depends(get_db)):
    total_amount = sum(item.price * item.quantity for item in order_data.items)
    
    db_order = OrderDB(
        id=str(uuid.uuid4()),
        user_id=order_data.user_id,
        total_amount=total_amount,
        status=OrderStatus.CREATED,
        delivery_method=order_data.delivery_method,
        payment_method=order_data.payment_method,
        created_at=datetime.utcnow()
    )
    
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    for item in order_data.items:
        db_item = OrderItemDB(
            id=str(uuid.uuid4()),
            order_id=db_order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price=item.price
        )
        db.add(db_item)
    
    db.commit()
    db.refresh(db_order)
    return db_order

@app.put("/orders/{order_id}", response_model=Order)
async def update_order(order_id: str, order_update: OrderUpdate, db: Session = Depends(get_db)):
    db_order = db.query(OrderDB).filter(OrderDB.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order_update.status:
        db_order.status = order_update.status
    
    if order_update.items:
        # Delete existing items
        db.query(OrderItemDB).filter(OrderItemDB.order_id == order_id).delete()
        
        # Add new items
        total_amount = 0
        for item in order_update.items:
            db_item = OrderItemDB(
                id=str(uuid.uuid4()),
                order_id=order_id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=item.price
            )
            db.add(db_item)
            total_amount += item.price * item.quantity
        
        db_order.total_amount = total_amount
    
    db.commit()
    db.refresh(db_order)
    return db_order