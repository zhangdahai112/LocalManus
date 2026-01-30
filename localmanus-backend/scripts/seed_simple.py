"""
Simple database seeding script that bypasses passlib issues.
"""
import os
import sys
from sqlmodel import Session, select
from core.database import engine, create_db_and_tables
from core.models import User

# Simple password hashing without passlib
import hashlib
import base64

def simple_hash(password: str) -> str:
    """Simple SHA-256 hash for demo purposes"""
    salt = "localmanus_salt_2026"
    return base64.b64encode(
        hashlib.sha256((password + salt).encode()).digest()
    ).decode()

def seed_users():
    # Create tables if they don't exist
    create_db_and_tables()
    
    # Sample users
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
            
            # Create new user with simple hash
            hashed_pw = simple_hash(user_data["password"])
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
        print("\nUsers created:")
        print("- admin / admin123")
        print("- testuser / test123")

if __name__ == "__main__":
    seed_users()