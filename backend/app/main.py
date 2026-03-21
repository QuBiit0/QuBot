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

# Service singletons
_docker_sandbox_service = None
_loop_detection_service = None
_tool_profile_service = None
_plugin_manager = None


def get_docker_sandbox():
    return _docker_sandbox_service


def get_loop_detection_service():
    return _loop_detection_service


def get_tool_profile_service():
    return _tool_profile_service


def get_plugin_manager():
    from .plugins import get_plugin_manager as _get_pm

    return _get_pm()


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
from .api.endpoints.integrations import router as integrations_router
from .api.endpoints.tool_execution import router as tool_execution_router
from .api.endpoints.tools import router as tools_router
from .api.endpoints.websocket import router as websocket_router
from .api.skills import router as skills_router
from .api.endpoints.channels import router as channels_router
from .api.endpoints.workflows import router as workflows_router
from .api.endpoints.calendar import router as calendar_router
from .api.endpoints.voice import router as voice_router
from .api.endpoints.secrets import router as secrets_router


async def _bootstrap_mcp_servers() -> None:
    """
    Ensure built-in MCP servers (Context7, etc.) are registered in the DB
    and their tool lists are synced on every startup.

    Servers are upserted by name — safe to run repeatedly.
    """
    import asyncio
    from datetime import datetime

    from sqlmodel import select as _select

    from .core.mcp_client import list_tools_sse, list_tools_stdio
    from .database import AsyncSessionLocal
    from .models.mcp_server import MCPServer

    BUILTIN_SERVERS = [
        {
            "name": "context7",
            "description": (
                "Real-time library documentation via Context7 MCP. "
                "Resolves any library name to its latest docs, code examples, and API reference."
            ),
            # Context7 uses the modern Streamable HTTP transport (POST-based, spec 2025-03-26)
            "server_type": "http",
            "url": "https://mcp.context7.com/mcp",
        },
    ]

    async with AsyncSessionLocal() as _sess:
        for srv in BUILTIN_SERVERS:
            # Upsert server record
            _res = await _sess.execute(
                _select(MCPServer).where(MCPServer.name == srv["name"])
            )
            server = _res.scalar_one_or_none()
            if not server:
                server = MCPServer(
                    name=srv["name"],
                    description=srv["description"],
                    server_type=srv["server_type"],
                    url=srv.get("url", ""),
                    command=srv.get("command", ""),
                    args=srv.get("args", []),
                    env_vars=srv.get("env_vars", {}),
                    enabled=True,
                )
                _sess.add(server)
                await _sess.commit()
                await _sess.refresh(server)
                logger.info(f"MCP server '{srv['name']}' registered.")
            else:
                # Always sync server_type/url from BUILTIN_SERVERS (may have changed)
                changed = False
                if server.server_type != srv["server_type"]:
                    server.server_type = srv["server_type"]
                    changed = True
                if server.url != srv.get("url", ""):
                    server.url = srv.get("url", "")
                    changed = True
                if changed:
                    server.status = "error"  # force re-sync
                    server.tools_cache = None
                    _sess.add(server)
                    await _sess.commit()
                    logger.info(
                        f"MCP server '{srv['name']}' config updated (server_type={srv['server_type']})."
                    )

            # Sync tools if cache is empty or server was in error state
            if not server.tools_cache or server.status == "error":
                try:
                    if server.server_type == "http":
                        from .core.mcp_client import list_tools_http

                        tools = await asyncio.wait_for(
                            list_tools_http(server.url, dict(server.headers or {})),
                            timeout=20,
                        )
                    elif server.server_type == "sse":
                        tools = await asyncio.wait_for(
                            list_tools_sse(server.url, dict(server.headers or {})),
                            timeout=20,
                        )
                    else:
                        tools = await asyncio.wait_for(
                            list_tools_stdio(
                                server.command,
                                list(server.args or []),
                                dict(server.env_vars or {}),
                            ),
                            timeout=20,
                        )

                    server.tools_cache = tools
                    server.status = "connected"
                    server.error_msg = ""
                    server.last_connected = datetime.utcnow()
                    _sess.add(server)
                    await _sess.commit()
                    logger.info(
                        f"MCP server '{server.name}' synced: {len(tools)} tools available."
                    )
                except Exception as _e:
                    server.status = "error"
                    server.error_msg = str(_e)[:500]
                    _sess.add(server)
                    await _sess.commit()
                    logger.warning(f"MCP server '{server.name}' sync failed: {_e}")
            else:
                logger.info(
                    f"MCP server '{server.name}' ready: {len(server.tools_cache)} tools cached."
                )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    global _docker_sandbox_service, _loop_detection_service, _tool_profile_service

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

    # Load tool integration configs from DB and apply to registry
    try:
        from .api.endpoints.integrations import (
            TOOL_CONFIG_SCHEMAS,
            _env_defaults,
            _reload_tool,
        )
        from .database import AsyncSessionLocal
        from .models.integration_config import IntegrationConfig
        from sqlmodel import select as _select

        async with AsyncSessionLocal() as _sess:
            _result = await _sess.execute(_select(IntegrationConfig))
            for _cfg in _result.scalars().all():
                if _cfg.tool_name in TOOL_CONFIG_SCHEMAS:
                    _live = {**_env_defaults(_cfg.tool_name), **_cfg.config}
                    _reload_tool(_cfg.tool_name, _live)
        logger.info("Tool integration configs loaded.")
    except Exception as exc:
        logger.warning(f"Tool config load skipped: {exc}")

    # Auto-register & sync built-in MCP servers (Context7, etc.)
    try:
        await _bootstrap_mcp_servers()
    except Exception as exc:
        logger.warning(f"MCP bootstrap skipped: {exc}")

    # Initialize channel plugins (Discord, Slack, WhatsApp)
    try:
        from . import channels  # noqa: F401 — triggers channel self-registration
        from .channels import get_channel_registry

        active = get_channel_registry().list_names()
        logger.info(f"Channels active: {active or 'none (set env vars to enable)'}")
    except Exception as exc:
        logger.warning(f"Channel init skipped: {exc}")

    # Setup Redis pub/sub for realtime
    try:
        manager = get_connection_manager()
        await manager.setup_redis()
        logger.info("Realtime system ready.")
    except Exception as exc:
        logger.warning(f"Realtime setup (Redis not available): {exc}")

    # Initialize ConversationManager (working memory / chat history)
    try:
        import redis.asyncio as aioredis
        from .core.conversation_manager import init_conversation_manager

        _redis_client = aioredis.from_url(
            settings.REDIS_URL, encoding="utf-8", decode_responses=False
        )
        init_conversation_manager(_redis_client)
        logger.info("ConversationManager initialized with Redis.")
    except Exception as exc:
        logger.warning(f"ConversationManager Redis init skipped: {exc}")

    # Initialize DockerSandboxService (secure isolated execution)
    try:
        from .services.docker_sandbox_service import DockerSandboxService, SandboxConfig

        _docker_sandbox_service = DockerSandboxService(
            base_config=SandboxConfig(
                enabled=True,
                image="python:3.12-slim",
                memory_limit="512m",
                timeout_seconds=300,
            )
        )
        await _docker_sandbox_service.initialize()
        logger.info("DockerSandboxService initialized.")
    except Exception as exc:
        logger.warning(f"DockerSandboxService init skipped: {exc}")
        _docker_sandbox_service = None

    # Initialize LoopDetectionService (prevents infinite tool-call loops)
    try:
        from .services.loop_detection_service import LoopDetectionService

        _loop_detection_service = LoopDetectionService(
            enabled=True, warning_threshold=8, critical_threshold=12, history_size=30
        )
        logger.info("LoopDetectionService initialized.")
    except Exception as exc:
        logger.warning(f"LoopDetectionService init skipped: {exc}")
        _loop_detection_service = None

    # Initialize ToolProfileService (granular tool access control)
    try:
        from .services.tool_profile_service import ToolProfileService

        _tool_profile_service = ToolProfileService()
        logger.info("ToolProfileService initialized.")
    except Exception as exc:
        logger.warning(f"ToolProfileService init skipped: {exc}")
        _tool_profile_service = None

    # Initialize PluginManager (discovers and loads plugins)
    try:
        from .plugins import get_plugin_manager as _get_pm

        _plugin_manager = _get_pm()
        await _plugin_manager.initialize()
        logger.info(
            f"PluginManager initialized with {len(_plugin_manager.list_plugins())} plugins."
        )
    except Exception as exc:
        logger.warning(f"PluginManager init skipped: {exc}")
        _plugin_manager = None

    yield

    # Shutdown
    logger.info("Shutting down Qubot backend...")

    # Shutdown DockerSandboxService
    if _docker_sandbox_service:
        try:
            await _docker_sandbox_service.shutdown()
            logger.info("DockerSandboxService shutdown complete.")
        except Exception as exc:
            logger.warning(f"DockerSandboxService shutdown error: {exc}")

    try:
        manager = get_connection_manager()
        await manager.close()
        logger.info("Realtime connections closed.")
    except Exception as exc:
        logger.error(f"Shutdown error: {exc}")

    # Shutdown PluginManager
    if _plugin_manager:
        try:
            await _plugin_manager.shutdown()
            logger.info("PluginManager shutdown complete.")
        except Exception as exc:
            logger.warning(f"PluginManager shutdown error: {exc}")


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
    allow_origins=settings.allowed_origins_list,
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
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    if not settings.DEBUG:
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
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
        content={
            "error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}
        },
    )


