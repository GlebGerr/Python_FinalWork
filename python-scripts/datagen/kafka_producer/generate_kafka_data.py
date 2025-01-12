import time
import json
import random
import logging
from kafka import KafkaProducer
from sqlalchemy import create_engine, text
from faker import Faker
import os
import re


def clean_phone_number(phone: str) -> str:
    """Очищает номер телефона от лишних символов и ограничивает его длину до 20 символов."""
    return re.sub(r"[^\d+]", "", phone)[:20]


def create_user_data(fake: Faker) -> dict:
    """
    Генерирует случайные данные пользователя в формате JSON.

    Args:
        fake (Faker): Экземпляр Faker для генерации случайных данных.

    Returns:
        dict: Сгенерированные данные пользователя.
    """
    return {
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.email(),
        "phone": clean_phone_number(fake.phone_number()),
        "registration_date": fake.date_time_between(start_date='-1y', end_date='now').isoformat(),
        "loyalty_status": random.choice(["Gold", "Silver", "Bronze"])
    }


def create_review_data(fake: Faker, users: list, products: list) -> dict:
    """
    Генерирует случайный отзыв в формате JSON.

    Args:
        fake (Faker): Экземпляр Faker для генерации текста отзыва.
        users (list): Список пользователей.
        products (list): Список продуктов.

    Returns:
        dict: Сгенерированные данные отзыва.
    """
    return {
        "user_id": random.choice(users),
        "product_id": random.choice(products),
        "rating": random.randint(1, 5),
        "review_text": fake.text(max_nb_chars=200),
        "created_at": fake.date_time_between(start_date='-1m', end_date='now').isoformat()
    }


def fetch_data_from_db(db_url: str) -> tuple:
    """
    Извлекает список пользователей и продуктов из PostgreSQL.

    Args:
        db_url (str): Строка подключения к базе данных.

    Returns:
        tuple: Списки пользователей и продуктов.
    """
    schema = os.getenv("POSTGRESQL_APP_SCHEMA", "source")
    engine = create_engine(db_url)

    query_users = f"SET search_path TO {schema}; SELECT user_id FROM users"
    query_products = f"SET search_path TO {schema}; SELECT product_id FROM products"

    with engine.connect() as conn:
        try:
            users = [row[0] for row in conn.execute(text(query_users))]
            products = [row[0] for row in conn.execute(text(query_products))]
        except Exception as e:
            raise ValueError(f"Ошибка при выполнении запросов: {e}")

    return users, products


def get_postgres_connection_string() -> str:
    """Возвращает строку подключения к PostgreSQL на основе переменных окружения."""
    return f"postgresql://{os.getenv('POSTGRESQL_APP_USER', 'db_user')}:" \
           f"{os.getenv('POSTGRESQL_APP_PASSWORD', 'qwerty')}@" \
           f"{os.getenv('POSTGRESQL_APP_HOST', 'postgresql')}:5432/" \
           f"{os.getenv('POSTGRESQL_APP_DB', 'postgres_db')}"


def configure_logging():
    """Конфигурирует логирование."""
    logging.basicConfig(level=logging.INFO)
    return logging.getLogger(__name__)


def main():
    """Главная функция для генерации и отправки данных в Kafka."""
    logger = configure_logging()

    kafka_config = {
        "bootstrap_servers": os.getenv("KAFKA_INTERNAL_CONNECT_PATH"),
        "user_topic": os.getenv("KAFKA_USER_TOPIC_NAME"),
        "review_topic": os.getenv("KAFKA_REVIEW_TOPIC_NAME"),
        "msg_gen_period": float(os.getenv("KAFKA_DATAGEN_PERIOD_SECS", "1")),
        "db_url": get_postgres_connection_string()
    }

    try:
        # Подключение к Kafka
        producer = KafkaProducer(
            bootstrap_servers=kafka_config["bootstrap_servers"],
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        fake = Faker()

        # Загрузка данных из базы
        users, products = fetch_data_from_db(kafka_config["db_url"])
        if not users or not products:
            logger.error("Списки пользователей и продуктов пусты. Проверьте базу данных.")
            return

        msg_id = 1

        while True:
            try:
                # Генерация и отправка сообщения пользователя
                user_data = create_user_data(fake)
                producer.send(kafka_config["user_topic"], value=user_data)
                logger.info(f"User message №{msg_id} отправлен: {user_data}")

                # Пауза перед следующей генерацией
                time.sleep(kafka_config["msg_gen_period"])
                msg_id += 1

                # Генерация и отправка сообщения отзыва
                review_data = create_review_data(fake, users, products)
                producer.send(kafka_config["review_topic"], value=review_data)
                logger.info(f"Review message №{msg_id} отправлен: {review_data}")

                # Пауза перед следующей генерацией
                time.sleep(kafka_config["msg_gen_period"])
                msg_id += 1

            except Exception as e:
                logger.error(f"Ошибка при генерации или отправке сообщения: {e}")
                time.sleep(kafka_config["msg_gen_period"])

    except Exception as e:
        logger.error(f"Ошибка подключения: {e}")


if __name__ == "__main__":
    main()