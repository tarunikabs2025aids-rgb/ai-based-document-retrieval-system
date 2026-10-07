from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, index=True) # UUID string format from frontend/client
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, default="New Conversation")
    is_pinned = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    role = Column(String, nullable=False) # "user" or "assistant"
    content = Column(Text, nullable=False) # Localized language content
    original_content = Column(Text, nullable=True) # English translated content
    language = Column(String, default="en") # Language code: 'en', 'hi', 'ta', etc.
    citations = Column(JSON, nullable=True) # List of source documents/chunks
    action_plan = Column(JSON, nullable=True) # Checklist & Next steps JSON
    confidence = Column(Integer, nullable=True) # Confidence percentage
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    conversation = relationship("Conversation", back_populates="messages")
    feedbacks = relationship("Feedback", back_populates="message", cascade="all, delete-orphan")

class Feedback(Base):
    __tablename__ = "feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False) # 1 for upvote, -1 for downvote
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    message = relationship("Message", back_populates="feedbacks")

class DocumentMetadata(Base):
    __tablename__ = "document_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True, nullable=False)
    file_type = Column(String, nullable=False) # "pdf" or "csv"
    file_hash = Column(String, nullable=False)
    chunk_count = Column(Integer, default=0)
    indexed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    query_text = Column(Text, nullable=False)
    detected_language = Column(String, default="en")
    response_confidence = Column(Integer, nullable=True)
    matched_scheme = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
