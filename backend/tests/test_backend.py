import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Append parent folder to python path so that app module can be found
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Force settings folders to point to empty test directories before anything else imports them
from app.core.config import settings
settings.PDF_FOLDER = "./test_pdf_dir_temp"
settings.DATASET_FOLDER = "./test_dataset_dir_temp"
settings.VECTOR_DB_PATH = "./test_vector_db_temp"

# Global mocks to prevent model loading/indexing on startup during test runs
mock_get_embeddings = patch("app.services.vector_db.get_embeddings", return_value=None).start()

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Force settings to use a testing db or override get_db
from app.main import app
from app.core.database import get_db
from app.models.models import Base, User, Conversation, Message, Feedback, AnalyticsEvent
from app.core.security import get_password_hash, create_access_token, verify_password

# Use an in-memory SQLite database with StaticPool for testing (persists database across multiple connections in a single test)
from sqlalchemy.pool import StaticPool
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded", "unavailable"]
    assert "timestamp" in data
    assert "services" in data

def test_config_loading():
    assert settings.PROJECT_NAME == "GovAssist AI"
    assert settings.DATABASE_URL is not None

def test_user_registration_and_login(client):
    # Test registration
    reg_data = {
        "email": "citizen@govassist.ai",
        "password": "strongpassword123",
        "full_name": "Citizen User"
    }
    response = client.post("/api/auth/register", json=reg_data)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "citizen@govassist.ai"
    assert "hashed_password" not in data  # Never expose hashed passwords
    
    # Test login
    login_data = {
        "username": "citizen@govassist.ai",
        "password": "strongpassword123"
    }
    response = client.post("/api/auth/login", data=login_data)
    assert response.status_code == 200
    tokens = response.json()
    assert "access_token" in tokens
    assert tokens["token_type"] == "bearer"
    
    # Test login JSON endpoint
    login_json_data = {
        "email": "citizen@govassist.ai",
        "password": "strongpassword123"
    }
    response = client.post("/api/auth/login-json", json=login_json_data)
    assert response.status_code == 200
    tokens_json = response.json()
    assert "access_token" in tokens_json

def test_login_invalid_credentials(client):
    login_data = {
        "username": "citizen@govassist.ai",
        "password": "wrongpassword"
    }
    response = client.post("/api/auth/login", data=login_data)
    assert response.status_code == 400
    assert response.json()["detail"] == "Incorrect email or password"

def test_protected_routes_and_invalid_token(client, db_session):
    # Call without token
    response = client.get("/api/history/")
    assert response.status_code == 401
    
    # Call with invalid token
    headers = {"Authorization": "Bearer invalidtokenhere"}
    response = client.get("/api/history/", headers=headers)
    assert response.status_code == 401

def test_analytics_empty_db(client, db_session):
    # Register first user (automatically made admin)
    reg_data = {
        "email": "admin@govassist.ai",
        "password": "adminpassword",
        "full_name": "Admin User"
    }
    client.post("/api/auth/register", json=reg_data)
    
    # Login to get admin token
    login_data = {
        "username": "admin@govassist.ai",
        "password": "adminpassword"
    }
    response = client.post("/api/auth/login", data=login_data)
    access_token = response.json()["access_token"]
    
    # Call analytics endpoint
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/api/analytics/summary", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_chats"] == 0
    assert data["total_messages"] == 0
    assert data["average_confidence"] == 85.0
    assert data["feedback_ratio"] == 100.0
    assert data["language_distribution"] == {}
    assert data["popular_schemes"] == []
    assert data["popular_states"] == []

def test_analytics_with_real_records(client, db_session):
    # Register and login admin
    reg_data = {
        "email": "admin2@govassist.ai",
        "password": "adminpassword",
        "full_name": "Admin User 2"
    }
    client.post("/api/auth/register", json=reg_data)
    response = client.post("/api/auth/login", data={"username": "admin2@govassist.ai", "password": "adminpassword"})
    access_token = response.json()["access_token"]
    
    # Create some real database entries
    # 1. Get user id
    admin_user = db_session.query(User).filter(User.email == "admin2@govassist.ai").first()
    
    # 2. Conversation
    conv = Conversation(id="test-conv-123", user_id=admin_user.id, title="Test Chat")
    db_session.add(conv)
    db_session.commit()
    
    # 3. Messages (including assistant message for average confidence)
    msg_user = Message(conversation_id=conv.id, role="user", content="Help with Tamil Nadu scholarship", language="en")
    msg_assistant = Message(conversation_id=conv.id, role="assistant", content="Here is information...", confidence=90, language="en")
    db_session.add_all([msg_user, msg_assistant])
    db_session.commit()
    
    # 4. Feedback
    feedback = Feedback(message_id=msg_assistant.id, user_id=admin_user.id, rating=1, comment="Great")
    db_session.add(feedback)
    
    # 5. AnalyticsEvent
    event = AnalyticsEvent(user_id=admin_user.id, query_text="Tamil Nadu college scholarship", detected_language="en", response_confidence=90, matched_scheme="State Scholarship Tamil Nadu")
    db_session.add(event)
    db_session.commit()
    
    # Call analytics endpoint
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/api/analytics/summary", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_chats"] == 1
    assert data["total_messages"] == 2
    assert data["average_confidence"] == 90.0
    assert data["feedback_ratio"] == 100.0
    assert data["language_distribution"] == {"en": 1}
    assert len(data["popular_schemes"]) == 1
    assert data["popular_schemes"][0]["scheme_name"] == "State Scholarship Tamil Nadu"
    assert len(data["popular_states"]) == 1
    assert data["popular_states"][0]["state"] == "Tamil Nadu"

