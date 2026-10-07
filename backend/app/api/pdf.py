from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io
from datetime import datetime

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import User, Message, Conversation
from app.services.pdf_exporter import generate_pdf_report

router = APIRouter()

@router.get("/export/{message_id}")
def export_chat_pdf(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves assistant message details and generates a beautiful PDF report.
    """
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message or message.role != "assistant":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Welfare advice message not found"
        )
        
    # Verify ownership of the conversation session
    conversation = db.query(Conversation).filter(
        Conversation.id == message.conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this conversation report"
        )

    # Compile data structure for PDF generator
    chat_data = {
        "answer": message.content,
        "citations": message.citations or [],
        "action_plan": message.action_plan,
        "date": message.created_at.strftime("%Y-%m-%d %H:%M:%S")
    }

    scheme_name = "Government Welfare Scheme"
    if message.citations:
        # Deduce scheme name from first citation
        scheme_name = message.citations[0].get("source", "Welfare Scheme Advice")
        if scheme_name.endswith(".csv") or scheme_name.endswith(".pdf"):
            scheme_name = scheme_name[:-4]

    try:
        pdf_buffer = generate_pdf_report(chat_data, scheme_name=scheme_name)
        
        filename = f"GovAssist_Action_Plan_{message_id}.pdf"
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF: {str(e)}"
        )
