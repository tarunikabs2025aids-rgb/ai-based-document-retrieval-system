import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.core.config import settings
from app.services.translator import detect_language, translate_to_english, translate_from_english
from app.services.vector_db import query_vector_db
from app.schemas.chat import Citation, ActionPlan, ActionTimelineItem

logger = logging.getLogger(__name__)

# System instructions to enforce grounded responses
SYSTEM_PROMPT = """You are GovAssist AI, an expert welfare schemes assistant for Indian citizens.
Your job is to answer the user's question using ONLY the provided retrieved context.

RULES:
1. Focus only on answering the question accurately using the context.
2. Do not hallucinate or include outside information.
3. If the context does not contain enough information to answer the question, state: "I couldn't find reliable information for this question."
4. Include structured details if asked (e.g. required documents, fees, eligibility criteria).
5. Output your response as a JSON block matching the structure below:
{{
  "answer": "A clear, detailed, markdown-formatted explanation of the scheme/answer",
  "has_sufficient_context": true/false,
  "required_documents": ["list", "of", "required", "documents"],
  "application_form_url": "url or null",
  "where_to_apply": "specific office, portal, or department",
  "office_address": "office address or null",
  "processing_time": "expected duration, e.g., 15 days",
  "application_fees": "fees, e.g., Rs. 50 or Free",
  "checklist": ["checklist item 1", "checklist item 2"],
  "timeline_steps": [
     {{"step": 1, "title": "step title", "description": "what to do in this step", "timeline": "e.g. Day 1", "status": "pending"}}
  ],
  "warnings": ["any warnings or eligibility limits"],
  "notes": ["any additional notes"]
}}

Context:
{context}

User Question:
{question}
"""

