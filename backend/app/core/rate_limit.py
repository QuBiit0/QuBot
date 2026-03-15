"""
Rate limiting configuration using slowapi
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from functools import wraps
import redis

from ..config import settings

# Create limiter with Redis storage if available
try:
    redis_client = redis.from_url(settings.REDIS_URL)
    redis_client.ping()
    
    limiter = Limiter(
        key_func=get_remote_address,
        storage_uri=settings.REDIS_URL,
        strategy="moving-window",
    )
    print("Rate limiting using Redis storage")
except:
    # Fallback to memory storage
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["100/minute"],
    )
    print("Rate limiting using memory storage")


def get_user_identifier(request: Request) -> str:
    """Get identifier for rate limiting (user ID if authenticated, IP otherwise)"""
    # Try to get user from request state (set by auth middleware)
    user = getattr(request.state, "user", None)
    if user:
        return f"user:{user.id}"
    
    # Fall back to IP address
    return get_remote_address(request)


def user_specific_limit(limit_string: str):
    """
    Decorator for user-specific rate limiting.
    
    Usage:
        @app.get("/expensive-endpoint")
        @user_specific_limit("10/minute")
        async def endpoint():
            return {"data": "..."}
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Set custom key function for this request
            request.state.rate_limit_key = get_user_identifier(request)
            return await func(request, *args, **kwargs)
        
        # Apply rate limit
        return limiter.limit(limit_string, key_func=get_user_identifier)(wrapper)
    return decorator


# Rate limit configurations for different endpoint types
RATE_LIMITS = {
    # Authentication endpoints
    "auth": {
        "login": ["5/minute", "20/hour"],  # Prevent brute force
        "register": ["3/minute", "10/hour"],  # Prevent spam
        "refresh": ["10/minute"],
    },
    
    # API endpoints
    "api": {
        "default": ["100/minute", "1000/hour"],
        "read": ["200/minute", "2000/hour"],
        "write": ["50/minute", "500/hour"],
        "execute": ["10/minute", "100/hour"],  # Task execution
    },
    
    # WebSocket
    "websocket": {
        "connections": ["10/minute"],  # Connection attempts
    },
}


def apply_rate_limits(app):
    """Apply rate limiting to FastAPI app"""
    # Add limiter to app state
    app.state.limiter = limiter
    
    # Add exception handler
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    return app
