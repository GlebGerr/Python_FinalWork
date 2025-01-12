from postgresdb.models import Base
from postgresdb.db_config import engine
from generator import generate_data

if __name__ == "__main__":
    # Создание схемы базы данных
    Base.metadata.create_all(engine)
    print("Схема базы данных создана.")

    # Генерация данных
    generate_data()
