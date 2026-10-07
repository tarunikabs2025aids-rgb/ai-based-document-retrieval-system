from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import User
from app.schemas.eligibility import EligibilityProfile, EligibilityCheckResponse
from app.services.eligibility_engine import evaluate_eligibility

router = APIRouter()

@router.post("/check", response_model=EligibilityCheckResponse)
def check_eligibility(
    profile: EligibilityProfile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Accepts user profile details and evaluates matching schemes.
    """
    try:
        results = evaluate_eligibility(profile)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Eligibility engine failed: {str(e)}"
        )
