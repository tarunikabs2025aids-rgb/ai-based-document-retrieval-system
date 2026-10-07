import logging
import json
import re
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.core.config import settings
from app.services.vector_db import query_vector_db
from app.schemas.eligibility import EligibilityProfile, SchemeEligibilityMatch, EligibilityCheckResponse

logger = logging.getLogger(__name__)

SYSTEM_ELIGIBILITY_PROMPT = """You are an expert Indian Government welfare officer.
Analyze if a citizen with the following Profile is eligible for the welfare Scheme described in the context.

Citizen Profile:
- Age: {age}
- Gender: {gender}
- State of Residence: {state}
- Occupation: {occupation}
- Annual Family Income: INR {income}
- Category: {category}
- Education: {education}
- Has Disability: {disability}
- Is Farmer: {farmer}
- Is Student: {student}
- Runs/Plans Business: {business}
- Is Military Veteran: {veteran}
- Is Widow: {widow}
- Belongs to Minority: {minority}

Scheme Details:
{scheme_context}

Return a JSON object with this exact schema:
{{
  "status": "ELIGIBLE" | "NOT_ELIGIBLE" | "MORE_INFO",
  "reason": "Clear explanation of why they are eligible or ineligible, highlighting exact matches or mismatch criteria",
  "highlighted_conditions": ["Condition 1 from scheme", "Condition 2 from scheme"],
  "missing_information": ["Any details not specified in profile but required by scheme"]
}}
"""

def python_fallback_eligibility_check(profile: EligibilityProfile, scheme_content: str, scheme_name: str) -> SchemeEligibilityMatch:
    """
    Python-based keyword & rule parsing engine.
    Used when OpenAI keys are absent, ensuring offline eligibility processing.
    """
    status = "ELIGIBLE"
    reasons = []
    conditions = []
    missing = []
    
    # 1. State check
    # Check if a specific state is mentioned in the content (other than the citizen's state and All India)
    state_match = re.search(r"State:\s*([A-Za-z\s]+)", scheme_content, re.IGNORECASE)
    if state_match:
        scheme_state = state_match.group(1).strip()
        conditions.append(f"Must be a resident of {scheme_state}.")
        if scheme_state.lower() != "all india" and scheme_state.lower() != profile.state.lower() and profile.state.lower() not in scheme_state.lower():
            status = "NOT_ELIGIBLE"
            reasons.append(f"Resident of {profile.state} but scheme is restricted to {scheme_state}.")
    
    # 2. Income check
    income_match = re.search(r"income\s*(?:limit|ceiling|less than|below|up to)?\s*(?:rs\.?|inr)?\s*([\d,]+)", scheme_content, re.IGNORECASE)
    if income_match:
        try:
            limit_val_str = income_match.group(1).replace(",", "")
            limit_val = float(limit_val_str)
            conditions.append(f"Annual family income must be below INR {limit_val:,.2f}.")
            if profile.income > limit_val:
                status = "NOT_ELIGIBLE"
                reasons.append(f"Annual income of INR {profile.income:,.2f} exceeds the limit of INR {limit_val:,.2f}.")
        except Exception:
            pass

    # 3. Age check
    age_limit_match = re.search(r"(?:age|years)\s*(?:limit|between|above|below)?\s*(\d+)\s*(?:to|-)?\s*(\d+)?", scheme_content, re.IGNORECASE)
    if age_limit_match:
        try:
            val1 = int(age_limit_match.group(1))
            val2_str = age_limit_match.group(2)
            
            if val2_str:
                val2 = int(val2_str)
                conditions.append(f"Age must be between {val1} and {val2} years.")
                if profile.age < val1 or profile.age > val2:
                    status = "NOT_ELIGIBLE"
                    reasons.append(f"Age is {profile.age} years, but scheme requires {val1}-{val2} years.")
            else:
                # "above 18" or "below 18" check
                context_around = scheme_content[max(0, age_limit_match.start() - 15) : min(len(scheme_content), age_limit_match.end() + 15)].lower()
                if "above" in context_around or "at least" in context_around or "minimum" in context_around:
                    conditions.append(f"Age must be at least {val1} years.")
                    if profile.age < val1:
                        status = "NOT_ELIGIBLE"
                        reasons.append(f"Age is {profile.age} years, but scheme requires minimum {val1} years.")
                elif "below" in context_around or "maximum" in context_around or "up to" in context_around:
                    conditions.append(f"Age must be under {val1} years.")
                    if profile.age > val1:
                        status = "NOT_ELIGIBLE"
                        reasons.append(f"Age is {profile.age} years, but scheme requires maximum {val1} years.")
        except Exception:
            pass

    # 4. Occupation/Farmer check
    if "farmer" in scheme_content.lower():
        conditions.append("Must be engaged in farming/agriculture activities.")
        if not profile.farmer and profile.occupation.lower() != "farmer":
            status = "MORE_INFO"
            reasons.append("Farmer status is set to No in your profile, but this scheme is targeted towards agricultural workers.")
            missing.append("Landholding ownership certificate, Farmer ID card.")

    if "student" in scheme_content.lower() or "scholarship" in scheme_content.lower():
        conditions.append("Must be currently studying in an educational institution.")
        if not profile.student and profile.occupation.lower() != "student":
            status = "MORE_INFO"
            reasons.append("Student status is set to No, but this scheme benefits students/academic pursuits.")
            missing.append("Current enrollment certificate, previous marksheets.")

    if "business" in scheme_content.lower() or "startup" in scheme_content.lower() or "entrepreneur" in scheme_content.lower():
        conditions.append("Must own or plan a business/MSME enterprise.")
        if not profile.business and profile.occupation.lower() not in ["business", "self-employed"]:
            status = "MORE_INFO"
            reasons.append("Profile does not indicate business interests, but this scheme provides corporate/startup support.")
            missing.append("Business Registration/Udyam Aadhaar certificate, project proposal.")

    if "disability" in scheme_content.lower() or "physically challenged" in scheme_content.lower() or "divyangjan" in scheme_content.lower():
        conditions.append("Must have a valid disability certificate (40% or more disability).")
        if not profile.disability:
            status = "NOT_ELIGIBLE"
            reasons.append("Scheme requires physical disability qualification, but disability flag is No.")

    # Formulate final outputs
    if status == "ELIGIBLE":
        if not reasons:
            reasons.append("Matches state, age, and occupation filters. Meets primary welfare standards.")
        reason_text = " ✅ " + " ".join(reasons)
    elif status == "NOT_ELIGIBLE":
        reason_text = " ❌ " + " ".join(reasons)
    else:
        reason_text = " ❓ " + " ".join(reasons) + " Verify if you satisfy additional conditions."

    if not conditions:
        conditions = ["Must satisfy income and residence certificate guidelines.", "Must possess Aadhaar card registration."]

    return SchemeEligibilityMatch(
        scheme_id=re.sub(r"[^a-zA-Z0-9]", "_", scheme_name.lower()),
        scheme_name=scheme_name,
        status=status,
        reason=reason_text,
        highlighted_conditions=conditions,
        missing_information=missing
    )

