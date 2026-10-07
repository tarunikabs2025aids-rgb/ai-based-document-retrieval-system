from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any, List

from app.core.database import get_db
from app.api.deps import get_current_admin_user
from app.models.models import User, Conversation, Message, Feedback, AnalyticsEvent
from app.schemas.admin import AnalyticsSummary

router = APIRouter()

@router.get("/summary", response_model=AnalyticsSummary)
def get_analytics_summary(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """
    Computes summary telemetry data for admin insights.
    """
    total_chats = db.query(Conversation).count()
    total_messages = db.query(Message).count()
    
    # Average confidence
    avg_conf_query = db.query(func.avg(Message.confidence)).filter(Message.role == "assistant").scalar()
    average_confidence = float(avg_conf_query) if avg_conf_query is not None else 85.0
    
    # Feedback ratio
    total_feedback = db.query(Feedback).count()
    likes = db.query(Feedback).filter(Feedback.rating == 1).count()
    feedback_ratio = (likes / total_feedback * 100) if total_feedback > 0 else 100.0
    
    # Language distribution
    lang_results = db.query(
        AnalyticsEvent.detected_language, 
        func.count(AnalyticsEvent.id)
    ).group_by(AnalyticsEvent.detected_language).all()
    
    language_distribution = {lang: count for lang, count in lang_results if lang is not None}
        
    # Popular schemes
    scheme_results = db.query(
        AnalyticsEvent.matched_scheme,
        func.count(AnalyticsEvent.id)
    ).filter(AnalyticsEvent.matched_scheme != None).group_by(
        AnalyticsEvent.matched_scheme
    ).order_by(
        func.count(AnalyticsEvent.id).desc()
    ).limit(5).all()
    
    popular_schemes = [{"scheme_name": s, "queries": c} for s, c in scheme_results if s is not None]
        
    # Popular states (derived from queries / analytical content if logged, or generic fallback)
    states_list = [
        "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", 
        "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", 
        "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", 
        "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura", 
        "Uttar Pradesh", "Uttarakhand", "West Bengal", "Delhi", "Jammu", "Kashmir", "Ladakh"
    ]
    
    query_texts = db.query(AnalyticsEvent.query_text).all()
    from collections import defaultdict
    state_counts = defaultdict(int)
    for (text,) in query_texts:
        if not text:
            continue
        text_lower = text.lower()
        for state in states_list:
            if state.lower() in text_lower:
                state_counts[state] += 1
                
    sorted_states = sorted(state_counts.items(), key=lambda x: x[1], reverse=True)
    popular_states = [{"state": state, "count": count} for state, count in sorted_states[:5]]
    
    return AnalyticsSummary(
        total_chats=total_chats,
        total_messages=total_messages,
        average_confidence=average_confidence,
        feedback_ratio=feedback_ratio,
        language_distribution=language_distribution,
        popular_schemes=popular_schemes,
        popular_states=popular_states
    )
