from models import User, UserRole, Railway, Base
from database import session_scope, engine

def init_db():
    """Инициализация базы данных и создание таблиц"""
    Base.metadata.create_all(engine)
    print("Database tables created successfully!")

def create_admin():
    try:
        with session_scope() as session:
            admin = User(
                id=790424474,  # Ваш Telegram ID
                username="sizard",
                full_name="Admin",
                position="Administrator",
                railway=Railway.YUGO_VOSTOCHNAYA,
                branch="Admin Branch",
                phone="Admin Phone",
                role=UserRole.ADMIN,
                is_active=True,
                is_blocked=False
            )
            session.merge(admin)  # merge вместо add, чтобы избежать конфликтов
            print("Admin created successfully!")
    except Exception as e:
        print(f"Error creating admin: {str(e)}")
        raise

if __name__ == "__main__":
    init_db()  # Сначала создаем таблицы
    create_admin()  # Затем создаем админа
