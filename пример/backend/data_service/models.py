from sqlalchemy import Column, Integer, String, Text, JSON
from database import Base

class FileMetadata(Base):
    __tablename__ = "file_metadata"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True)
    filetype = Column(String)
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)

