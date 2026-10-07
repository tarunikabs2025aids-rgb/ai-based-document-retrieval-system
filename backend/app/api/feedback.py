from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import User, Message, Feedback
from app.schemas.chat import FeedbackInput

router = APIRouter()

@router.post("/")
def submit_feedback(
    fb: FeedbackInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submits user feedback (upvote/downvote and optional comment) for a chatbot message.
    """
    # Verify message exists
    msg = db.query(Message).filter(Message.id == fb.message_id).first()
    if not msg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
        
    # Check if user already provided feedback for this message
    existing_fb = db.query(Feedback).filter(
        Feedback.message_id == fb.message_id,
        Feedback.user_id == current_user.id
    ).first()
    
    if existing_fb:
        existing_fb.rating = fb.rating
        existing_fb.comment = fb.comment
        db.commit()
        return {"message": "Feedback updated successfully"}
        
    new_fb = Feedback(
        message_id=fb.message_id,
        user_id=current_user.id,
        rating=fb.rating,
        comment=fb.comment
    )
    db.add(new_fb)
    db.commit()
    return {"message": "Feedback submitted successfully"}
