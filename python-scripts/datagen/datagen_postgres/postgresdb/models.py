from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, CheckConstraint, Text, Float
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

# Модель пользователей
class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20))
    registration_date = Column(DateTime, default=datetime.now)
    loyalty_status = Column(String(20), CheckConstraint("loyalty_status IN ('Gold', 'Silver', 'Bronze')"), nullable=False)

    # Связь с заказами
    orders = relationship("Order", back_populates="user")
    # Связь с отзывами
    reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")
    # Связь с бонусами
    loyalty_points = relationship("LoyaltyPoint", back_populates="user", cascade="all, delete-orphan")


# Модель категорий товаров
class ProductCategory(Base):
    __tablename__ = 'productcategories'

    category_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    parent_category_id = Column(Integer, ForeignKey('productcategories.category_id'))

    # Связь с дочерними категориями
    subcategories = relationship("ProductCategory", backref="parent", remote_side=[category_id])
    products = relationship("Product", back_populates="category")


# Модель товаров
class Product(Base):
    __tablename__ = 'products'

    product_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    category_id = Column(Integer, ForeignKey('productcategories.category_id'))
    price = Column(Numeric(10, 2), nullable=False)
    stock_quantity = Column(Integer, default=0)
    creation_date = Column(DateTime, default=datetime.now)

    # Связь с категорией
    category = relationship("ProductCategory", back_populates="products")
    # Связь с деталями заказа
    order_details = relationship("OrderDetail", back_populates="product")
    # Связь с отзывами
    reviews = relationship("Review", back_populates="product", cascade="all, delete-orphan")

# Модель заказов
class Order(Base):
    __tablename__ = "orders"

    order_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    order_date = Column(DateTime, nullable=False)
    total_amount = Column(Float, nullable=True)
    status = Column(String, nullable=False)
    delivery_date = Column(DateTime, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('Pending', 'Completed', 'Canceled', 'Processing', 'Shipped', 'Delivered', 'Returned', 'Failed')",
            name="orders_status_check"
        ),
    )

    user = relationship("User", back_populates="orders")
    order_details = relationship("OrderDetail", back_populates="order")


# Модель деталей заказа
class OrderDetail(Base):
    __tablename__ = "orderdetails"

    order_detail_id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price_per_unit = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)

    order = relationship("Order", back_populates="order_details")
    product = relationship("Product")

# Модель отзыва о продукте
class Review(Base):
    __tablename__ = "reviews"

    review_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.product_id", ondelete="CASCADE"), nullable=False)
    rating = Column(Integer, nullable=False)  # Рейтинг от 1 до 5
    review_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="reviews")
    product = relationship("Product", back_populates="reviews")

# Модель бонусных баллов
class LoyaltyPoint(Base):
    __tablename__ = "loyaltypoints"

    loyalty_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    points = Column(Integer, nullable=False)
    reason = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="loyalty_points")