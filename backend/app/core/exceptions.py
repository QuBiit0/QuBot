"""Custom exception classes for Qubot"""


class AppError(Exception):
    """Base application error"""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    """Resource not found"""

    def __init__(self, resource: str, id: str | None = None):
        msg = f"{resource} not found" if not id else f"{resource} '{id}' not found"
        super().__init__(msg, code="NOT_FOUND", status_code=404)


class ValidationError(AppError):
    """Validation error"""

    def __init__(self, message: str, details: list | None = None):
        self.details = details
        super().__init__(message, code="VALIDATION_ERROR", status_code=422)


class ConflictError(AppError):
    """Resource conflict"""

    def __init__(self, message: str):
        super().__init__(message, code="CONFLICT", status_code=409)


class AuthenticationError(AppError):
    """Authentication failure"""

    def __init__(self, message: str = "Not authenticated"):
        super().__init__(message, code="UNAUTHORIZED", status_code=401)


class AuthorizationError(AppError):
    """Authorization failure"""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, code="FORBIDDEN", status_code=403)
