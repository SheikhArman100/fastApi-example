This planning document outlines the architecture and execution steps for your FastAPI project. We will follow a Service-Repository pattern to keep business logic (like file saving) separate from the API routes.
1. Project Package & Dependencies
Create a requirements.txt to manage your environment:
fastapi: Framework.
uvicorn[standard]: ASGI server.
sqlalchemy: ORM.
pymysql: MySQL driver.
pydantic[email]: Data validation.
python-multipart: Required for handling file uploads.
passlib[bcrypt]: For password hashing.
python-jose[cryptography]: For JWT token handling.
alembic: For database migrations.
python-dotenv: Environment variable management.
2. Folder Structure (Best Practice)
code
Text
app/
├── __init__.py
├── main.py                 # Entry point
├── core/                   # Global configuration
│   ├── config.py           # Environment variables
│   └── security.py         # Hashing & JWT logic
├── db/                     # Database connection
│   ├── session.py          # Engine & SessionLocal
│   └── base.py             # Import all models here for Alembic
├── models/                 # SQLAlchemy Models (DB Tables)
│   ├── user.py
│   └── file.py
├── schemas/                # Pydantic Models (Validation)
│   ├── user.py
│   ├── file.py
│   └── token.py
├── api/                    # API Endpoints
│   ├── deps.py             # Dependencies (get_db, get_current_admin)
│   └── v1/
│       └── auth.py         # Register/Login routes
├── services/               # Business Logic
│   ├── user_service.py
│   └── file_service.py     # Logic for saving files to disk
└── utils/                  # Helper functions
├── migrations/             # Alembic migration files
├── uploads/                # Local storage for profile images
├── .env                    # Secrets (DB URL, Secret Key)
├── alembic.ini
└── requirements.txt
3. Comprehensive Tasklist
Phase 1: Environment & Database Setup

- [x] Initialize git and create a virtual environment.
- [x] Install dependencies from requirements.txt.
- [x] Create .env and configure DATABASE_URL (MySQL).
- [x] Setup SQLAlchemy session.py and Base class.
- [x] Model Definition: Create File model (id, path, type, names). Create User model with relationships and Enum for roles.
- [x] Initialize Alembic and run the first migration to create tables in MySQL.

Phase 2: Security & Utility Foundation

- [x] Implement password hashing and verification logic in core/security.py.
- [x] Create a dependency get_db to handle database session lifecycles.
- [x] Create a "Stub" dependency for get_current_admin (to be fully implemented once Login is ready, but required for your Phase 1 requirement).

Phase 3: File Service (The Multipart Logic)

- [x] Create file_service.py logic: Generate unique filenames (UUID). Save bytes to the uploads/ folder. Insert record into the files table and return the ID.

Phase 4: Registration API (The Request Phase)

- [x] Define Pydantic schemas for User Response (don't return passwords).
- [x] Implementation of POST /auth/register: Set route to accept Multipart/form-data. Add logic to check if Email already exists. Call File Service to save the profile_image. Create User record with the file_id link. Link createdBy and updatedBy fields.

Phase 5: Refinement & Testing

- [x] Implement global error handling (Try/Except blocks for DB errors).
- [x] Verify file folder permissions.
- [x] Test via FastAPI Swagger Docs (/docs).
4. Database Schema Design details
To ensure we match your requirements exactly:
User Table:
id: Int (PK)
name: String
email: String (Unique, Indexed)
password: String (Hashed)
isActive: Boolean (Default: True)
role: Enum ("admin", "user")
profileImageId: Int (FK -> File.id)
createdBy: Int (Self-referencing FK, Nullable)
updatedBy: Int (Self-referencing FK, Nullable)
createdAt: DateTime
updatedAt: DateTime
File Table:
id: Int (PK)
path: String (Physical path on server)
type: String (MIME type e.g., image/jpeg)
originalName: String
modifiedName: String (Unique UUID name)
