from pydantic import BaseModel

class FileResponse(BaseModel):
    id: int
    path: str
    type: str
    original_name: str
    modified_name: str

    class Config:
        from_attributes = True
