from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


class OrderBase(BaseModel):
    user_id: int
    status: str
    order_date: datetime
    delivery_date: Optional[datetime]
    total_amount: float

    @field_validator("status")
    @classmethod
    def validate_status(cls, value):
        """
        Валидатор для статуса заказа.
        Проверяет, что статус является допустимым значением.
        """
        allowed_statuses = [
            "Pending", "Completed", "Canceled", "Processing",
            "Shipped", "Delivered", "Returned", "Failed"
        ]
        if value not in allowed_statuses:
            raise ValueError(
                f"Invalid status: '{value}'. Allowed values are: {', '.join(allowed_statuses)}"
            )
        return value

    @field_validator("delivery_date", mode="before")
    @classmethod
    def validate_delivery_date(cls, value, info):
        """
        Валидатор для даты доставки.
        Убедитесь, что дата доставки после даты заказа.
        """
        order_date = info.data["order_date"]
        if value:
            if order_date and value < order_date:
                raise ValueError("Delivery date cannot be earlier than the order date.")
        return value

    @field_validator("order_date", mode="before")
    @classmethod
    def validate_order_date(cls, value):
        """
        Валидатор для даты заказа.
        Убедитесь, что дата заказа не находится в будущем.
        """
        if value > datetime.now():
            raise ValueError("Order date cannot be in the future.")
        return value

    @field_validator("total_amount")
    @classmethod
    def validate_total_amount(cls, value):
        """
        Валидатор для общей суммы заказа.
        Убедитесь, что сумма заказа не отрицательна.
        """
        if value < 0:
            raise ValueError("Total amount cannot be negative.")
        return value


class OrderCreate(OrderBase):
    pass


class OrderRead(OrderBase):
    order_id: int
    order_date: datetime
    total_amount: float

    class Config:
        from_attributes = True


class OrderDetailBase(BaseModel):
    product_id: int
    quantity: int
    price_per_unit: float
    total_price: float


class OrderDetailCreate(OrderDetailBase):
    pass


class OrderDetailRead(OrderDetailBase):
    order_detail_id: int

    class Config:
        from_attributes = True