def evaluate_eligibility(profile: EligibilityProfile) -> EligibilityCheckResponse:
    """
    Retrieve schemes matching user context, evaluate criteria, and group them.
    """
    # Create search terms based on occupation and profile flags
    search_keywords = ["government scheme"]
    if profile.farmer or profile.occupation.lower() == "farmer":
        search_keywords.append("farmer agriculture loan subsidy")
    if profile.student or profile.occupation.lower() == "student":
        search_keywords.append("student scholarship education fellowship")
    if profile.business:
        search_keywords.append("business startup loan subsidy MSME")
    if profile.widow:
        search_keywords.append("widow pension welfare assistance")
    if profile.disability:
        search_keywords.append("disabled handicap divyangjan pension disability")
    if profile.income < 300000:
        search_keywords.append("poor BPL ration card free subsidy")
        
    combined_query = " ".join(search_keywords)
    logger.info(f"Evaluating eligibility with query: '{combined_query}' for profile state '{profile.state}'")
    
    # Query vector store for related scheme chunks
    matched_chunks = query_vector_db(combined_query, top_k=8, filters={"type": "csv"})
    
    eligible = []
    not_eligible = []
    more_info = []
    
    seen_schemes = set()
    
    for chunk in matched_chunks:
        meta = chunk["metadata"]
        scheme_name = meta.get("scheme_name")
        if not scheme_name or scheme_name in seen_schemes:
            continue
        seen_schemes.add(scheme_name)
        
        content = chunk["page_content"]
        
        # Evaluate eligibility (LLM vs python fallback)
        llm_evaluated = False
        match_result = None
        
        if settings.OPENAI_API_KEY:
            try:
                prompt = ChatPromptTemplate.from_messages([
                    ("system", SYSTEM_ELIGIBILITY_PROMPT),
                ])
                llm = ChatOpenAI(
                    model=settings.MODEL_NAME,
                    openai_api_key=settings.OPENAI_API_KEY,
                    temperature=0.0,
                    response_format={"type": "json_object"}
                )
                chain = prompt | llm
                response = chain.invoke({
                    "age": profile.age,
                    "gender": profile.gender,
                    "state": profile.state,
                    "occupation": profile.occupation,
                    "income": profile.income,
                    "category": profile.category,
                    "education": profile.education,
                    "disability": profile.disability,
                    "farmer": profile.farmer,
                    "student": profile.student,
                    "business": profile.business,
                    "veteran": profile.veteran,
                    "widow": profile.widow,
                    "minority": profile.minority,
                    "scheme_context": content
                })
                
                resp_json = json.loads(response.content)
                match_result = SchemeEligibilityMatch(
                    scheme_id=re.sub(r"[^a-zA-Z0-9]", "_", scheme_name.lower()),
                    scheme_name=scheme_name,
                    status=resp_json.get("status", "MORE_INFO"),
                    reason=resp_json.get("reason", "Requires details."),
                    highlighted_conditions=resp_json.get("highlighted_conditions", []),
                    missing_information=resp_json.get("missing_information", [])
                )
                llm_evaluated = True
            except Exception as e:
                logger.error(f"LLM eligibility evaluation failed for {scheme_name}: {e}. Swapping to python engine.")
                
        if not llm_evaluated:
            match_result = python_fallback_eligibility_check(profile, content, scheme_name)
            
        # Group based on status
        if match_result.status == "ELIGIBLE":
            eligible.append(match_result)
        elif match_result.status == "NOT_ELIGIBLE":
            not_eligible.append(match_result)
        else:
            more_info.append(match_result)
            
    # If no schemes matched from vector DB, supply a default set of placeholders (if local CSV folder is empty)
    if not eligible and not not_eligible and not more_info:
        logger.warning("No schemes found in Vector DB. Synthesizing default check results.")
        # Synthesize fallback schemes for demonstration if DB is empty
        schemes_fallback = [
            ("Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)", "farmer", "Eligible. Farmers receive Rs. 6000 income support.", ["Must own cultivable agricultural land.", "Must not be an income tax payer."]),
            ("Post Matric Scholarship for SC/ST Students", "student", "Eligible. Financial assistance for higher education studies.", ["Must belong to SC/ST category.", "Family income must be below 2.5 LPA."]),
            ("Pradhan Mantri Mudra Yojana (PMMY) Startup Loan", "business", "Eligible. Micro loans up to 10 Lakhs for business establishment.", ["For non-corporate, non-farm small/micro enterprises.", "Subject to bank credit checks."])
        ]
        for name, keyword, desc, conds in schemes_fallback:
            is_match = False
            if keyword == "farmer" and (profile.farmer or profile.occupation.lower() == "farmer"):
                is_match = True
            elif keyword == "student" and (profile.student or profile.occupation.lower() == "student"):
                is_match = True
            elif keyword == "business" and profile.business:
                is_match = True
                
            if is_match:
                eligible.append(SchemeEligibilityMatch(
                    scheme_id=re.sub(r"[^a-zA-Z0-9]", "_", name.lower()),
                    scheme_name=name,
                    status="ELIGIBLE",
                    reason=f" ✅ Matches {keyword} profile. {desc}",
                    highlighted_conditions=conds,
                    missing_information=[]
                ))
                
    # Create profile summary
    profile_summary = {
        "Age": str(profile.age),
        "Gender": profile.gender,
        "State": profile.state,
        "Occupation": profile.occupation,
        "Annual Income": f"INR {profile.income:,.2f}",
        "Category": profile.category,
        "Education": profile.education,
        "Special Attributes": ", ".join(filter(None, [
            "Farmer" if profile.farmer else None,
            "Student" if profile.student else None,
            "Business Owner" if profile.business else None,
            "Veteran" if profile.veteran else None,
            "Widow" if profile.widow else None,
            "Minority" if profile.minority else None,
            "Disabled" if profile.disability else None,
        ])) or "None"
    }
    
    return EligibilityCheckResponse(
        profile_summary=profile_summary,
        eligible_schemes=eligible,
        not_eligible_schemes=not_eligible,
        more_info_schemes=more_info
    )
