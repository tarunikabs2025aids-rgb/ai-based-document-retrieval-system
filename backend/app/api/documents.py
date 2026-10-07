import os
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.config import settings
from app.core.database import get_db
from app.api.deps import get_current_admin_user
from app.models.models import DocumentMetadata, User
from app.schemas.admin import DocumentMetadataResponse
from app.services.vector_db import scan_and_rebuild_index

router = APIRouter()

@router.get("/", response_model=List[DocumentMetadataResponse])
def get_documents(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """
    List all indexed PDF documents and CSV datasets.
    """
    return db.query(DocumentMetadata).all()

@router.post("/upload")
def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """
    Upload a new PDF document or CSV dataset, and trigger index rebuild.
    """
    filename = file.filename
    if not filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
        
    ext = os.path.splitext(filename)[1].lower()
    
    if ext == ".pdf":
        target_dir = Path(settings.PDF_FOLDER)
    elif ext == ".csv":
        target_dir = Path(settings.DATASET_FOLDER)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Only PDF and CSV are supported."
        )
        
    target_dir.mkdir(parents=True, exist_ok=True)
    filepath = target_dir / filename
    
    # Save the file locally
    try:
        with open(filepath, "wb") as buffer:
            content = file.file.read()
            buffer.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
        
    # Schedule vector DB rebuild task in the background
    background_tasks.add_task(scan_and_rebuild_index)
    
    return {"message": f"File '{filename}' uploaded successfully. Reindexing started in the background."}

@router.delete("/{doc_id}")
def delete_document(
    doc_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """
    Delete an uploaded document and trigger index rebuild.
    """
    doc = db.query(DocumentMetadata).filter(DocumentMetadata.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    # Determine local file path
    if doc.file_type == "pdf":
        filepath = Path(settings.PDF_FOLDER) / doc.filename
    else:
        filepath = Path(settings.DATASET_FOLDER) / doc.filename
        
    # Delete file
    if filepath.exists():
        try:
            os.remove(filepath)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to remove file from system: {str(e)}"
            )
            
    # Delete database record
    db.delete(doc)
    db.commit()
    
    # Trigger reindexing
    background_tasks.add_task(scan_and_rebuild_index)
    
    return {"message": f"Document '{doc.filename}' deleted. Reindexing started in the background."}
