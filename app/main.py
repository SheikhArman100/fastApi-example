from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import text
import logging

# import routers
from .api.v1.auth import router as auth_router

# import middleware
from .middleware.error_handlers import register_error_handlers

# import response utilities
from .schemas.response import create_response

# import database
from .db.session import SessionLocal

app = FastAPI(
    title="FastAPI App",
    version="1.0.0",
)

# ==============================
# Database Connection Check
# ==============================
@app.on_event("startup")
async def check_database_connection():
    """Check database connection on startup"""
    try:
        db = SessionLocal()
        # Test connection with a simple query
        db.execute(text("SELECT 1"))
        db.close()
        print("✅ Database connection successful!")
        logging.info("Database connection verified on startup")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        logging.error(f"Database connection failed on startup: {e}")
        # You might want to exit the application if DB is critical
        # import sys
        # sys.exit(1)

# ==============================
# Routers
# ==============================
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])

# ==============================
# Error Handlers
# ==============================
register_error_handlers(app)


# ==============================
# Health Check
# ==============================
@app.get("/", tags=["health"])
async def root_health_check():
    """Root health check endpoint"""
    return create_response(
        message="FastAPI application is running",
        status_code=200
    )


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return create_response(
        message="FastAPI application is healthy",
        status_code=200
    )


    """User profile - accessible by admin and user roles"""
    return create_response(
        data={
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role.value,
                "is_active": user.is_active
            }
        },
        message="User profile retrieved",
        status_code=200
    )


# ==============================
# Custom Application Error
# ==============================
class AppError(HTTPException):
    def __init__(self, status_code: int, message: str):
        super().__init__(status_code=status_code, detail=message)


# ==============================
# Local Run
# ==============================
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
