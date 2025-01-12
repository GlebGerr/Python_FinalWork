from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class ReviewBase(BaseModel):
    user_id: int
    product_id: int
    rating: int = Field(ge=1, le=5)  # Рейтинг от 1 до 5
    review_text: Optional[str]

class ReviewCreate(ReviewBase):
    pass

class ReviewRead(ReviewBase):
    review_id: int
    created_at: datetime

    class Config:
        from_attributes = True
