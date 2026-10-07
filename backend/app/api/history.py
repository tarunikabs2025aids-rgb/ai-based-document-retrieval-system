from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import User, Conversation, Message
from app.schemas.chat import ConversationResponse, MessageResponse

router = APIRouter()

@router.get("/", response_model=List[ConversationResponse])
def get_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all chat sessions for the current logged-in citizen.
    Ordered by pinned status first, then by last update time.
    """
    conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(
        Conversation.is_pinned.desc(),
        Conversation.updated_at.desc()
    ).all()
    
    return conversations

@router.get("/{conversation_id}", response_model=ConversationResponse)
def get_conversation_detail(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetch all messages in a specific chat session.
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation session not found"
        )
        
    return conversation

@router.put("/{conversation_id}/rename")
def rename_conversation(
    conversation_id: str,
    title: str = Query(..., min_length=1, max_length=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Rename a chat session title.
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    conversation.title = title
    conversation.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Conversation renamed successfully", "title": title}

@router.put("/{conversation_id}/pin")
def pin_conversation(
    conversation_id: str,
    is_pinned: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Pin or unpin a chat session to keep it at the top of the sidebar.
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    conversation.is_pinned = is_pinned
    conversation.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Conversation pin status updated", "is_pinned": is_pinned}

@router.delete("/{conversation_id}")
def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a chat session and all its associated messages.
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    db.delete(conversation)
    db.commit()
    return {"message": "Conversation deleted successfully"}
