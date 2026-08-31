from app.core.database import SessionLocal
from app.core.models import User
from app.core.security import get_password_hash
from sqlalchemy.exc import IntegrityError

def seed_users():
    db = SessionLocal()
    users_to_create = [
        {"username": "test1", "email": "test1@gmail.com", "password": "test1"},
        {"username": "test2", "email": "test2@gmail.com", "password": "test2"},
        {"username": "test3", "email": "test3@gmail.com", "password": "test3"},
    ]

    for u in users_to_create:
        if not db.query(User).filter_by(email=u["email"]).first():
            user = User(
                username=u["username"],
                email=u["email"],
                hashed_password=get_password_hash(u["password"]),
            )
            db.add(user)
            try:
                db.commit()
                print(f"✅ Created user: {u['username']}")
            except IntegrityError:
                db.rollback()
                print(f"⚠️  Skipped duplicate: {u['email']}")
    db.close()

if __name__ == "__main__":
    seed_users()