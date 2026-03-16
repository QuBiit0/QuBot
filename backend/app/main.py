"""
Qubot API — FastAPI application factory
"""

import logging
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .core.exceptions import AppError
from .core.metrics import PrometheusMiddleware
from .core.rate_limit import apply_rate_limits
from .core.realtime import get_connection_manager
from .database import create_tables

# Configure structlog
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logging.basicConfig(
    format="%(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
    ],
)

# Use structlog-compatible formatter for stdlib logging
for handler in logging.root.handlers:
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processor=structlog.dev.ConsoleRenderer()
            if settings.DEBUG
            else structlog.processors.JSONRenderer(),
        )
    )

logger = structlog.get_logger(__name__)

# Import routers
from .api.endpoints.agents import router as agents_router
from .api.endpoints.auth import router as auth_router
from .api.endpoints.chat import router as chat_router
from .api.endpoints.config import router as config_router
from .api.endpoints.execution import router as execution_router
from .api.endpoints.llm_configs import router as llm_configs_router
from .api.endpoints.memories import router as memories_router
from .api.endpoints.system import router as system_router
from .api.endpoints.tasks import router as tasks_router
from .api.endpoints.telegram import router as telegram_router
from .api.endpoints.tool_execution import router as tool_execution_router
from .api.endpoints.tools import router as tools_router
from .api.endpoints.websocket import router as websocket_router
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
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Request-ID"],
)

# Trusted hosts middleware (production)
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.qubot.io", "qubot.io", "localhost", "*.localhost"],
    )


# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if not settings.DEBUG:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests"""
    import time

    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time

    logger.info(
        "http_request",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=round(duration * 1000, 2),
    )

    return response


# Custom application error handler
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    """Handle custom application errors"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
            }
        },
    )


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    logger.error("unhandled_exception", error=str(exc), exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}},
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
