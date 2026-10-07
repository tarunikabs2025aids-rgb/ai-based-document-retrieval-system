from fastapi import APIRouter, Depends, Query
from typing import Optional
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import User
from app.services.vector_db import query_vector_db

router = APIRouter()

@router.get("/")
def semantic_search(
    q: str = Query(..., description="Search query string"),
    state: Optional[str] = Query(None, description="Filter by state"),
    category: Optional[str] = Query(None, description="Filter by category"),
    occupation: Optional[str] = Query(None, description="Filter by occupation"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search vector DB for government schemes matching keywords, applying metadata filters.
    """
    filters = {}
    if state and state.lower() != "all india" and state.lower() != "any":
        filters["state"] = state
    if category and category.lower() != "any":
        filters["category"] = category
        
    results = query_vector_db(q, top_k=6, filters=filters if filters else None)
    
    # Formulate output structure
    search_results = []
    for r in results:
        meta = r["metadata"]
        search_results.append({
            "title": meta.get("scheme_name", "Scheme Detail"),
            "source": meta.get("source"),
            "content": r["page_content"],
            "confidence": int(r["confidence"] * 100),
            "state": meta.get("state", "All India"),
            "category": meta.get("category", "General"),
            "official_website": meta.get("official_website"),
            "type": meta.get("type", "csv")
        })
        
    return search_results

@router.get("/suggestions")
def get_search_suggestions(
    q: Optional[str] = Query("", description="Input query prefix"),
    current_user: User = Depends(get_current_user)
):
    """
    Returns autocompleting queries and trending schemes lists.
    """
    all_suggestions = [
        "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
        "Post Matric Scholarship Schemes",
        "Startup India Seed Fund Scheme",
        "Pradhan Mantri Mudra Yojana (PMMY)",
        "Ayushman Bharat PM-JAY Health Insurance",
        "Atal Pension Yojana (APY)",
        "PM Street Vendor's AtmaNirbhar Nidhi (PM SVANidhi)",
        "Deendayal Antyodaya Yojana - National Livelihoods Mission"
    ]
    
    trending = [
        "PM-KISAN Farmer Subsidy",
        "Ayushman Bharat Medical Card",
        "Mudra Business Loan",
        "National Scholarship Portal"
    ]
    
    filtered = [s for s in all_suggestions if q.lower() in s.lower()] if q else all_suggestions[:4]
    
    return {
        "suggestions": filtered,
        "trending": trending
    }
