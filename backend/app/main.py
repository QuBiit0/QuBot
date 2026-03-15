"""
Qubot API — FastAPI application factory
"""
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from .config import settings
from .database import create_tables
from .core.realtime import get_connection_manager
from .core.rate_limit import limiter, apply_rate_limits
from .core.metrics import PrometheusMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import routers
from .api.endpoints.system import router as system_router
from .api.endpoints.auth import router as auth_router
from .api.endpoints.agents import router as agents_router
from .api.endpoints.tasks import router as tasks_router
from .api.endpoints.tools import router as tools_router
from .api.endpoints.llm_configs import router as llm_configs_router
from .api.endpoints.memories import router as memories_router
from .api.endpoints.tool_execution import router as tool_execution_router
from .api.endpoints.execution import router as execution_router
from .api.endpoints.websocket import router as websocket_router
from .api.endpoints.chat import router as chat_router
from .api.endpoints.telegram import router as telegram_router
from .api.endpoints.config import router as config_router
from .api.skills import router as skills_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Qubot backend...")
    
    # Initialize database
    await create_tables()
    logger.info("Database ready.")
    
    # Seed data
    try:
        from scripts.seed_db import seed
        await seed()
        logger.info("Seed data verified.")
    except Exception as exc:
        logger.error("Seed error: %s", exc)
    
    # Setup Redis pub/sub for realtime
    try:
        manager = get_connection_manager()
        await manager.setup_redis()
        logger.info("Realtime system ready.")
    except Exception as exc:
        logger.warning(f"Realtime setup (Redis not available): {exc}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Qubot backend...")
    
    try:
        manager = get_connection_manager()
        await manager.close()
        logger.info("Realtime connections closed.")
    except Exception as exc:
        logger.error(f"Shutdown error: {exc}")


# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Apply rate limiting
apply_rate_limits(app)

# Prometheus metrics middleware
app.add_middleware(PrometheusMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted hosts middleware (production)
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.qubot.io", "qubot.io", "localhost", "*.localhost"],
    )

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests"""
    import time
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    
    logger.info(
        f"{request.method} {request.url.path} - {response.status_code} - {duration:.3f}s"
    )
    
    return response

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

# Include routers
app.include_router(system_router, prefix=settings.API_V1_STR)
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(agents_router, prefix=settings.API_V1_STR)
app.include_router(tasks_router, prefix=settings.API_V1_STR)
app.include_router(tools_router, prefix=settings.API_V1_STR)
app.include_router(llm_configs_router, prefix=settings.API_V1_STR)
app.include_router(memories_router, prefix=settings.API_V1_STR)
app.include_router(tool_execution_router, prefix=settings.API_V1_STR)
app.include_router(execution_router, prefix=settings.API_V1_STR)
app.include_router(websocket_router)
app.include_router(chat_router, prefix=settings.API_V1_STR)
app.include_router(telegram_router, prefix=settings.API_V1_STR)
app.include_router(config_router, prefix=settings.API_V1_STR)
app.include_router(skills_router, prefix=settings.API_V1_STR)

# Root endpoint
@app.get("/")
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs" if settings.DEBUG else None,
        "health": f"{settings.API_V1_STR}/health",
    }

# Health check for load balancers
@app.get("/health")
async def health():
    return {"status": "healthy"}
