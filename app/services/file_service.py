import os
from uuid import uuid4
from fastapi import UploadFile
from sqlalchemy.orm import Session
from ..models.file import File

def save_file(db: Session, file: UploadFile, module: str = "general") -> int:
    """
    Save uploaded file to dynamic module-based directory structure

    Args:
        db: Database session
        file: FastAPI UploadFile object
        module: Module name (e.g., 'users', 'products', 'documents')

    Returns:
        File record ID
    """
    # Generate unique filename using UUID
    file_extension = os.path.splitext(file.filename)[1]
    unique_name = str(uuid4()) + file_extension

    # Create dynamic module directory structure
    upload_dir = os.path.join("uploads", module)
    os.makedirs(upload_dir, exist_ok=True)

    # Save file to disk
    file_path = os.path.join(upload_dir, unique_name)
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    # Insert record into files table
    db_file = File(
        path=file_path,  
        type=file.content_type,
        original_name=file.filename,
        modified_name=unique_name
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    return db_file.id

def get_file_path(file_record: File) -> str:
    """Get the full file path for a file record"""
    return file_record.path

def get_file_by_id(db: Session, file_id: int):
    """Get file details by ID"""
    return db.query(File).filter(File.id == file_id).first()

def delete_file(file_record: File) -> bool:
    """Delete file from disk and database"""
    try:
        # Delete from disk
        if os.path.exists(file_record.path):
            os.remove(file_record.path)

        # Note: Database record deletion should be handled by cascade delete
        # or explicitly in the calling code

        return True
    except Exception:
        return False
