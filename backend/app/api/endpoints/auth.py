"""
Authentication API Endpoints
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...config import settings
from ...core.rate_limit import limiter
from ...core.security import (
    cleanup_expired_sessions,
    create_access_token,
    create_refresh_token,
    create_user_session,
    decode_token,
    get_current_user,
    get_password_hash,
    revoke_all_user_sessions,
    revoke_session,
    verify_password,
)
from ...core.security import (
    generate_api_key as _generate_api_key,
)
from ...database import get_session
from ...models.user import (
    Token,
    User,
    UserCreate,
    UserLogin,
    UserResponse,
    UserRole,
    UserSession,
)

router = APIRouter()
security = HTTPBearer(auto_error=False)


@router.post("/auth/register", response_model=UserResponse)
@limiter.limit("5/minute")
async def register(
    request: Request,
    user_data: UserCreate,
    session: AsyncSession = Depends(get_session),
):
    """Register a new user account"""
    # Check if email exists
    result = await session.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Check if username exists
    result = await session.execute(
        select(User).where(User.username == user_data.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    # Create user
    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=UserRole.USER,
        is_active=True,
    )

    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user


@router.post("/auth/login", response_model=Token)
@limiter.limit("10/minute")
async def login(
    request: Request,
    response: Response,
    login_data: UserLogin,
    session: AsyncSession = Depends(get_session),
):
    """Login and receive access and refresh tokens"""
    # Find user by email
    result = await session.execute(select(User).where(User.email == login_data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    # Update last login
    user.last_login = datetime.utcnow()
    user.login_count += 1

    # Create tokens
    access_token, access_jti = create_access_token(
        user_id=str(user.id),
        role=user.role.value if hasattr(user.role, "value") else str(user.role),
    )
    refresh_token, refresh_jti, refresh_expires = create_refresh_token(
        user_id=str(user.id),
    )

    # Create session
    await create_user_session(
        session=session,
        user_id=str(user.id),
        jti=refresh_jti,
        expires_at=refresh_expires,
        request=request,
    )

    await session.commit()

    # Set refresh token in HTTP-only cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=not settings.DEBUG,  # False in dev (HTTP), True in prod (HTTPS)
        samesite="lax",
        max_age=7 * 24 * 60 * 60,  # 7 days
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=60 * 24 * 60,  # 1 day in seconds
    )


@router.post("/auth/refresh", response_model=Token)
async def refresh_token(
    response: Response,
    refresh_token: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    """Refresh access token using refresh token"""
    # Get refresh token from cookie or body
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required",
        )

    # Decode and validate refresh token
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = payload.get("sub")
    jti = payload.get("jti")

    # Check if session is valid
    result = await session.execute(
        select(UserSession).where(
            UserSession.token_jti == jti,
            UserSession.is_revoked == False,
        )
    )
    user_session = result.scalar_one_or_none()

    if not user_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session revoked or expired",
        )

    # Get user
    result = await session.execute(
        select(User).where(User.id == user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Revoke old session
    await revoke_session(session, jti)

    # Create new tokens
    new_access_token, new_access_jti = create_access_token(
        user_id=str(user.id),
        role=user.role.value if hasattr(user.role, "value") else str(user.role),
    )
    new_refresh_token, new_refresh_jti, new_refresh_expires = create_refresh_token(
        user_id=str(user.id),
    )

    # Create new session
    await create_user_session(
        session=session,
        user_id=str(user.id),
        jti=new_refresh_jti,
        expires_at=new_refresh_expires,
    )

    await session.commit()

    # Set new refresh token in cookie
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
    )

    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=60 * 24 * 60,
    )


@router.post("/auth/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Logout and revoke current session"""
    # Extract JTI from the current access token to revoke specific session
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        payload = decode_token(token)
        if payload and payload.get("jti"):
            await revoke_session(session, payload["jti"])
        else:
            await revoke_all_user_sessions(session, str(current_user.id))
    else:
        await revoke_all_user_sessions(session, str(current_user.id))

    await session.commit()

    # Clear cookie
    response.delete_cookie("refresh_token")

    return {"message": "Successfully logged out"}


@router.post("/auth/logout-all")
async def logout_all_devices(
    response: Response,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Logout from all devices"""
    count = await revoke_all_user_sessions(session, str(current_user.id))
    await session.commit()

    # Clear cookie
    response.delete_cookie("refresh_token")

    return {"message": f"Logged out from {count} devices"}


@router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """Get current authenticated user information"""
    return current_user


@router.put("/auth/me")
async def update_current_user(
    full_name: str | None = None,
    avatar_url: str | None = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Update current user profile"""
    if full_name is not None:
        current_user.full_name = full_name
    if avatar_url is not None:
        current_user.avatar_url = avatar_url

    current_user.updated_at = datetime.utcnow()
    await session.commit()
    await session.refresh(current_user)

    return current_user


@router.post("/auth/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Change user password"""
    # Verify current password
    if not verify_password(current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password",
        )

    # Update password
    current_user.hashed_password = get_password_hash(new_password)
    current_user.updated_at = datetime.utcnow()

    # Revoke all sessions (force re-login)
    await revoke_all_user_sessions(session, str(current_user.id))
    await session.commit()

    return {"message": "Password changed successfully. Please login again."}


@router.post("/auth/api-key")
async def generate_api_key(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Generate a new API key for programmatic access"""
    api_key = _generate_api_key()

    current_user.api_key = api_key
    current_user.api_key_created_at = datetime.utcnow()
    current_user.updated_at = datetime.utcnow()

    await session.commit()

    return {
        "api_key": api_key,
        "created_at": current_user.api_key_created_at,
        "message": "Save this API key - it won't be shown again",
    }


@router.delete("/auth/api-key")
async def revoke_api_key(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Revoke API key"""
    current_user.api_key = None
    current_user.api_key_created_at = None
    current_user.updated_at = datetime.utcnow()

    await session.commit()

    return {"message": "API key revoked successfully"}


# Admin endpoints


@router.get("/admin/users")
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List all users (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    result = await session.execute(select(User).offset(skip).limit(limit))
    users = result.scalars().all()

    return {
        "data": [
            {
                "id": str(u.id),
                "email": u.email,
                "username": u.username,
                "role": u.role,
                "is_active": u.is_active,
                "created_at": u.created_at,
            }
            for u in users
        ]
    }


@router.post("/admin/cleanup-sessions")
async def cleanup_sessions(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Clean up expired sessions (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    count = await cleanup_expired_sessions(session)

    return {"message": f"Cleaned up {count} expired sessions"}
