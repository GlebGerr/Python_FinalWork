from pydantic import BaseModel, EmailStr, constr, field_validator
from datetime import datetime
import re


class UserBase(BaseModel):
    first_name: constr(max_length=50)
    last_name: constr(max_length=50)
    email: EmailStr
    phone: constr(max_length=20)
    loyalty_status: str

    @field_validator("loyalty_status")
    def validate_loyalty_status(cls, value):
        pattern = re.compile(r"^(Gold|Silver|Bronze)$")
        if not pattern.match(value):
            raise ValueError("Loyalty status must be 'Gold', 'Silver', or 'Bronze'")
        return value


class UserCreate(UserBase):
    pass


class UserRead(UserBase):
    user_id: int
    registration_date: datetime

    class Config:
        from_attributes = True
