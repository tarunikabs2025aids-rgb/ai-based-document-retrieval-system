import os
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    PROJECT_NAME: str = "GovAssist AI"
    API_V1_STR: str = "/api"
    
    # Security
    JWT_SECRET: str = "super_secret_jwt_key_change_me_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str = "sqlite:///./govassist.db"
    
    # RAG & LLM
    OPENAI_API_KEY: str = ""
    MODEL_NAME: str = "gpt-4o-mini"
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    
    # Paths
    PDF_FOLDER: str = "backend/documents"
    DATASET_FOLDER: str = "backend/datasets"
    VECTOR_DB_PATH: str = "backend/vector_db"

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'ignore'

# Initialize settings
settings = Settings()

# Ensure folders exist
Path(settings.PDF_FOLDER).mkdir(parents=True, exist_ok=True)
Path(settings.DATASET_FOLDER).mkdir(parents=True, exist_ok=True)
Path(settings.VECTOR_DB_PATH).mkdir(parents=True, exist_ok=True)
