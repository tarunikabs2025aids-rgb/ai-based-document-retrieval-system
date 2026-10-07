import logging
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
from collections import defaultdict

from app.core.config import settings
from app.core.database import init_db
from app.services.vector_db import scan_and_rebuild_index
from app.api import auth, chat, eligibility, search, documents, feedback, analytics, history, pdf

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for citizen welfare schemes discoveries and applications assistance.",
    version="1.0.0"
)
@app.get("/")
def root():
    return {
        "message": "GovAssist AI Backend is running successfully",
        "docs": "/docs"
    }

# CORS configurations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom In-Memory Rate Limiter Middleware
# Keeps track of requests count per client IP within 1-minute window
rate_limit_store = defaultdict(list)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    
    # Clean up request history older than 60 seconds
    rate_limit_store[client_ip] = [t for t in rate_limit_store[client_ip] if now - t < 60]
    
    # Set limit: 100 requests per minute
    LIMIT = 100
    if len(rate_limit_store[client_ip]) >= LIMIT:
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Too many requests. Please try again in a minute."}
        )
        
    rate_limit_store[client_ip].append(now)
    response = await call_next(request)
    return response

# Startup tasks
@app.on_event("startup")
def startup_event():
    logger.info("Starting GovAssist AI Backend...")
    # Initialize SQL database tables
    logger.info("Initializing database...")
    init_db()
    
    # Run initial index scan
    logger.info("Scanning document repository for vector indexing...")
    try:
        results = scan_and_rebuild_index()
        logger.info(f"Vector indexing status on boot: {results}")
    except Exception as e:
        logger.warning(f"Index build failed on startup (this is fine if models are downloading or directories are empty): {e}")

# Register API Routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(chat.router, prefix=f"{settings.API_V1_STR}/chat", tags=["Chatbot"])
app.include_router(eligibility.router, prefix=f"{settings.API_V1_STR}/eligibility", tags=["Eligibility Checker"])
app.include_router(search.router, prefix=f"{settings.API_V1_STR}/search", tags=["Smart Search"])
app.include_router(documents.router, prefix=f"{settings.API_V1_STR}/documents", tags=["Document Panel"])
app.include_router(feedback.router, prefix=f"{settings.API_V1_STR}/feedback", tags=["Feedback"])
app.include_router(analytics.router, prefix=f"{settings.API_V1_STR}/analytics", tags=["Analytics"])
app.include_router(history.router, prefix=f"{settings.API_V1_STR}/history", tags=["Chat History"])
app.include_router(pdf.router, prefix=f"{settings.API_V1_STR}/pdf-export", tags=["PDF Exporter"])

@app.get("/health", tags=["Health"])
def health_check():
    from sqlalchemy import text
    from app.core.database import engine
    from app.services.vector_db import HAS_VECTOR_LIBS
    from pathlib import Path
    
    db_status = "unhealthy"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            db_status = "healthy"
    except Exception as e:
        logger.error(f"Health check: Database connection failed: {e}")
        
    index_path = Path(settings.VECTOR_DB_PATH) / "index.faiss"
    vector_status = "unavailable"
    if HAS_VECTOR_LIBS:
        if index_path.exists():
            vector_status = "healthy"
        else:
            vector_status = "empty_index"
            
    # System status determination
    if db_status == "healthy":
        if vector_status == "healthy":
            sys_status = "healthy"
        else:
            sys_status = "degraded"
    else:
        sys_status = "unavailable"
        
    return {
        "status": sys_status,
        "timestamp": time.time(),
        "services": {
            "database": db_status,
            "vector_search": vector_status,
            "translation": "available"
        }
    }
