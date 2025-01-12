from pydantic import BaseModel
from datetime import datetime

class LoyaltyPointBase(BaseModel):
    user_id: int
    points: int
    reason: str

class LoyaltyPointCreate(LoyaltyPointBase):
    pass

class LoyaltyPointRead(LoyaltyPointBase):
    loyalty_id: int
    created_at: datetime

    class Config:
        from_attributes = True
