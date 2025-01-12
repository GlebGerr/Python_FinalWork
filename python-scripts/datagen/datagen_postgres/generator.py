import os
import random
import re
from datetime import timedelta
from faker import Faker
from postgresdb.models import User, ProductCategory, Product, Order, OrderDetail, Review, LoyaltyPoint
from postgresdb_schemas import (
    LoyaltyPointCreate,
    ReviewCreate,
    UserCreate,
    CategoryCreate,
    ProductCreate,
    OrderCreate,
    OrderDetailCreate
)
from postgresdb.db_config import get_session
from sqlalchemy.orm import Session
from sqlalchemy import text

def clean_phone(phone: str) -> str:
    """Очистка телефонного номера от лишних символов и обрезка до 20 символов"""
    return re.sub(r"[^\d+]", "", phone)[:20]

def add_records_to_session(session, model_class, schema_class, data):
    """Добавление записей в сессию"""
    try:
        schema = schema_class(**data)
        instance = model_class(**schema.model_dump())
        session.add(instance)
        session.flush()
        return instance
    except Exception as e:
        print(f"Ошибка при добавлении записи {model_class.__name__}: {e}")
        session.rollback()

def generate_users(session: Session, fake, num_users: int):
    """Генерация пользователей"""
    print("Генерация пользователей...")
    generated_emails = set()
    user_registration_dates = {}

    for _ in range(num_users):
        email = fake.unique.email()
        registration_date = fake.date_time_between(start_date='-1y', end_date='now')

        user_data = {
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": email,
            "phone": clean_phone(fake.phone_number()),
            "registration_date": registration_date,
            "loyalty_status": random.choice(['Gold', 'Silver', 'Bronze']),
        }

        user = add_records_to_session(session, User, UserCreate, user_data)
        user_registration_dates[user.user_id] = registration_date

    session.commit()
    return user_registration_dates

def generate_categories(session: Session, fake, expanded_categories):
    """Генерация категорий товаров"""
    print("Генерация категорий товаров...")
    category_ids = {}

    for group, subcategories in expanded_categories.items():
        group_data = {"name": group, "parent_category_id": None}
        group_category = add_records_to_session(session, ProductCategory, CategoryCreate, group_data)

        subcategory_ids = []
        for subcategory in subcategories:
            subcategory_data = {"name": subcategory, "parent_category_id": group_category.category_id}
            subcategory_instance = add_records_to_session(session, ProductCategory, CategoryCreate, subcategory_data)
            subcategory_ids.append(subcategory_instance.category_id)

        category_ids[group] = {"group_id": group_category.category_id, "subcategories": subcategory_ids}

    session.commit()
    return category_ids

def generate_products(session: Session, fake, num_products: int, category_ids: dict):
    """Генерация товаров"""
    print("Генерация товаров...")
    for _ in range(num_products):
        group = random.choice(list(category_ids.keys()))
        subcategory_id = random.choice(category_ids[group]["subcategories"])
        product_data = {
            "name": fake.word(),
            "description": fake.text(max_nb_chars=200),
            "category_id": subcategory_id,
            "price": round(random.uniform(10, 1000), 2),
            "stock_quantity": random.randint(0, 100),
        }
        add_records_to_session(session, Product, ProductCreate, product_data)

    session.commit()

def generate_orders(session: Session, fake, num_orders: int, user_ids, product_ids, user_registration_dates, num_order_details_min, num_order_details_max):
    """Генерация заказов и деталей заказов"""
    print("Генерация заказов...")
    order_statuses = ["Pending", "Completed", "Canceled", "Processing", "Shipped", "Delivered", "Returned", "Failed"]

    for _ in range(num_orders):
        user_id = random.choice(user_ids)
        registration_date = user_registration_dates[user_id]

        order_date = fake.date_time_between(start_date=registration_date, end_date='now')
        delivery_date = fake.date_time_between(start_date=order_date, end_date=order_date + timedelta(days=30))

        total_amount = 0
        order_details = []

        for _ in range(random.randint(num_order_details_min, num_order_details_max)):
            product_id = random.choice(product_ids)
            quantity = random.randint(1, 5)
            price_per_unit = round(random.uniform(10, 1000), 2)
            total_price = quantity * price_per_unit
            total_amount += total_price

            order_details.append({
                "product_id": product_id,
                "quantity": quantity,
                "price_per_unit": price_per_unit,
                "total_price": round(total_price, 2),
            })

        order_data = {
            "user_id": user_id,
            "order_date": order_date,
            "status": random.choice(order_statuses),
            "delivery_date": delivery_date,
            "total_amount": round(total_amount, 2),
        }

        order = add_records_to_session(session, Order, OrderCreate, order_data)

        for detail in order_details:
            order_detail_schema = OrderDetailCreate(**detail)
            order_detail = OrderDetail(order_id=order.order_id, **order_detail_schema.model_dump())
            session.add(order_detail)

    session.commit()

