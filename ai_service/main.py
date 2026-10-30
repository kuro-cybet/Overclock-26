from fastapi import FastAPI, Depends, HTTPException, Header, status
from fastapi.middleware.cors import CORSMiddleware
from ai_service.config import config
from ai_service.schemas import (
    ClassificationRequest,
    ClassificationResponse,
    AnswerRequest,
    AnswerResponse,
    HealthResponse
)
from ai_service.classifier import classifier
from ai_service.qa_engine import qa_engine
from ai_service.llama_client import llama_client

app = FastAPI(
    title="CampusOps Local Qwen AI Microservice",
    description="Dedicated AI inference service bridging Meta WhatsApp / CampusOps Backend with local Qwen GGUF via llama.cpp",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def verify_ai_token(
    authorization: str = Header(None),
    x_ai_token: str = Header(None, alias="X-AI-Token")
):
    """Enforces shared secret authentication between CampusOps backend and this AI service."""
    token = None
    if authorization:
        parts = authorization.split(" ")
        token = parts[1] if len(parts) == 2 and parts[0].lower() == "bearer" else authorization
    elif x_ai_token:
        token = x_ai_token

    if not config.AI_SERVICE_TOKEN:
        return True

    if not token or token != config.AI_SERVICE_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Invalid or missing AI_SERVICE_TOKEN"
        )
    return True

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Reports AI service and upstream llama.cpp server connectivity."""
    is_connected = await llama_client.check_health()
    return HealthResponse(
        status="healthy" if is_connected else "degraded",
        llama_cpp_connected=is_connected,
        model=config.LLAMA_CPP_MODEL,
        endpoint=config.LLAMA_CPP_BASE_URL
    )

@app.post(
    "/ai/v1/classify",
    response_model=ClassificationResponse,
    tags=["Classification"],
    dependencies=[Depends(verify_ai_token)]
)
async def classify_message(payload: ClassificationRequest):
    """
    Classifies intent and extracts operational entities (category, location, description, priority)
    from WhatsApp user messages using Qwen GGUF.
    """
    return await classifier.classify(
        message=payload.message,
        sender_role=payload.sender_role or "student",
        conversation_history=payload.conversation_history
    )

@app.post(
    "/ai/v1/answer",
    response_model=AnswerResponse,
    tags=["Q&A"],
    dependencies=[Depends(verify_ai_token)]
)
async def generate_answer(payload: AnswerRequest):
    """
    Synthesizes grounded responses to general campus, academic, or procedure queries using
    supplied CampusOps DB data, institutional knowledge, or verified web search context.
    """
    return await qa_engine.answer(
        query=payload.query,
        context=payload.context,
        source_urls=payload.source_urls,
        sender_role=payload.sender_role or "student"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("ai_service.main:app", host=config.HOST, port=config.PORT, reload=True)