def generate_mock_rag_response(query_en: str, matched_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate a high-quality mock response based on the top FAISS matching chunks.
    Ensures that the app functions and can be demoed fully without an active LLM key.
    """
    if not matched_chunks:
        return {
            "answer": "I couldn't find reliable information for this question. Please rephrase or ask something more specific.",
            "has_sufficient_context": False,
            "required_documents": [],
            "application_form_url": None,
            "where_to_apply": "N/A",
            "office_address": None,
            "processing_time": "N/A",
            "application_fees": "N/A",
            "checklist": [],
            "timeline_steps": [],
            "warnings": [],
            "notes": []
        }
    
    top_chunk = matched_chunks[0]
    meta = top_chunk["metadata"]
    content = top_chunk["page_content"]
    
    # Attempt to extract fields dynamically if it's a CSV row chunk
    if meta.get("type") == "csv":
        scheme_name = meta.get("scheme_name", "the requested scheme")
        website = meta.get("official_website", "the official portal")
        state = meta.get("state", "All India")
        category = meta.get("category", "General")
        
        # Simple extraction helper
        def extract_field(marker: str, fallback: str = "Not specified") -> str:
            for line in content.split("\n"):
                if line.startswith(marker):
                    return line.replace(marker, "").strip()
            return fallback

        desc = extract_field("Description:")
        elig = extract_field("Eligibility Criteria:")
        benefits = extract_field("Benefits Provided:")
        docs = extract_field("Required Documents:")
        process = extract_field("Application Process:")
        fees = extract_field("Fees:", "Free")
        timeline = extract_field("Processing Time:", "Varies")
        
        doc_list = [d.strip() for d in docs.split(",") if d.strip()] if docs != "Not specified" else ["Aadhar Card", "Income Certificate"]
        
        ans_md = (
            f"### {scheme_name}\n\n"
            f"**Description:**\n{desc}\n\n"
            f"**Eligibility Details:**\n{elig}\n\n"
            f"**Benefits:**\n{benefits}\n\n"
            f"**Application Process:**\n{process}"
        )
        
        return {
            "answer": ans_md,
            "has_sufficient_context": True,
            "required_documents": doc_list,
            "application_form_url": website if website != "Not specified" else None,
            "where_to_apply": "State / Central Government Nodal Office or website",
            "office_address": f"Local Block Development Office or Department of Welfare, {state}",
            "processing_time": timeline,
            "application_fees": fees,
            "checklist": ["Verify age and income criteria", "Collect required documents", "Submit form online or at local office"],
            "timeline_steps": [
                {"step": 1, "title": "Check Eligibility", "description": f"Confirm you satisfy: {elig[:120]}...", "timeline": "Day 1", "status": "pending"},
                {"step": 2, "title": "Document Gathering", "description": f"Gather: {', '.join(doc_list[:3])}", "timeline": "Day 2-3", "status": "pending"},
                {"step": 3, "title": "Application Submission", "description": f"Apply online at {website} or visit block office", "timeline": "Day 4", "status": "pending"},
                {"step": 4, "title": "Verification & Approval", "description": "Wait for official verification", "timeline": timeline, "status": "pending"}
            ],
            "warnings": [f"Applicable for residents of {state}.", f"Targeted category: {category}."],
            "notes": ["Ensure details on your Aadhaar card match your certificates.", "Double check eligibility criteria before applying."]
        }
    else:
        # PDF page chunk response formulation
        source_name = meta.get("source", "Government PDF Document")
        page = meta.get("page", 1)
        
        ans_md = (
            f"According to the official document **{source_name} (Page {page})**:\n\n"
            f"{content[:500]}...\n\n"
            f"For further instructions, check the official guidelines."
        )
        
        return {
            "answer": ans_md,
            "has_sufficient_context": True,
            "required_documents": ["Aadhaar Card", "Proof of Residence", "Income Certificate"],
            "application_form_url": None,
            "where_to_apply": "Government Department specified in document",
            "office_address": "Concerned ministry department office",
            "processing_time": "15-30 days",
            "application_fees": "Free",
            "checklist": ["Read official guideline PDF carefully", "Prepare ID cards", "Submit application form"],
            "timeline_steps": [
                {"step": 1, "title": "Verify Guidelines", "description": "Review PDF chunk instructions", "timeline": "Day 1", "status": "pending"},
                {"step": 2, "title": "Submit Documentation", "description": "Complete paperwork and submit", "timeline": "Day 2-5", "status": "pending"}
            ],
            "warnings": ["Check details in official circular"],
            "notes": ["Referenced from page content."]
        }

def execute_rag_pipeline(user_query: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Executes complete RAG pipeline:
    1. Detect Language
    2. Translate to English
    3. Retrieve relevant chunks (FAISS)
    4. Perform low confidence filtering
    5. Query LLM / mock generator for grounded answer
    6. Formulate Citations & Citizen Action Planner
    7. Translate answer back to user language
    8. Return structured result
    """
    # 1. Detect language
    lang = detect_language(user_query)
    logger.info(f"RAG Pipeline: Detected query language '{lang}' for input: '{user_query}'")
    
    # 2. Translate query to English
    query_en, _ = translate_to_english(user_query, lang)
    logger.info(f"RAG Pipeline: English translated query: '{query_en}'")
    
    # 3. Retrieve chunks
    matched_chunks = query_vector_db(query_en, top_k=4, filters=filters)
    
    # 4. Check confidence threshold
    # If no chunks retrieved or average confidence score is extremely low (e.g. < 0.40)
    avg_confidence = 0.0
    if matched_chunks:
        avg_confidence = sum(c["confidence"] for c in matched_chunks) / len(matched_chunks)
        
    CONFIDENCE_THRESHOLD = 0.42
    if not matched_chunks or avg_confidence < CONFIDENCE_THRESHOLD:
        logger.warning(f"RAG Pipeline: Low confidence detected (avg score: {avg_confidence:.2f}). Returning fallback.")
        fallback_msg_en = "I couldn't find reliable information for this question. Please rephrase your question or ask something more specific."
        fallback_msg_loc = translate_from_english(fallback_msg_en, lang)
        
        return {
            "answer": fallback_msg_loc,
            "detected_language": lang,
            "confidence_percentage": int(avg_confidence * 100),
            "citations": [],
            "action_plan": None
        }
        
    # 5. Get grounded answer (LLM or mock generator)
    llm_success = False
    rag_data = {}
    
    if settings.OPENAI_API_KEY:
        try:
            logger.info("Invoking OpenAI LLM for grounded generation...")
            # Form context block
            context_block = "\n\n---\n\n".join(
                f"[Source: {c['metadata'].get('source')}, Type: {c['metadata'].get('type')}]\n{c['page_content']}"
                for c in matched_chunks
            )
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", SYSTEM_PROMPT),
                ("human", "{question}")
            ])
            
            llm = ChatOpenAI(
                model=settings.MODEL_NAME,
                openai_api_key=settings.OPENAI_API_KEY,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            chain = prompt | llm
            response = chain.invoke({
                "context": context_block,
                "question": query_en
            })
            
            # Parse json output
            response_json = json.loads(response.content)
            
            if response_json.get("has_sufficient_context", True):
                rag_data = response_json
                llm_success = True
            else:
                logger.warning("LLM reported insufficient context to answer.")
        except Exception as e:
            logger.error(f"OpenAI LLM processing failed: {e}. Swapping to local generator.")
            
    if not llm_success:
        logger.info("Executing local model-free RAG parser...")
        rag_data = generate_mock_rag_response(query_en, matched_chunks)
        
    # 6. Format citations
    citations: List[Citation] = []
    for c in matched_chunks:
        meta = c["metadata"]
        citations.append(Citation(
            source=meta.get("source", "Welfare Scheme Document"),
            page=meta.get("page"),
            chunk=c["page_content"],
            official_website=meta.get("official_website"),
            confidence=round(c["confidence"], 2),
            row_index=meta.get("row_index")
        ))
        
    # Translate answer and planner details back to user's language
    final_answer_en = rag_data["answer"]
    final_answer_loc = translate_from_english(final_answer_en, lang)
    
    # 7. Formulate Citizen Action Plan
    action_plan = None
    if rag_data.get("required_documents") or rag_data.get("timeline_steps"):
        timeline_items = [
            ActionTimelineItem(
                step=item["step"],
                title=translate_from_english(item["title"], lang),
                description=translate_from_english(item["description"], lang),
                timeline=translate_from_english(item["timeline"], lang),
                status=item["status"]
            )
            for item in rag_data.get("timeline_steps", [])
        ]
        
        action_plan = ActionPlan(
            required_documents=[translate_from_english(doc, lang) for doc in rag_data.get("required_documents", [])],
            application_form_url=rag_data.get("application_form_url"),
            where_to_apply=translate_from_english(rag_data.get("where_to_apply", ""), lang),
            office_address=translate_from_english(rag_data.get("office_address", ""), lang) if rag_data.get("office_address") else None,
            processing_time=translate_from_english(rag_data.get("processing_time", ""), lang),
            application_fees=translate_from_english(rag_data.get("application_fees", ""), lang),
            checklist=[translate_from_english(item, lang) for item in rag_data.get("checklist", [])],
            timeline=timeline_items,
            warnings=[translate_from_english(w, lang) for w in rag_data.get("warnings", [])],
            notes=[translate_from_english(n, lang) for n in rag_data.get("notes", [])]
        )
        
    return {
        "answer": final_answer_loc,
        "detected_language": lang,
        "confidence_percentage": int(avg_confidence * 100),
        "citations": [cit.dict() for cit in citations],
        "action_plan": action_plan.dict() if action_plan else None
    }
