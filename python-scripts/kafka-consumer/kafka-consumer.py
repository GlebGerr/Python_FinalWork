import json
import os
import logging
from kafka import KafkaConsumer
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_postgres_connection_url():
    """
    Формирует строку подключения к PostgreSQL на основе переменных окружения.
    """
    user = os.getenv("POSTGRESQL_APP_USER", "db_user")
    password = os.getenv("POSTGRESQL_APP_PASSWORD", "qwerty")
    host = os.getenv("POSTGRESQL_APP_HOST", "postgresql")
    db = os.getenv("POSTGRESQL_APP_DB", "postgres_db")
    return f"postgresql://{user}:{password}@{host}:5432/{db}"

def initialize_session(engine, schema):
    """
    Создаёт новую сессию и устанавливает схему по умолчанию.

    Args:
        engine: SQLAlchemy Engine для подключения к базе данных.
        schema (str): Имя схемы для установки.

    Returns:
        session: SQLAlchemy Session с установленной схемой.
    """
    Session = sessionmaker(bind=engine)
    session = Session()
    session.execute(text(f"SET search_path TO {schema}"))
    logger.info(f"Установлен search_path: {schema}")
    return session

def process_user_message(user_msg, session):
    """
    Обрабатывает сообщение пользователя и добавляет его в базу данных.

    Args:
        user_msg (dict): Сообщение о пользователе из Kafka.
        session: Сессия базы данных.
    """
    logger.info(f"Обработка пользователя: {user_msg}")
    try:
        # Проверка на существование пользователя
        query_check = text("""
            SELECT 1 FROM users WHERE email = :email LIMIT 1
        """)
        result = session.execute(query_check, {"email": user_msg["email"]}).fetchone()

        if not result:
            # Добавление нового пользователя
            query_insert = text("""
                INSERT INTO users (first_name, last_name, email, phone, registration_date, loyalty_status)
                VALUES (:first_name, :last_name, :email, :phone, :registration_date, :loyalty_status)
            """)
            session.execute(query_insert, user_msg)
            session.commit()
            logger.info(f"Пользователь {user_msg['email']} добавлен.")
        else:
            logger.info(f"Пользователь {user_msg['email']} уже существует.")
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Ошибка при обработке пользователя: {e}")

def process_review_message(review_msg, session):
    """
    Обрабатывает сообщение отзыва и добавляет его в базу данных.

    Args:
        review_msg (dict): Сообщение об отзыве из Kafka.
        session: Сессия базы данных.
    """
    logger.info(f"Обработка отзыва: {review_msg}")
    try:
        # Добавление нового отзыва
        query_insert = text("""
            INSERT INTO reviews (user_id, product_id, rating, review_text, created_at)
            VALUES (:user_id, :product_id, :rating, :review_text, :created_at)
        """)
        session.execute(query_insert, review_msg)
        session.commit()
        logger.info(f"Отзыв добавлен.")
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Ошибка при обработке отзыва: {e}")

def consume_messages(consumer, session, schema):
    """
    Непрерывно обрабатывает сообщения из Kafka.

    Args:
        consumer: KafkaConsumer для прослушивания топиков.
        session: Сессия базы данных.
        schema (str): Имя схемы базы данных.
    """
    logger.info("Начало прослушивания сообщений Kafka.")
    while True:
        try:
            for message in consumer:
                if message.topic == os.getenv("KAFKA_USER_TOPIC_NAME"):
                    process_user_message(message.value, session)
                elif message.topic == os.getenv("KAFKA_REVIEW_TOPIC_NAME"):
                    process_review_message(message.value, session)
                else:
                    logger.warning(f"Сообщение из неизвестного топика: {message.topic}")
        except SQLAlchemyError as db_error:
            logger.error(f"Ошибка базы данных: {db_error}")
            session.rollback()
        except Exception as e:
            logger.error(f"Общая ошибка: {e}")

def main():
    # Конфигурации Kafka
    kafka_bootstrap_servers = os.getenv("KAFKA_INTERNAL_CONNECT_PATH")
    kafka_user_topic = os.getenv("KAFKA_USER_TOPIC_NAME")
    kafka_review_topic = os.getenv("KAFKA_REVIEW_TOPIC_NAME")
    db_url = get_postgres_connection_url()
    schema = os.getenv("POSTGRESQL_APP_SCHEMA", "source")  # Имя схемы базы данных

    # Инициализация базы данных
    engine = create_engine(db_url)

    # Инициализация Kafka Consumer
    consumer = KafkaConsumer(
        kafka_user_topic,
        kafka_review_topic,
        bootstrap_servers=kafka_bootstrap_servers,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='kafka_consumer_group'
    )

    while True:
        session = initialize_session(engine, schema)
        try:
            consume_messages(consumer, session, schema)
        except Exception as e:
            logger.error(f"Ошибка в основном процессе: {e}")
        finally:
            session.close()

if __name__ == "__main__":
    main()
