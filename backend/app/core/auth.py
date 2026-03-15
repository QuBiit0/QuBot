"""
Authentication utilities
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """
    Get current user from JWT token.
    
    For now, this is a simplified version that returns a mock user.
    In production, this should validate the JWT token and return the actual user.
    """
    # TODO: Implement proper JWT validation
    # For now, return a mock user for development
    if credentials:
        return {
            "id": "user-1",
            "email": "admin@qubot.local",
            "name": "Admin User",
            "role": "admin"
        }
    return None


async def get_current_active_user(
    current_user: Optional[dict] = Depends(get_current_user)
) -> dict:
    """
    Get current active user or raise 401.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user
