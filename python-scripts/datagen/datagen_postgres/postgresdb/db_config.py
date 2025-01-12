import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

## Получение переменных окружения с помощью os.environ
POSTGRESQL_APP_HOST = os.getenv("POSTGRESQL_APP_HOST")
POSTGRESQL_APP_DB = os.getenv("POSTGRESQL_APP_DB")
POSTGRESQL_APP_USER = os.getenv("POSTGRESQL_APP_USER")
POSTGRESQL_APP_PASSWORD = os.getenv("POSTGRESQL_APP_PASSWORD")
POSTGRESQL_APP_SCHEMA = os.getenv("POSTGRESQL_APP_SCHEMA")

# Создание строки подключения
DATABASE_URL = (
    f"postgresql://{POSTGRESQL_APP_USER}:{POSTGRESQL_APP_PASSWORD}@{POSTGRESQL_APP_HOST}/{POSTGRESQL_APP_DB}"
    f"?options=-c%20search_path={POSTGRESQL_APP_SCHEMA}"
)

# Создаем движок SQLAlchemy
engine = create_engine(DATABASE_URL)

# Создаем фабрику сессий
Session = sessionmaker(bind=engine)

# Экспортируем сессию и движок
def get_session():
    return Session()
