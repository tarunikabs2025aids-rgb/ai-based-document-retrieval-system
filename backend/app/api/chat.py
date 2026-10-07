import json
import asyncio
import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import User, Conversation, Message, AnalyticsEvent
from app.schemas.chat import ChatInput, MessageResponse
from app.services.rag import execute_rag_pipeline

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/send")
async def send_message_stream(
    chat_in: ChatInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Post a new user query and return an SSE stream yielding response text deltas,
    and structured citations + action plans.
    """
    conversation_id = chat_in.conversation_id
    
    # Validate message query
    if not chat_in.message or not chat_in.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message query cannot be empty or only whitespace."
        )
    
    # Generate new conversation if not provided
    if not conversation_id:
        conversation_id = str(uuid.uuid4())
        conversation = Conversation(
            id=conversation_id,
            user_id=current_user.id,
            title=chat_in.message[:30] + ("..." if len(chat_in.message) > 30 else "")
        )
        db.add(conversation)
        db.commit()
    else:
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation:
            # Create if client generated a UUID
            conversation = Conversation(
                id=conversation_id,
                user_id=current_user.id,
                title=chat_in.message[:30] + ("..." if len(chat_in.message) > 30 else "")
            )
            db.add(conversation)
            db.commit()
        else:
            # Update conversation timestamp
            conversation.updated_at = datetime.now(timezone.utc)
            db.commit()

    # Save User message to Database
    user_msg = Message(
        conversation_id=conversation_id,
        role="user",
        content=chat_in.message,
        original_content=chat_in.message,
        language=chat_in.language or "en"
    )
    db.add(user_msg)
    db.commit()

    # Execute RAG Pipeline (Language Detection, Semantic Retrieval, Grounding, Translation)
    # Perform in executor or async block to avoid blocking FastAPI threads
    loop = asyncio.get_running_loop()
    rag_result = await loop.run_in_executor(
        None, 
        lambda: execute_rag_pipeline(chat_in.message)
    )

    detected_lang = rag_result.get("detected_language", "en")
    answer_text = rag_result.get("answer", "")
    citations = rag_result.get("citations", [])
    action_plan = rag_result.get("action_plan")
    confidence = rag_result.get("confidence_percentage", 50)

    # Save Analytics Event in background
    matched_scheme = None
    if citations:
        matched_scheme = citations[0].get("source")
    
    analytics_event = AnalyticsEvent(
        user_id=current_user.id,
        query_text=chat_in.message,
        detected_language=detected_lang,
        response_confidence=confidence,
        matched_scheme=matched_scheme
    )
    db.add(analytics_event)
    db.commit()

    # Save Assistant message to Database (all at once)
    assistant_msg = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=answer_text,
        original_content=answer_text, # Translate if wanted, keeping it standard
        language=detected_lang,
        citations=citations,
        action_plan=action_plan,
        confidence=confidence
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    async def sse_generator():
        try:
            # Stream the answer in chunks simulating word streaming (around 20-30 characters at a time)
            chunk_size = 12
            for i in range(0, len(answer_text), chunk_size):
                chunk = answer_text[i:i + chunk_size]
                yield f"data: {json.dumps({'type': 'delta', 'content': chunk})}\n\n"
                await asyncio.sleep(0.015)
                
            # Send message ID
            yield f"data: {json.dumps({'type': 'msg_info', 'message_id': assistant_msg.id, 'conversation_id': conversation_id, 'confidence': confidence})}\n\n"
            
            # Send citations
            if citations:
                yield f"data: {json.dumps({'type': 'citations', 'content': citations})}\n\n"
                
            # Send Action Plan
            if action_plan:
                yield f"data: {json.dumps({'type': 'action_plan', 'content': action_plan})}\n\n"
                
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"SSE Streaming error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': 'Stream interrupted'})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")
