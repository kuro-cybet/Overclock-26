import os
from typing import List, Optional
from pydantic import BaseModel
from dotenv import load_dotenv

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.path.join(BACKEND_DIR, ".env")
if os.path.exists(ENV_FILE):
    load_dotenv(ENV_FILE)
else:
    load_dotenv()

DEFAULT_DB_PATH = os.path.join(BACKEND_DIR, "data", "campusops.db")
SQLITE_URL = f"sqlite:///{DEFAULT_DB_PATH.replace(os.sep, '/')}"

def _usable_env(value: Optional[str]) -> Optional[str]:
    """Ignore empty values and unfilled placeholders like [YOUR-PROJECT-REF]."""
    if not value:
        return None
    value = value.strip()
    if not value or "[" in value or "]" in value:
        return None
    return value

class Settings(BaseModel):
    PROJECT_NAME: str = "CampusOps"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "campusops-secret-key-for-development-and-demo-purposes-32chars")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    ALGORITHM: str = "HS256"
    DATABASE_URL: str = os.getenv("DATABASE_URL", SQLITE_URL)
    CORS_ORIGINS: List[str] = ["*"]
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    # Used to build deep links inside notification emails.
    APP_PUBLIC_URL: str = os.getenv("APP_PUBLIC_URL", "http://localhost:5173")

    # Supabase Configuration
    SUPABASE_URL: Optional[str] = _usable_env(os.getenv("SUPABASE_URL"))
    SUPABASE_KEY: Optional[str] = _usable_env(os.getenv("SUPABASE_KEY"))  # Anon key
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = _usable_env(os.getenv("SUPABASE_SERVICE_ROLE_KEY"))

    # Gmail delivery (via the send-campusops-email Supabase Edge Function)
    SUPABASE_EMAIL_FUNCTION: str = os.getenv("SUPABASE_EMAIL_FUNCTION", "send-campusops-email")
    CAMPUSOPS_WEBHOOK_SECRET: Optional[str] = _usable_env(os.getenv("CAMPUSOPS_WEBHOOK_SECRET"))
    # Optional separate secret for the inbound-email webhook; falls back to the webhook secret.
    CAMPUSOPS_INBOUND_SECRET: Optional[str] = _usable_env(os.getenv("CAMPUSOPS_INBOUND_SECRET"))
    # auto: use Gmail when configured, otherwise simulate. gmail: require Gmail. simulated: never call Gmail.
    EMAIL_DELIVERY_MODE: str = os.getenv("EMAIL_DELIVERY_MODE", "auto").strip().lower()
    EMAIL_DELIVERY_TIMEOUT_SECONDS: float = float(os.getenv("EMAIL_DELIVERY_TIMEOUT_SECONDS", "15"))

    @property
    def email_function_url(self) -> Optional[str]:
        if not self.SUPABASE_URL:
            return None
        if not self.SUPABASE_URL.startswith("http"):
            return None
        return f"{self.SUPABASE_URL.rstrip('/')}/functions/v1/{self.SUPABASE_EMAIL_FUNCTION}"

    # WhatsApp Cloud API Configuration
    WHATSAPP_ACCESS_TOKEN: Optional[str] = os.getenv("WHATSAPP_ACCESS_TOKEN", None)
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = os.getenv("WHATSAPP_PHONE_NUMBER_ID", None)
    WHATSAPP_BUSINESS_ACCOUNT_ID: Optional[str] = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID", None)
    WHATSAPP_VERIFY_TOKEN: str = os.getenv("WHATSAPP_VERIFY_TOKEN", "campusops_verify_token_2026")
    WHATSAPP_APP_SECRET: Optional[str] = os.getenv("WHATSAPP_APP_SECRET", None)
    WHATSAPP_API_VERSION: str = os.getenv("WHATSAPP_API_VERSION", "v21.0")

    # AI Service Configuration (ngrok HTTPS or local microservice)
    AI_SERVICE_URL: str = os.getenv("AI_SERVICE_URL", "http://127.0.0.1:8001")
    AI_SERVICE_TOKEN: str = os.getenv("AI_SERVICE_TOKEN", "campusops_ai_secret_token_2026")
    AI_MODEL: str = os.getenv("AI_MODEL", "qwen-local")
    AI_TIMEOUT_SECONDS: int = int(os.getenv("AI_TIMEOUT_SECONDS", "60"))

    # Web Search Configuration
    WEB_SEARCH_PROVIDER: str = os.getenv("WEB_SEARCH_PROVIDER", "duckduckgo")
    WEB_SEARCH_API_KEY: Optional[str] = os.getenv("WEB_SEARCH_API_KEY", None)

settings = Settings()
