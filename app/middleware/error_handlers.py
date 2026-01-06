from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException


# ==============================
# Request Validation Error Handler
# ==============================
def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    error_messages = [
        {
            "path": ".".join(map(str, error["loc"][1:])) or "body",
            "message": error["msg"],
        }
        for error in exc.errors()
    ]

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "statusCode": 422,
            "message": "Validation Error",
            "errorMessages": error_messages,
        },
    )


# ==============================
# Database Integrity Error Handler
# ==============================
def integrity_error_handler(request: Request, exc: IntegrityError):
    """Handle database integrity errors"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "statusCode": 400,
            "message": "Database integrity error",
            "errorMessages": [
                {
                    "path": "database",
                    "message": str(exc.orig) if exc.orig else "Integrity constraint violated",
                }
            ],
        },
    )


# ==============================
# HTTP Exception Handler
# ==============================
def http_exception_handler(request: Request, exc: HTTPException):
    """Handle custom HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "statusCode": exc.status_code,
            "message": exc.detail if isinstance(exc.detail, str) else "Request error",
            "errorMessages": [
                {
                    "path": request.url.path,
                    "message": exc.detail,
                }
            ],
        },
    )


# ==============================
# SQLAlchemy Error Handler
# ==============================
def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle SQLAlchemy errors"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "statusCode": 500,
            "message": "Database error",
            "errorMessages": [
                {
                    "path": "database",
                    "message": "Database operation failed",
                }
            ],
        },
    )


# ==============================
# 404 Handler
# ==============================
def not_found_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle 404 errors"""
    if exc.status_code == 404:
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "statusCode": 404,
                "message": "API not found",
                "errorMessages": [
                    {
                        "path": request.url.path,
                        "message": "Invalid URL or route",
                    }
                ],
            },
        )

    # fallback to normal HTTP exception handler
    return http_exception_handler(request, exc)


# ==============================
# Global Exception Handler
# ==============================
def global_exception_handler(request: Request, exc: Exception):
    """Handle any other exceptions"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "statusCode": 500,
            "message": "Something went wrong",
            "errorMessages": [
                {
                    "path": request.url.path,
                    "message": str(exc),
                }
            ],
        },
    )


# ==============================
# Register All Error Handlers
# ==============================
def register_error_handlers(app):
    """Register all error handlers with the FastAPI app"""

    # Validation errors
    app.exception_handler(RequestValidationError)(validation_exception_handler)

    # Database errors
    app.exception_handler(IntegrityError)(integrity_error_handler)
    app.exception_handler(SQLAlchemyError)(sqlalchemy_exception_handler)

    # HTTP exceptions
    app.exception_handler(HTTPException)(http_exception_handler)

    # 404 handler
    app.exception_handler(StarletteHTTPException)(not_found_exception_handler)

    # Global exception handler (must be last)
    app.exception_handler(Exception)(global_exception_handler)
