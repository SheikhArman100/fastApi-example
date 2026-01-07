from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from typing import Optional, Dict, Any, List
from ..models.user import User, Role
from ..schemas.response import create_paginated_response
from ..utils.filtering import apply_search_filter, apply_dynamic_field_filters, calculate_pagination
from ..services.file_service import get_file_by_id

USER_FILTERABLE_FIELDS = ['search_term', 'role', 'email', 'is_active']
USER_SEARCHABLE_FIELDS = ['name', 'email']

class UserFilters:
    """Structured user filters interface"""
    def __init__(
        self,
        search_term: Optional[str] = None,
        role: Optional[str] = None,
        email: Optional[str] = None,
        is_active: Optional[bool] = None
    ):
        self.search_term = search_term
        self.role = role
        self.email = email
        self.is_active = is_active

class PaginationOptions:
    def __init__(
        self,
        page: int = 1,
        limit: int = 10,
        order_by: str = "created_at",
        order_direction: str = "desc"
    ):
        self.page = max(1, page)  # Ensure page is at least 1
        self.limit = max(1, min(100, limit))  # Limit between 1-100
        self.order_by = order_by
        self.order_direction = order_direction
        self.skip = (self.page - 1) * self.limit

def get_all_users(
    db: Session,
    filters: UserFilters,
    pagination: PaginationOptions,
    current_user: User
) -> Dict[str, Any]:
    """
    Get all users with filtering, pagination and search functionality.
    Only admins can access this endpoint.
    """

    # Base query
    query = db.query(User)

    # Apply role-based access control
    if current_user.role != Role.admin:
        # Non-admin users can only see their own profile
        query = query.filter(User.id == current_user.id)

    search_term = filters.search_term
    filters_data = {
        'role': filters.role,
        'email': filters.email,
        'is_active': filters.is_active
    }

    filters_data = {k: v for k, v in filters_data.items() if v is not None and v != ""}

    query = apply_search_filter(
        query=query,
        search_term=search_term,
        searchable_fields=USER_SEARCHABLE_FIELDS,
        model_class=User
    )

    query = apply_dynamic_field_filters(
        query=query,
        filters_data=filters_data,
        filterable_fields=USER_FILTERABLE_FIELDS,
        model_class=User
    )

    # Handle special cases (like enum conversions)
    if filters.role:
        try:
            role_enum = Role(filters.role.lower())
            query = query.filter(User.role == role_enum)
        except ValueError:
            # Invalid role, return empty results
            query = query.filter(User.id == -1)

    # Get total count before pagination
    total_count = query.count()

    # Apply ordering
    order_column = getattr(User, pagination.order_by, User.created_at)
    if pagination.order_direction.lower() == "desc":
        query = query.order_by(order_column.desc())
    else:
        query = query.order_by(order_column.asc())

    # Apply pagination
    users = query.offset(pagination.skip).limit(pagination.limit).all()

    # Calculate pagination metadata
    total_pages = (total_count + pagination.limit - 1) // pagination.limit

    # Format user data (exclude sensitive information)
    user_data = []
    for user in users:
        user_dict = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "is_active": user.is_active,
            "role": user.role.value,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "profile_image_id": user.profile_image_id
        }
        user_data.append(user_dict)

    return {
        "data": user_data,
        "meta": {
            "page": pagination.page,
            "limit": pagination.limit,
            "count": total_count,
            "totalPages": total_pages
        }
    }

def get_user_by_id(db: Session, user_id: int, current_user: User) -> Optional[Dict[str, Any]]:
    """
    Get a single user by ID with authorization checks.
    Only admins can access other users, users can only access themselves.
    """

    # Check authorization
    if current_user.role != Role.admin and current_user.id != user_id:
        return None  # Not authorized to view this user

    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        return None  # User not found

    # Get profile image details if exists
    profile_image = None
    if user.profile_image_id:
        file_record = get_file_by_id(db, user.profile_image_id)
        if file_record:
            profile_image = {
                "id": file_record.id,
                "path": file_record.path,
                "type": file_record.type,
                "original_name": file_record.original_name,
                "modified_name": file_record.modified_name
            }

    # Return user data (exclude sensitive information)
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "is_active": user.is_active,
        "role": user.role.value,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "profile_image": profile_image
    }
