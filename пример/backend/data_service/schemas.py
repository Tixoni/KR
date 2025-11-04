from pydantic import BaseModel
from typing import Optional, Dict, Any

class FileMetadataCreate(BaseModel):
    filename: str
    filetype: str
    title: Optional[str] = None
    description: Optional[str] = None