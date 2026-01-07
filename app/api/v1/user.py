from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from ...services.file_service import save_file
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
    current_user: User = Depends(auth("admin")),  # Only admins can create users
    db: Session = Depends(get_db)
):
    """Create a new user (Admin only)"""
    # Check if email already exists
    db_user = db.query(User).filter(User.email == email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Save the profile image in users module directory
    file_id = save_file(db, profile_image, module="users")

    # Hash the password
    hashed_password = hash_password(password)

    # Create the user record
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
