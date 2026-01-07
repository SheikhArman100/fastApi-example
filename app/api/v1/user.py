from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from ...services.file_service import save_file
from ...services.user_service import get_all_users, UserFilters, PaginationOptions
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
    print("Fetching users with filters and pagination")
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
