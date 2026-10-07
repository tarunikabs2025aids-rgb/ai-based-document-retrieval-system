from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class EligibilityProfile(BaseModel):
    age: int
    gender: str = Field(..., description="Male, Female, Transgender, Other")
    state: str = Field(..., description="State of residence in India")
    occupation: str = Field(..., description="Farmer, Student, Unemployed, Salaried, Self-employed, Business, Other")
    income: float = Field(..., description="Annual family income in INR")
    category: str = Field("General", description="General, OBC, SC, ST, EWS")
    education: str = Field("None", description="Primary, Secondary, Higher Secondary, Graduate, Post Graduate, None")
    disability: bool = Field(False, description="Whether the citizen has a disability")
    farmer: bool = Field(False, description="Is the citizen a farmer")
    student: bool = Field(False, description="Is the citizen a student")
    business: bool = Field(False, description="Does the citizen run/plan a business")
    veteran: bool = Field(False, description="Is the citizen a military veteran")
    widow: bool = Field(False, description="Is the citizen a widow")
    minority: bool = Field(False, description="Belongs to a minority community")
    other_params: Optional[Dict[str, str]] = None

class SchemeEligibilityMatch(BaseModel):
    scheme_id: str
    scheme_name: str
    status: str # "ELIGIBLE" | "NOT_ELIGIBLE" | "MORE_INFO"
    reason: str
    highlighted_conditions: List[str]
    missing_information: List[str] = []

class EligibilityCheckResponse(BaseModel):
    profile_summary: Dict[str, str]
    eligible_schemes: List[SchemeEligibilityMatch]
    not_eligible_schemes: List[SchemeEligibilityMatch]
    more_info_schemes: List[SchemeEligibilityMatch]
