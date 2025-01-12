from pydantic import BaseModel, constr
from typing import Optional
from datetime import datetime


class ProductBase(BaseModel):
    name: constr(max_length=100)
    description: Optional[str]
    category_id: Optional[int]
    price: float
    stock_quantity: int


class ProductCreate(ProductBase):
    pass


class ProductRead(ProductBase):
    product_id: int
    creation_date: datetime

    class Config:
        from_attributes = True