# Include routers
app.include_router(system_router, prefix=settings.API_V1_STR)
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(agents_router, prefix=settings.API_V1_STR)
app.include_router(tasks_router, prefix=settings.API_V1_STR)
app.include_router(
    tool_execution_router, prefix=settings.API_V1_STR
)  # must be before tools_router (static routes before /{uuid})
app.include_router(tools_router, prefix=settings.API_V1_STR)
app.include_router(llm_configs_router, prefix=settings.API_V1_STR)
app.include_router(memories_router, prefix=settings.API_V1_STR)
app.include_router(execution_router, prefix=settings.API_V1_STR)
app.include_router(websocket_router)
app.include_router(chat_router, prefix=settings.API_V1_STR)
app.include_router(telegram_router, prefix=settings.API_V1_STR)
app.include_router(config_router, prefix=settings.API_V1_STR)
app.include_router(integrations_router, prefix=settings.API_V1_STR)
app.include_router(skills_router, prefix=settings.API_V1_STR)
app.include_router(channels_router, prefix=settings.API_V1_STR)
app.include_router(workflows_router, prefix=settings.API_V1_STR)
app.include_router(calendar_router, prefix=settings.API_V1_STR)
app.include_router(voice_router, prefix=settings.API_V1_STR)
app.include_router(secrets_router, prefix=settings.API_V1_STR)


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
