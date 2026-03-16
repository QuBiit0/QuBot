"""
ID Generator utilities
"""

import uuid


def generate_id(prefix: str | None = None) -> str:
    """
    Generate a unique ID.

    Args:
        prefix: Optional prefix for the ID (e.g., 'agent', 'task')

    Returns:
        A unique string ID
    """
    uid = str(uuid.uuid4())[:8]  # Use first 8 chars of UUID for brevity
    if prefix:
        return f"{prefix}-{uid}"
    return uid


def generate_uuid() -> str:
    """Generate a full UUID string."""
    return str(uuid.uuid4())
