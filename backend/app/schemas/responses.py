"""Standardized API response schemas"""
from typing import Any

from pydantic import BaseModel


class PaginatedMeta(BaseModel):
    """Pagination metadata"""

    page: int
    limit: int
    total: int
    total_pages: int


class APIResponse[T](BaseModel):
    """Standard success response"""

    data: T
    meta: PaginatedMeta | None = None


class APIErrorDetail(BaseModel):
    """Error detail"""

    code: str
    message: str
    details: list[dict[str, Any]] | None = None


class APIErrorResponse(BaseModel):
    """Standard error response"""

    error: APIErrorDetail
