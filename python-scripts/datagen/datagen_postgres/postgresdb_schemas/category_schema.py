from pydantic import BaseModel, constr
from typing import Optional, List


class CategoryBase(BaseModel):
    name: constr(max_length=100)
    parent_category_id: Optional[int]


class CategoryCreate(CategoryBase):
    pass


class CategoryRead(CategoryBase):
    category_id: int
    subcategories: List['CategoryRead'] = []

    class Config:
        from_attributes = True
