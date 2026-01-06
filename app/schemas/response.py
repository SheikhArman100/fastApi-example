from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    """Standardized API response structure"""
    statusCode: int
    success: bool
    message: Optional[str] = None
    meta: Optional[dict] = None
    data: Optional[T] = None

    class Config:
        from_attributes = True


class PaginationMeta(BaseModel):
    """Pagination metadata structure"""
    page: int
    limit: int
    count: int
    total: int
    totalPages: int


def create_response(
    data: T = None,
    message: str = None,
    status_code: int = 200,
    success: bool = True,
    meta: dict = None
) -> ApiResponse[T]:
    """
    Create a standardized API response

    Args:
        data: The response data
        message: Success/error message
        status_code: HTTP status code
        success: Whether the request was successful
        meta: Additional metadata (pagination, etc.)

    Returns:
        Standardized ApiResponse object
    """
    return ApiResponse[T](
        statusCode=status_code,
        success=success,
        message=message,
        meta=meta,
        data=data
    )


def create_paginated_response(
    data: T,
    page: int,
    limit: int,
    count: int,
    total: int,
    message: str = None,
    status_code: int = 200
) -> ApiResponse[T]:
    """
    Create a paginated API response

    Args:
        data: The paginated data
        page: Current page number
        limit: Items per page
        count: Number of items in current page
        total: Total number of items
        message: Success message
        status_code: HTTP status code

    Returns:
        Standardized ApiResponse with pagination meta
    """
    total_pages = (total + limit - 1) // limit  # Ceiling division

    meta = PaginationMeta(
        page=page,
        limit=limit,
        count=count,
        total=total,
        totalPages=total_pages
    )

    return create_response(
        data=data,
        message=message,
        status_code=status_code,
        success=True,
        meta=meta.dict()
    )
