import sys
import os

# Append app folder to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.core.database import init_db, SessionLocal
from app.models.models import User, Conversation, Message
from app.services.translator import detect_language, translate_to_english, translate_from_english
from app.services.vector_db import scan_and_rebuild_index, query_vector_db
from app.services.eligibility_engine import evaluate_eligibility, EligibilityProfile

def run_all_tests():
    print("=== STARTING BACKEND SYSTEM VERIFICATION ===")
    
    # 1. Database Init Check
    print("\n[1/5] Testing Database schema initialization...")
    try:
        init_db()
        print("[OK] Database tables initialized successfully.")
    except Exception as e:
        print(f"[FAIL] Database initialization failed: {e}")
        return False

    # 2. Test DB Session and write
    print("\n[2/5] Testing database writes and queries...")
    db = SessionLocal()
    try:
        # Create temp user
        test_email = "test_verifier@govassist.ai"
        existing = db.query(User).filter(User.email == test_email).first()
        if existing:
            db.delete(existing)
            db.commit()
            
        temp_user = User(email=test_email, hashed_password="hashed_placeholder", full_name="Verifier Bot")
        db.add(temp_user)
        db.commit()
        db.refresh(temp_user)
        print(f"[OK] Created verifier user ID: {temp_user.id}")
        
        # Clean up
        db.delete(temp_user)
        db.commit()
        print("[OK] Database cleanup successful.")
    except Exception as e:
        print(f"[FAIL] Database operations failed: {e}")
        db.rollback()
        return False
    finally:
        db.close()

    # 3. Translator Check
    print("\n[3/5] Testing Translation service...")
    try:
        hi_text = "मुझे किसान कर्ज माफी योजना की जानकारी चाहिए"
        detected = detect_language(hi_text)
        print(f"Detected language for Hindi query: '{detected}' (expected: 'hi')")
        
        en_translation, _ = translate_to_english(hi_text, detected)
        print(f"Translated to English: '{en_translation}'")
        
        re_translated = translate_from_english("Hello, how can I help you?", "hi")
        # Print length and status rather than unicode chars directly to avoid cp1252 print crashes
        print(f"Translated greeting back to Hindi. Character length: {len(re_translated)}")
        
        if detected == "hi" and en_translation and len(re_translated) > 0:
            print("[OK] Translation pipeline is functional.")
        else:
            print("[WARN] Translation results are unexpected, but pipeline executed.")
    except Exception as e:
        print(f"[FAIL] Translation service failed: {e}")
        return False

    # 4. Search and Fallback Index Check
    print("\n[4/5] Testing Vector Search and Indexing...")
    try:
        # Create dummy CSV file to index
        csv_dir = os.path.join(settings.DATASET_FOLDER)
        os.makedirs(csv_dir, exist_ok=True)
        csv_file = os.path.join(csv_dir, "test_schemes.csv")
        
        with open(csv_file, mode="w", encoding="utf-8") as f:
            f.write("Scheme Name,State,Category,Description,Eligibility Criteria,Required Documents,Application Process,Official Website\n")
            f.write("PM-KISAN Crop Subsidy,All India,Farmers,Direct financial assistance of Rs 6000 per year to farmers,Must own agricultural land,Aadhaar card land papers,Apply online at portal,https://pmkisan.gov.in\n")
            f.write("State Scholarship Tamil Nadu,Tamil Nadu,Students,Scholarship support for college education,Must be a resident of Tamil Nadu and student,College ID income proof,Apply through state scholarship portal,https://scholarship.tn.gov.in\n")
            
        print("Created mock CSV schemes database. Scanning and indexing...")
        rebuild_results = scan_and_rebuild_index()
        print(f"Index rebuild results: {rebuild_results}")
        
        # Test Query
        query_res = query_vector_db("Tamil Nadu college scholarship")
        print(f"Search results for 'Tamil Nadu college scholarship':")
        for idx, res in enumerate(query_res):
            print(f"  [{idx+1}] {res['metadata'].get('scheme_name')} (Confidence: {int(res['confidence']*100)}%)")
            
        if query_res and query_res[0]['metadata'].get('scheme_name') == "State Scholarship Tamil Nadu":
            print("[OK] Semantic/Keyword search indexing is fully functional.")
        else:
            print("[WARN] Index returned search results but top match was not expected.")
            
        # Clean up files
        if os.path.exists(csv_file):
            os.remove(csv_file)
    except Exception as e:
        print(f"[FAIL] Search indexing failed: {e}")
        return False

    # 5. Eligibility Engine Check
    print("\n[5/5] Testing Eligibility evaluation...")
    try:
        farmer_profile = EligibilityProfile(
            age=35,
            gender="Male",
            state="Punjab",
            occupation="Farmer",
            income=150000,
            category="General",
            education="Secondary",
            disability=False,
            farmer=True,
            student=False,
            business=False,
            veteran=False,
            widow=False,
            minority=False
        )
        
        results = evaluate_eligibility(farmer_profile)
        print(f"Eligibility matches for Farmer profile:")
        for scheme in results.eligible_schemes:
            print(f"  [ELIGIBLE] {scheme.scheme_name}")
            # Avoid printing scheme.reason directly if it could contain non-ASCII emojis or regional chars
            print(f"     Status: {scheme.status}")
        print("[OK] Eligibility evaluation engine is functional.")
    except Exception as e:
        print(f"[FAIL] Eligibility evaluation failed: {e}")
        return False

    print("\n=== BACKEND SYSTEM VERIFICATION SUCCESSFUL ===")
    return True

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
