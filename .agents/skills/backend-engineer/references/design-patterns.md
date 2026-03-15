# Design Patterns Reference — Backend Engineer

> Patrones de diseño más usados en desarrollo backend con FastAPI y NestJS.

## Patrones Estructurales

### Repository Pattern

Separa la lógica de acceso a datos de la lógica de negocio.

```python
# app/repositories/base.py
from typing import TypeVar, Generic, Type, Optional
from sqlmodel import Session, SQLModel, select

T = TypeVar("T", bound=SQLModel)


class BaseRepository(Generic[T]):
    """Repositorio genérico con operaciones CRUD."""

    def __init__(self, model: Type[T], session: Session):
        self.model = model
        self.session = session

    def get_by_id(self, id: str) -> Optional[T]:
        return self.session.get(self.model, id)

    def get_all(self, skip: int = 0, limit: int = 100) -> list[T]:
        statement = select(self.model).offset(skip).limit(limit)
        return self.session.exec(statement).all()

    def create(self, obj: T) -> T:
        self.session.add(obj)
        self.session.commit()
        self.session.refresh(obj)
        return obj

    def update(self, obj: T) -> T:
        self.session.add(obj)
        self.session.commit()
        self.session.refresh(obj)
        return obj

    def delete(self, id: str) -> bool:
        obj = self.get_by_id(id)
        if obj:
            self.session.delete(obj)
            self.session.commit()
            return True
        return False
```

### Service Layer Pattern

Encapsula lógica de negocio entre controllers y repositories.

```python
# app/services/user_service.py
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate
from app.models.user import User


class UserService:
    """Lógica de negocio para usuarios."""

    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def create_user(self, data: UserCreate) -> User:
        # Validación de negocio
        existing = self.repo.get_by_email(data.email)
        if existing:
            raise ValueError(f"Email {data.email} ya registrado")

        user = User(**data.model_dump())
        return self.repo.create(user)

    async def get_user(self, user_id: str) -> User:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"Usuario {user_id} no encontrado")
        return user
```

### Dependency Injection (FastAPI)

```python
# app/api/deps.py
from typing import Annotated
from fastapi import Depends
from sqlmodel import Session
from app.core.database import get_session
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService


def get_user_repository(
    session: Annotated[Session, Depends(get_session)]
) -> UserRepository:
    return UserRepository(session)


def get_user_service(
    repo: Annotated[UserRepository, Depends(get_user_repository)]
) -> UserService:
    return UserService(repo)
```

## Patrones de Resiliencia

### Circuit Breaker

```python
import time
from enum import Enum
from typing import Callable, Any


class CircuitState(Enum):
    CLOSED = "closed"       # Funcionando normal
    OPEN = "open"           # Cortado, rechaza requests
    HALF_OPEN = "half_open" # Probando si se recuperó


class CircuitBreaker:
    """Implementación simple de Circuit Breaker."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = 0

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
```

### Retry with Backoff

```python
import asyncio
import random
from functools import wraps


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
):
    """Decorator para retry con exponential backoff + jitter."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries:
                        raise e
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    jitter = random.uniform(0, delay * 0.1)
                    await asyncio.sleep(delay + jitter)
        return wrapper
    return decorator
```

## Anti-Patterns a Evitar

| ❌ Anti-Pattern | ✅ Alternativa |
|----------------|---------------|
| Fat Controller (lógica en endpoint) | Service Layer Pattern |
| God Object (clase que hace todo) | Single Responsibility |
| N+1 Queries | Eager loading / JOINs |
| Hardcoded configs | Environment variables |
| String SQL | ORM / Prepared statements |
| Catch-all exceptions | Specific exception handling |
| Synchronous blocking in async | `asyncio.to_thread()` |
| Mutable default arguments | `field(default_factory=list)` |
