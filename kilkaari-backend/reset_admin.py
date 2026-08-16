"""
reset_admin.py — updates the existing admin account's email/password to
match whatever is currently in .env (FIRST_ADMIN_EMAIL / FIRST_ADMIN_PASSWORD),
without touching any other data in the database. Use this instead of deleting
the database when you just want to change admin credentials.

Usage:
    python reset_admin.py
"""

from app.auth import hash_password
from app.config import settings
from app.database import SessionLocal
from app.models import User, UserRole


def run():
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.role == UserRole.admin).first()
        if not admin:
            print("No admin account found. Just run `python run.py` — it will create one automatically from .env.")
            return

        old_email = admin.email
        admin.email = settings.first_admin_email
        admin.full_name = settings.first_admin_name
        admin.hashed_password = hash_password(settings.first_admin_password)
        admin.is_active = True
        db.commit()

        print(f"Updated admin account: {old_email} -> {settings.first_admin_email}")
        print("You can now log in with the credentials currently in your .env file.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
