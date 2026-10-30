import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class AIConfig(BaseModel):
    # llama.cpp server endpoint (OpenAI compatible)
    LLAMA_CPP_BASE_URL: str = os.getenv("LLAMA_CPP_BASE_URL", "http://127.0.0.1:8080/v1")
    LLAMA_CPP_MODEL: str = os.getenv("LLAMA_CPP_MODEL", "qwen-local")

    # Security token for communication between CampusOps backend and AI service
    AI_SERVICE_TOKEN: str = os.getenv("AI_SERVICE_TOKEN", "campusops_ai_secret_token_2026")

    # Inference timeout in seconds
    INFERENCE_TIMEOUT: float = float(os.getenv("INFERENCE_TIMEOUT", "60.0"))

    # Service host & port
    HOST: str = os.getenv("AI_SERVICE_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("AI_SERVICE_PORT", "8001"))

config = AIConfig()

