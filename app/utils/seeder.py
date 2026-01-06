import sys
import os
from sqlalchemy.orm import Session

# Add the project root to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.db.session import SessionLocal
# Import both models to avoid circular import issues
from app.models.user import User, Role
from app.models.file import File  # Import File model too
from app.core.security import hash_password


def seed_admin_users():
    """Seed the database with initial admin users"""

    # Create a database session
    db: Session = SessionLocal()

    try:
        # Check if admin users already exist
        existing_admin = db.query(User).filter(User.role == Role.admin).first()
        if existing_admin:
            print("Admin users already exist. Skipping seeder.")
            return

        # Admin users data
        admin_users_data = [
            {
                "name": "Super Admin",
                "email": "admin@example.com",
                "password": "admin123",
                "role": Role.admin,
                "is_active": True,
            },
            {
                "name": "System Administrator",
                "email": "sysadmin@example.com",
                "password": "sysadmin123",
                "role": Role.admin,
                "is_active": True,
            },
            {
                "name": "John Doe",
                "email": "john@example.com",
                "password": "john123",
                "role": Role.user,
                "is_active": True,
            },
            {
                "name": "Jane Smith",
                "email": "jane@example.com",
                "password": "jane123",
                "role": Role.user,
                "is_active": True,
            },
        ]

        created_users = []

        for user_data in admin_users_data:
            # Check if user already exists
            existing_user = db.query(User).filter(User.email == user_data["email"]).first()
            if existing_user:
                print(f"User {user_data['email']} already exists. Skipping.")
                continue

            # Hash the password
            hashed_password = hash_password(user_data["password"])

            # Create the user
            db_user = User(
                name=user_data["name"],
                email=user_data["email"],
                password=hashed_password,
                role=user_data["role"],
                is_active=user_data["is_active"],
                # created_by and updated_by will be None for seeders
            )

            db.add(db_user)
            db.commit()
            db.refresh(db_user)

            created_users.append({
                "name": db_user.name,
                "email": db_user.email,
                "role": db_user.role.value
            })

            print(f"Created user: {db_user.name} ({db_user.email}) - Role: {db_user.role.value}")

        if created_users:
            print(f"\n✅ Successfully seeded {len(created_users)} users!")
            print("\n📋 Created Users:")
            for user in created_users:
                print(f"  • {user['name']} ({user['email']}) - {user['role']}")

            print("\n⚠️  IMPORTANT: Please change default passwords after first login!")
        else:
            print("No new users were created.")

    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("🌱 FastAPI User Seeder")
    print("=" * 50)
    print("Note: This will only add new users, never delete existing ones.")

    seed_admin_users()

    print("\n" + "=" * 50)
    print("Seeder completed!")
