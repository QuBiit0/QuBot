# LMAgent Backend Python Template

Template de proyecto FastAPI con la estructura y configuración recomendada por LMAgent.

## Estructura

```
backend-python/
├── app/
│   ├── __init__.py
│   ├── main.py              # Entry point FastAPI
│   ├── config.py            # Configuración con Pydantic Settings
│   ├── routers/             # Endpoints API
│   │   ├── __init__.py
│   │   ├── health.py        # Health check
│   │   └── v1/              # API v1
│   │       ├── __init__.py
│   │       └── users.py     # Ejemplo: users endpoints
│   ├── services/            # Lógica de negocio
│   │   ├── __init__.py
│   │   └── user_service.py
│   ├── repositories/        # Acceso a datos
│   │   ├── __init__.py
│   │   └── user_repository.py
│   ├── models/              # SQLModel models
│   │   ├── __init__.py
│   │   └── user.py
│   ├── schemas/             # Pydantic schemas
│   │   ├── __init__.py
│   │   └── user.py
│   └── core/                # Utilidades compartidas
│       ├── __init__.py
│       ├── database.py      # Database connection
│       └── exceptions.py    # Custom exceptions
├── tests/
│   ├── conftest.py          # Fixtures de pytest
│   └── test_health.py
├── Dockerfile
├── requirements.txt
├── requirements-dev.txt
└── pyproject.toml
```

## Quick Start

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores

# Ejecutar en desarrollo
uvicorn app.main:app --reload

# Ejecutar tests
pytest --cov=app
```

## Dependencias Principales

- **FastAPI**: Framework web async
- **SQLModel**: ORM + validación
- **Pydantic**: Validación de datos
- **Uvicorn**: Servidor ASGI
- **Redis**: Cache
- **pytest**: Testing

## Patrones de Código

Ver `rules/code-style.md` y `personas/backend-engineer.md` para guías detalladas.
