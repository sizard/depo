from models import User
from database import session_scope

def check_database():
    with session_scope() as session:
        # Check users table
        users = session.query(User).all()
        print(f"\nFound {len(users)} users:")
        for user in users:
            print(f"- ID: {user.id}, Name: {user.full_name}, Role: {user.role}")

if __name__ == "__main__":
    check_database()
