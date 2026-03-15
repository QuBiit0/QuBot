#!/usr/bin/env python3
"""
LMAgent - Backend Project Scaffolding Script
Genera la estructura base de un proyecto backend con FastAPI o NestJS.

Uso:
    python scaffold_backend.py --framework fastapi --name mi-proyecto
    python scaffold_backend.py --framework nestjs --name mi-proyecto
"""

import os
import sys
import argparse
from pathlib import Path


def create_fastapi_structure(project_name: str, base_path: Path):
    """Crea estructura de proyecto FastAPI estandarizada."""
    dirs = [
        f"{project_name}/app",
        f"{project_name}/app/api",
        f"{project_name}/app/api/v1",
        f"{project_name}/app/api/v1/endpoints",
        f"{project_name}/app/core",
        f"{project_name}/app/models",
        f"{project_name}/app/schemas",
        f"{project_name}/app/services",
        f"{project_name}/app/repositories",
        f"{project_name}/app/middleware",
        f"{project_name}/app/utils",
        f"{project_name}/tests",
        f"{project_name}/tests/unit",
        f"{project_name}/tests/integration",
        f"{project_name}/migrations",
        f"{project_name}/migrations/versions",
        f"{project_name}/docs",
    ]

    files = {
        f"{project_name}/app/__init__.py": "",
        f"{project_name}/app/main.py": '''"""FastAPI Application Entry Point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.VERSION}
''',
        f"{project_name}/app/core/__init__.py": "",
        f"{project_name}/app/core/config.py": '''"""Application Configuration."""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "LMAgent Backend")
    VERSION: str = os.getenv("VERSION", "0.1.0")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    # CORS
    ALLOWED_ORIGINS: list[str] = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

    class Config:
        env_file = ".env"


settings = Settings()
''',
        f"{project_name}/app/api/__init__.py": "",
        f"{project_name}/app/api/v1/__init__.py": "",
        f"{project_name}/app/api/v1/endpoints/__init__.py": "",
        f"{project_name}/app/models/__init__.py": "",
        f"{project_name}/app/schemas/__init__.py": "",
        f"{project_name}/app/services/__init__.py": "",
        f"{project_name}/app/repositories/__init__.py": "",
        f"{project_name}/app/middleware/__init__.py": "",
        f"{project_name}/app/utils/__init__.py": "",
        f"{project_name}/tests/__init__.py": "",
        f"{project_name}/tests/conftest.py": '''"""Test Configuration and Fixtures."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    """Async test client fixture."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
''',
        f"{project_name}/requirements.txt": """fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
sqlmodel>=0.0.22
alembic>=1.14.0
asyncpg>=0.30.0
httpx>=0.27.0
redis>=5.0.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.9
""",
        f"{project_name}/requirements-dev.txt": """pytest>=8.0.0
pytest-asyncio>=0.23.0
pytest-cov>=5.0.0
httpx>=0.27.0
ruff>=0.8.0
mypy>=1.13.0
faker>=30.0.0
""",
        f"{project_name}/.env.example": """# Application
PROJECT_NAME=mi-proyecto
VERSION=0.1.0
DEBUG=true

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/mydb

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=change-me-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
""",
        f"{project_name}/Dockerfile": """# Multi-stage build
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
""",
        f"{project_name}/pyproject.toml": f"""[project]
name = "{project_name}"
version = "0.1.0"
requires-python = ">=3.12"

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "W", "F", "I", "N", "UP", "S", "B", "A", "C4"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.mypy]
python_version = "3.12"
strict = true
""",
    }

    for d in dirs:
        (base_path / d).mkdir(parents=True, exist_ok=True)

    for filepath, content in files.items():
        (base_path / filepath).write_text(content, encoding="utf-8")

    print(f"✅ Proyecto FastAPI '{project_name}' creado exitosamente.")
    print(f"   📁 Ubicación: {base_path / project_name}")
    print(f"\n   Siguientes pasos:")
    print(f"   1. cd {project_name}")
    print(f"   2. cp .env.example .env")
    print(f"   3. pip install -r requirements.txt")
    print(f"   4. uvicorn app.main:app --reload")


def create_nestjs_structure(project_name: str, base_path: Path):
    """Crea estructura de proyecto NestJS estandarizada."""
    dirs = [
        f"{project_name}/src",
        f"{project_name}/src/common",
        f"{project_name}/src/common/decorators",
        f"{project_name}/src/common/filters",
        f"{project_name}/src/common/guards",
        f"{project_name}/src/common/interceptors",
        f"{project_name}/src/common/pipes",
        f"{project_name}/src/config",
        f"{project_name}/src/modules",
        f"{project_name}/src/modules/auth",
        f"{project_name}/src/modules/users",
        f"{project_name}/test",
        f"{project_name}/prisma",
    ]

    files = {
        f"{project_name}/src/main.ts": '''import { NestFactory } from "@nestjs/core";
import { ValidationPipe } from "@nestjs/common";
import { AppModule } from "./app.module";

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  app.enableCors({
    origin: process.env.ALLOWED_ORIGINS?.split(",") || ["http://localhost:3000"],
    credentials: true,
  });

  app.useGlobalPipes(new ValidationPipe({ whitelist: true, transform: true }));
  app.setGlobalPrefix("api/v1");

  const port = process.env.PORT || 3001;
  await app.listen(port);
  console.log(`🚀 Server running on http://localhost:${port}`);
}
bootstrap();
''',
        f"{project_name}/.env.example": """# Application
PORT=3001
NODE_ENV=development

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/mydb

# JWT
JWT_SECRET=change-me-in-production
JWT_EXPIRES_IN=30m

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
""",
    }

    for d in dirs:
        (base_path / d).mkdir(parents=True, exist_ok=True)

    for filepath, content in files.items():
        (base_path / filepath).write_text(content, encoding="utf-8")

    print(f"✅ Proyecto NestJS '{project_name}' creado exitosamente.")
    print(f"   📁 Ubicación: {base_path / project_name}")
    print(f"\n   Siguientes pasos:")
    print(f"   1. cd {project_name}")
    print(f"   2. cp .env.example .env")
    print(f"   3. npm install")
    print(f"   4. npm run start:dev")


def main():
    parser = argparse.ArgumentParser(
        description="LMAgent Backend Scaffolding — Genera estructura de proyecto backend"
    )
    parser.add_argument(
        "--framework", "-f",
        choices=["fastapi", "nestjs"],
        required=True,
        help="Framework a usar (fastapi o nestjs)"
    )
    parser.add_argument(
        "--name", "-n",
        required=True,
        help="Nombre del proyecto"
    )
    parser.add_argument(
        "--path", "-p",
        default=".",
        help="Ruta base donde crear el proyecto (default: directorio actual)"
    )

    args = parser.parse_args()
    base_path = Path(args.path).resolve()

    if args.framework == "fastapi":
        create_fastapi_structure(args.name, base_path)
    elif args.framework == "nestjs":
        create_nestjs_structure(args.name, base_path)


if __name__ == "__main__":
    main()
