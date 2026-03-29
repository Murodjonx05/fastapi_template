from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from src.utils.logging import get_logger

logger = get_logger("exceptions")
class DomainError(Exception):
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR

class NotFoundError(DomainError):
    status_code: int = status.HTTP_404_NOT_FOUND

class AlreadyExistsError(DomainError):
    status_code: int = status.HTTP_409_CONFLICT

class ValidationError(DomainError):
    status_code: int = status.HTTP_400_BAD_REQUEST

class UnauthorizedError(DomainError):
    status_code: int = status.HTTP_401_UNAUTHORIZED

def setup_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers for the application."""

    @app.exception_handler(DomainError)
    async def domain_exception_handler(request: Request, exc: DomainError):
        """Handle domain-specific exceptions polymorphism."""
        if exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
            logger.error(f"Unhandled domain exception: {type(exc).__name__}: {exc}")

        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": str(exc), "type": type(exc).__name__}
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Fallback handler for any unhandled exceptions."""
        logger.exception(f"Unhandled system error: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected server error occurred.", "type": "InternalServerError"}
        )
