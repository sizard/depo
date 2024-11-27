from models import Base
from database import engine

def init_db():
    # Создаем все таблицы
    Base.metadata.create_all(engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_db()
