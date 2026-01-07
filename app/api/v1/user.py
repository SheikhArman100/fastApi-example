from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from typing import Optional
from sqlalchemy.orm import Session
from ...services.file_service import save_file, delete_file
from ...services.user_service import get_all_users, get_user_by_id, update_user, UserFilters, PaginationOptions
from ...core.security import hash_password
from ...api.deps import get_db, auth
from ...models.user import User
from ...schemas.response import create_response

router = APIRouter()

@router.post("/")
async def create_user(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    profile_image: UploadFile = File(...),
    current_user: User = Depends(auth("admin")),
    db: Session = Depends(get_db)
):
    """Create a new user (Admin only)"""
    db_user = db.query(User).filter(User.email == email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    file_id = save_file(db, profile_image, module="users")
    hashed_password = hash_password(password)

    db_user = User(
        name=name,
        email=email,
        password=hashed_password,
        profile_image_id=file_id,
        created_by=current_user.id,
        updated_by=current_user.id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return create_response(
        data={
            "user": {
                "id": db_user.id,
                "name": db_user.name,
                "email": db_user.email,
                "role": db_user.role.value,
                "is_active": db_user.is_active
            }
        },
        message="User created successfully",
        status_code=201
    )

@router.get("/")
async def get_all_users_endpoint(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    order_by: str = Query("created_at", description="Sort field"),
    order_direction: str = Query("desc", description="Sort direction"),
    search_term: str = Query(None, description="Search across name and email"),
    role: str = Query(None, description="Filter by role"),
    email: str = Query(None, description="Filter by email"),
    is_active: bool = Query(None, description="Filter by active status"),
    current_user: User = Depends(auth("admin")),
    db: Session = Depends(get_db)
):
    """Get all users with filtering and pagination (Admin only)"""
    
    pagination = PaginationOptions(
        page=page,
        limit=limit,
        order_by=order_by,
        order_direction=order_direction
    )

    filters = UserFilters(
        search_term=search_term,
        role=role,
        email=email,
        is_active=is_active
    )



    result = get_all_users(db, filters, pagination, current_user)

    return create_response(
        data=result["data"],
        message="Users retrieved successfully",
        status_code=200,
        meta=result["meta"]
    )

@router.get("/{user_id}")
async def get_user_by_id_endpoint(
    user_id: int,
    current_user: User = Depends(auth()),
    db: Session = Depends(get_db)
):
    """Get a single user by ID"""
    user_data = get_user_by_id(db, user_id, current_user)

    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    return create_response(
        data=user_data,
        message="User retrieved successfully",
        status_code=200
    )

@router.put("/{user_id}")
async def update_user_endpoint(
    user_id: int,
    name: str = Form(None, description="User name"),
    email: str = Form(None, description="User email"),
    role: str = Form(None, description="User role (admin/user)"),
    is_active: bool = Form(None, description="User active status"),
    profile_image: Optional[UploadFile] = File(None, description="Profile image file"),
    current_user: User = Depends(auth()),
    db: Session = Depends(get_db)
):
    """Update user information"""

    # Prepare update data (exclude None values)
    update_data = {}
    if name is not None:
        update_data['name'] = name
    if email is not None:
        update_data['email'] = email
    if role is not None:
        update_data['role'] = role
    if is_active is not None:
        update_data['is_active'] = is_active

    try:
        updated_user = update_user(db, user_id, update_data, profile_image, current_user)

        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found or not authorized")

        return create_response(
            data=updated_user,
            message="User updated successfully",
            status_code=200
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
