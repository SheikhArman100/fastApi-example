from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from typing import Optional, Dict, Any, List
from ..models.user import User, Role
from ..schemas.response import create_paginated_response
from ..utils.filtering import apply_search_filter, apply_dynamic_field_filters, calculate_pagination
from ..services.file_service import get_file_by_id, save_file, delete_file
from ..core.security import verify_password, hash_password

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

        user_dict = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "is_active": user.is_active,
            "role": user.role.value,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "profile_image": profile_image
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
        raise HTTPException(status_code=403, detail="You are not authorized to access this user")
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

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

def delete_user(db: Session, user_id: int, current_user: User) -> bool:
    """
    Delete a user with authorization checks.
    Only admins can delete users, and users cannot delete themselves.
    """

    # Check authorization - only admins can delete users
    if current_user.role != Role.admin:
        raise HTTPException(status_code=403, detail="Only administrators can delete users")

    # Prevent self-deletion
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")

    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Delete associated profile image if exists
    if user.profile_image_id:
        file_record = get_file_by_id(db, user.profile_image_id)
        if file_record:
            delete_file(file_record)

    # Delete the user
    db.delete(user)
    db.commit()

    return True

def change_password(db: Session, user_id: int, current_password: str, new_password: str, current_user: User) -> bool:
    """
    Change user password with validation.
    Users can only change their own password.
    """

    # Check authorization - users can only change their own password
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You can only change your own password")

    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify current password
    if not verify_password(current_password, user.password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    # Hash new password
    hashed_new_password = hash_password(new_password)

    # Update password
    user.password = hashed_new_password
    user.updated_by = current_user.id
    user.updated_at = func.now()

    db.commit()

    return True

def update_user(db: Session, user_id: int, update_data: Dict[str, Any], profile_image_file, current_user: User) -> Optional[Dict[str, Any]]:
    """
    Update user information with authorization checks.
    Only admins can update other users, users can only update themselves.
    Admins can update role and is_active, users can only update name, email, and profile_image.
    """

    # Check authorization
    if current_user.role != Role.admin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You are not authorized to update this user")

    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Handle profile image update if provided
    if profile_image_file is not None and hasattr(profile_image_file, 'filename') and profile_image_file.filename:
        # Delete old profile image if exists
        if user.profile_image_id:
            old_file = get_file_by_id(db, user.profile_image_id)
            if old_file:
                delete_file(old_file)

        # Save new profile image
        new_file_id = save_file(db, profile_image_file, module="users")
        user.profile_image_id = new_file_id

    # Update user fields based on permissions
    if current_user.role == Role.admin:
        # Admins can update everything
        if 'name' in update_data:
            user.name = update_data['name']
        if 'email' in update_data:
            # Check if email is already taken by another user
            existing_user = db.query(User).filter(User.email == update_data['email'], User.id != user_id).first()
            if existing_user:
                raise HTTPException(status_code=400, detail="Email already taken")
            user.email = update_data['email']
        if 'role' in update_data:
            try:
                user.role = Role(update_data['role'].lower())
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid role")
        if 'is_active' in update_data:
            user.is_active = update_data['is_active']
    else:
        # Regular users can only update name, email, and profile image
        if 'name' in update_data:
            user.name = update_data['name']
        if 'email' in update_data:
            # Check if email is already taken by another user
            existing_user = db.query(User).filter(User.email == update_data['email'], User.id != user_id).first()
            if existing_user:
                raise HTTPException(status_code=400, detail="Email already taken")
            user.email = update_data['email']
        # Regular users cannot update role or is_active

    user.updated_by = current_user.id
    user.updated_at = func.now()

    db.commit()
    db.refresh(user)

    # Return updated user data with profile image details
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
