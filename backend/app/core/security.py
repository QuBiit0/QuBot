"""
Security utilities - JWT, password hashing, and authentication
"""

from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ..config import settings
from ..database import get_session
from ..models.user import User, UserRole, UserSession

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day
REFRESH_TOKEN_EXPIRE_DAYS = 7  # 7 days

# Security scheme for Swagger UI
security_scheme = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(
    user_id: str,
    role: str,
    expires_delta: timedelta | None = None,
) -> tuple[str, str]:
    """
    Create a JWT access token.

    Returns:
        Tuple of (token, jti)
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    jti = str(uuid4())
    to_encode = {
        "sub": user_id,
        "exp": expire,
        "jti": jti,
        "type": "access",
        "role": role,
        "iat": datetime.utcnow(),
    }

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt, jti


def create_refresh_token(user_id: str) -> tuple[str, str, datetime]:
    """
    Create a JWT refresh token.

    Returns:
        Tuple of (token, jti, expires_at)
    """
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    jti = str(uuid4())

    to_encode = {
        "sub": user_id,
        "exp": expire,
        "jti": jti,
        "type": "refresh",
        "iat": datetime.utcnow(),
    }

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt, jti, expire


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    """
    Dependency to get the current authenticated user.

    Usage:
        @app.get("/protected")
        async def protected_route(user: User = Depends(get_current_user)):
            return {"message": f"Hello {user.username}"}
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not credentials:
        raise credentials_exception

    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("sub")
    jti: str = payload.get("jti")
    token_type: str = payload.get("type")

    if user_id is None or jti is None:
        raise credentials_exception

    if token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    # Check if session is revoked
    session_result = await session.execute(
        select(UserSession).where(
            UserSession.token_jti == jti,
            UserSession.is_revoked == False,
        )
    )
    user_session = session_result.scalar_one_or_none()

    if user_session is None:
        raise credentials_exception

    # Get user
    result = await session.execute(
        select(User).where(User.id == user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency to get current user and verify they are active"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


def require_role(required_role: UserRole):
    """
    Dependency factory to require specific role.

    Usage:
        @app.get("/admin-only")
        async def admin_route(user: User = Depends(require_role(UserRole.ADMIN))):
            return {"message": "Admin access granted"}
    """

    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        # Admin can access everything
        if current_user.role == UserRole.ADMIN:
            return current_user

        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {required_role} required",
            )
        return current_user

    return role_checker


async def create_user_session(
    session: AsyncSession,
    user_id: str,
    jti: str,
    expires_at: datetime,
    request: Request | None = None,
) -> UserSession:
    """Create a new user session"""
    user_session = UserSession(
        user_id=user_id,
        token_jti=jti,
        expires_at=expires_at,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )

    session.add(user_session)
    await session.commit()
    await session.refresh(user_session)

    return user_session


async def revoke_session(session: AsyncSession, jti: str) -> bool:
    """Revoke a user session by JTI"""
    result = await session.execute(
        select(UserSession).where(UserSession.token_jti == jti)
    )
    user_session = result.scalar_one_or_none()

    if user_session:
        user_session.is_revoked = True
        await session.commit()
        return True

    return False


async def revoke_all_user_sessions(session: AsyncSession, user_id: str) -> int:
    """Revoke all sessions for a user"""
    result = await session.execute(
        select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.is_revoked == False,
        )
    )
    sessions = result.scalars().all()

    count = 0
    for s in sessions:
        s.is_revoked = True
        count += 1

    await session.commit()
    return count


async def cleanup_expired_sessions(session: AsyncSession) -> int:
    """Delete expired sessions from database"""
    from sqlalchemy import delete

    result = await session.execute(
        delete(UserSession).where(UserSession.expires_at < datetime.utcnow())
    )
    await session.commit()
    return result.rowcount


def generate_api_key() -> str:
    """Generate a secure API key"""
    return f"qubot_{uuid4().hex}_{uuid4().hex}"


async def get_user_by_api_key(session: AsyncSession, api_key: str) -> User | None:
    """Get user by API key"""
    result = await session.execute(
        select(User).where(
            User.api_key == api_key,
            User.is_active == True,
        )
    )
    return result.scalar_one_or_none()


async def authenticate_api_key_or_token(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> User | None:
    """
    Authenticate using either API key (header) or JWT token (Authorization header).

    This allows programmatic access with API keys while maintaining JWT for web access.
    """
    # Check for API key first
    api_key = request.headers.get("X-API-Key")
    if api_key:
        user = await get_user_by_api_key(session, api_key)
        if user:
            return user

    # Fall back to JWT token
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        payload = decode_token(token)

        if payload and payload.get("type") == "access":
            user_id = payload.get("sub")
            if user_id:
                result = await session.execute(
                    select(User).where(User.id == user_id, User.is_active == True)
                )
                return result.scalar_one_or_none()

    return None
