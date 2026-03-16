"""
Authentication utilities — re-exports from security module.

All authentication logic lives in core/security.py.
This module exists for backward compatibility of imports.
"""

from .security import (
    get_current_active_user,
    get_current_user,
)

__all__ = [
    "get_current_user",
    "get_current_active_user",
]