def test_chat_validation_empty_message(client):
    reg_data = {
        "email": "user@govassist.ai",
        "password": "password123",
        "full_name": "Standard User"
    }
    client.post("/api/auth/register", json=reg_data)
    response = client.post("/api/auth/login", data={"username": "user@govassist.ai", "password": "password123"})
    access_token = response.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {access_token}"}
    chat_input = {
        "message": "",  # Empty message
        "language": "en"
    }
    response = client.post("/api/chat/send", json=chat_input, headers=headers)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()

@patch("app.services.rag.detect_language")
@patch("app.services.rag.translate_to_english")
@patch("app.services.rag.query_vector_db")
def test_chat_no_rag_fallback(mock_query, mock_translate, mock_detect, client):
    # Mock fallback when RAG has low confidence
    mock_detect.return_value = "en"
    mock_translate.return_value = ("Test Query", "en")
    mock_query.return_value = [] # Empty search results -> low confidence
    
    # Register and login user
    reg_data = {
        "email": "chatuser@govassist.ai",
        "password": "password123"
    }
    client.post("/api/auth/register", json=reg_data)
    response = client.post("/api/auth/login", data={"username": "chatuser@govassist.ai", "password": "password123"})
    access_token = response.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {access_token}"}
    chat_input = {
        "message": "Unrelated random text search",
        "language": "en"
    }
    response = client.post("/api/chat/send", json=chat_input, headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    
    # Verify events in SSE stream
    content = response.content.decode("utf-8")
    assert "delta" in content
    assert "msg_info" in content
    
    # Reassemble streamed deltas to search for substrings
    import json
    deltas = []
    for line in content.split("\n"):
        if line.startswith("data: "):
            try:
                data_json = json.loads(line[6:])
                if data_json.get("type") == "delta":
                    deltas.append(data_json["content"])
            except Exception:
                pass
    reassembled = "".join(deltas)
    assert "reliable information" in reassembled

def test_translation_fallback():
    from app.services.translator import translate_to_english, translate_from_english
    # Test fallback with invalid language/network down
    res, lang = translate_to_english("random text", "invalid-lang")
    assert res == "random text"
    
    res_from = translate_from_english("random text", "invalid-lang")
    assert res_from == "random text"

def test_vector_db_empty_directories():
    from app.services.vector_db import scan_and_rebuild_index
    # Temporarily point setting directory paths to non-existent ones
    with patch("app.services.vector_db.settings") as mock_settings:
        mock_settings.PDF_FOLDER = "./nonexistent_pdf_folder_test_123"
        mock_settings.DATASET_FOLDER = "./nonexistent_dataset_folder_test_123"
        mock_settings.VECTOR_DB_PATH = "./nonexistent_vector_db_test_123"
        
        # This should execute successfully and return status: empty
        res = scan_and_rebuild_index()
        assert res["status"] == "empty"
        assert res["total_chunks"] == 0
        
        # Clean up mock directories if created
        import shutil
        if os.path.exists("./nonexistent_pdf_folder_test_123"):
            shutil.rmtree("./nonexistent_pdf_folder_test_123")
        if os.path.exists("./nonexistent_dataset_folder_test_123"):
            shutil.rmtree("./nonexistent_dataset_folder_test_123")
        if os.path.exists("./nonexistent_vector_db_test_123"):
            shutil.rmtree("./nonexistent_vector_db_test_123")

@pytest.fixture(scope="session", autouse=True)
def cleanup_temp_folders():
    yield
    import shutil
    for folder in ["./test_pdf_dir_temp", "./test_dataset_dir_temp", "./test_vector_db_temp"]:
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder)
            except Exception:
                pass