def generate_reviews(session: Session, fake, num_reviews: int, user_ids, product_ids):
    """Генерация отзывов"""
    print("Генерация отзывов...")
    for _ in range(num_reviews):
        user_id = random.choice(user_ids)
        product_id = random.choice(product_ids)
        review_data = {
            "user_id": user_id,
            "product_id": product_id,
            "rating": random.randint(1, 5),
            "review_text": fake.text(max_nb_chars=200)
        }
        add_records_to_session(session, Review, ReviewCreate, review_data)

    session.commit()

def generate_loyalty_points(session: Session, fake, num_loyalty_points, user_ids):
    """Генерация бонусных баллов"""
    print("Генерация бонусных баллов...")
    for _ in range(num_loyalty_points):
        user_id = random.choice(user_ids)
        loyalty_data = {
            "user_id": user_id,
            "points": random.randint(10, 500),
            "reason": random.choice(["Order", "Promotion", "Event Participation"])
        }
        add_records_to_session(session, LoyaltyPoint, LoyaltyPointCreate, loyalty_data)

    session.commit()

def generate_data():
    """Основная функция для генерации всех данных"""
    fake = Faker()
    session: Session = get_session()

    num_users = int(os.getenv('PG_DATAGEN_NUM_USERS', 500))
    num_products = int(os.getenv('PG_DATAGEN_NUM_PRODUCTS', 800))
    num_orders = int(os.getenv('PG_DATAGEN_NUM_ORDERS', 3000))
    num_order_details_min = int(os.getenv('PG_DATAGEN_NUM_ORDER_DETAILS_MIN', 1))
    num_order_details_max = int(os.getenv('PG_DATAGEN_NUM_ORDER_DETAILS_MAX', 10))
    num_reviews = int(os.getenv('PG_DATAGEN_NUM_REVIEWS', 2000))
    num_loyalty_points = int(os.getenv('PG_DATAGEN_NUM_LOYALTY_POINTS', 3000))

    try:
        user_registration_dates = generate_users(session, fake, num_users)
        expanded_categories = {
            "Electronics": ["Smartphones", "Laptops", "Tablets", "Audio", "Televisions", "Smart Devices", "Cameras"],
            "Books": ["Fiction", "Non-Fiction", "Children’s Books", "Educational", "Comics & Graphic Novels", "Cookbooks"],
            "Clothing": ["Men's Clothing", "Women's Clothing", "Children's Clothing", "Sportswear", "Accessories"],
            "Home Appliances": ["Kitchen Appliances", "Cleaning Appliances", "Heating & Cooling"],
            "Toys": ["Action Figures", "Educational Toys", "Board Games", "Dolls", "Puzzles"],
        }
        category_ids = generate_categories(session, fake, expanded_categories)
        generate_products(session, fake, num_products, category_ids)
        
        user_ids = [row[0] for row in session.execute(text("SELECT user_id FROM users")).fetchall()]
        product_ids = [row[0] for row in session.execute(text("SELECT product_id FROM products")).fetchall()]

        generate_orders(session, fake, num_orders, user_ids, product_ids, user_registration_dates, num_order_details_min, num_order_details_max)
        generate_reviews(session, fake, num_reviews, user_ids, product_ids)
        generate_loyalty_points(session, fake, num_loyalty_points, user_ids)

        print("Данные успешно сгенерированы!")

    except Exception as e:
        print(f"Ошибка генерации данных: {e}")
        session.rollback()
    finally:
        session.close()