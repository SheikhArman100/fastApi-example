from sqlalchemy import Column, Integer, String
from ..db.base import Base

class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    path = Column(String(500), nullable=False)
    type = Column(String(100), nullable=False)
    original_name = Column(String(255), nullable=False)
    modified_name = Column(String(255), unique=True, nullable=False)
