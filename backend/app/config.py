import os
from typing import List
from pydantic import BaseModel

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB_PATH = os.path.join(BACKEND_DIR, "data", "campusops.db")
SQLITE_URL = f"sqlite:///{DEFAULT_DB_PATH.replace(os.sep, '/')}"

class Settings(BaseModel):
    PROJECT_NAME: str = "CampusOps"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "campusops-secret-key-for-development-and-demo-purposes-32chars")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    ALGORITHM: str = "HS256"
    DATABASE_URL: str = os.getenv("DATABASE_URL", SQLITE_URL)
    CORS_ORIGINS: List[str] = ["*"]
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

settings = Settings()
