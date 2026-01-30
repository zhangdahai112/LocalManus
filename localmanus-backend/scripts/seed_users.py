"""
Script to manually insert users into the database.
Run this from the backend directory: python scripts/seed_users.py
"""
from sqlmodel import Session, select
from core.database import engine, create_db_and_tables
from core.models import User
from core.auth import get_password_hash

def seed_users():
    # Create tables if they don't exist
    create_db_and_tables()
    
    # Sample users to insert (shorter passwords to avoid bcrypt 72-byte limit)
    users_data = [
        {
            "username": "admin",
            "email": "admin@example.com",
            "full_name": "Administrator",
            "password": "admin123"
        },
        {
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "test123"
        }
    ]
    
    with Session(engine) as session:
        for user_data in users_data:
            # Check if user already exists
            existing = session.exec(select(User).where(User.username == user_data["username"])).first()
            if existing:
                print(f"User {user_data['username']} already exists, skipping...")
                continue
            
            # Create new user
            hashed_pw = get_password_hash(user_data["password"])
            user = User(
                username=user_data["username"],
                email=user_data["email"],
                full_name=user_data["full_name"],
                hashed_password=hashed_pw
            )
            session.add(user)
            print(f"Created user: {user.username}")
        
        session.commit()
        print("Database seeding completed!")

if __name__ == "__main__":
    seed_users()