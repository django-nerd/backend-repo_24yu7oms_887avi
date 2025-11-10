"""
Database Schemas for Food Ordering App

Each Pydantic model represents a collection in MongoDB. The collection name is the lowercase of the class name.
"""

from pydantic import BaseModel, Field
from typing import Optional, List

class Restaurant(BaseModel):
    name: str = Field(..., description="Restaurant name")
    cuisine: str = Field(..., description="Cuisine type")
    rating: float = Field(4.5, ge=0, le=5, description="Average rating")
    delivery_fee: float = Field(1.99, ge=0, description="Delivery fee in USD")
    image: Optional[str] = Field(None, description="Cover image URL")

class Menuitem(BaseModel):
    restaurant_id: str = Field(..., description="Restaurant ObjectId as string")
    name: str = Field(...)
    description: Optional[str] = None
    price: float = Field(..., ge=0)
    image: Optional[str] = None

class OrderItem(BaseModel):
    item_id: Optional[str] = None
    restaurant_id: str
    name: str
    price: float
    qty: int = Field(1, ge=1)

class Order(BaseModel):
    email: str = Field(..., description="Customer email to fetch their orders")
    address: str = Field(..., description="Delivery address")
    items: List[OrderItem]
    subtotal: float = 0
    delivery_fee: float = 0
    total: float = 0
    status: str = Field("placed", description="placed|preparing|on the way|delivered")
