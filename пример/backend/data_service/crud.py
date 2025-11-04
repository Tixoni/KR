from sqlalchemy.orm import Session
import models
import schemas

def create_file_metadata(db: Session, file_metadata: schemas.FileMetadataCreate):
    db_file = models.FileMetadata(
        filename=file_metadata.filename,
        filetype=file_metadata.filetype,
        title=file_metadata.title,
        description=file_metadata.description
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file

def get_all_files(db: Session):
    return db.query(models.FileMetadata).all()

def delete_file_metadata(db: Session, filename: str):
    file_obj = db.query(models.FileMetadata).filter(models.FileMetadata.filename == filename).first()
    if not file_obj:
        return False
    db.delete(file_obj)
    db.commit()
    return True