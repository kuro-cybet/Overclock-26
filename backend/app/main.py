from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.api.router import api_router
from app.core.exceptions import CampusOpsException
from app.core.outbox_worker import outbox_worker

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Safe non-blocking startup of background notification outbox worker
    await outbox_worker.start()
    yield
    # Safe worker shutdown
    await outbox_worker.stop()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="CampusOps Unified Operations Platform with Four Role-Based Portals, Workflow Services & Simulation Engine",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Enable CORS for frontend Vite dev server and any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(CampusOpsException)
async def campusops_exception_handler(request: Request, exc: CampusOpsException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "error_type": exc.__class__.__name__}
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "platform": settings.PROJECT_NAME,
        "status": "operational",
        "version": "1.0.0",
        "api_v1_docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

