from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from src.crud.user import UserError, UserAlreadyExistsError, UserNotFoundError, InvalidCredentialsError
from src.schemas.i18n import (
    I18nError, 
    TranslationAlreadyExistsError, 
    TranslationNotFoundError, 
    TranslationValidationError,
    TranslationDeleteNotFoundError
)
from src.utils.logging import get_logger

logger = get_logger("exceptions")

def setup_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers for the application."""

    @app.exception_handler(UserError)
    @app.exception_handler(I18nError)
    async def domain_exception_handler(request: Request, exc: Exception):
        """Handle domain-specific exceptions and map them to HTTP status codes."""
        
        # Mapping table for flat lookup (Cleaner than deep if/else)
        status_map = {
            # User Domain
            UserAlreadyExistsError: status.HTTP_409_CONFLICT,
            UserNotFoundError: status.HTTP_404_NOT_FOUND,
            InvalidCredentialsError: status.HTTP_401_UNAUTHORIZED,
            
            # I18n Domain
            TranslationAlreadyExistsError: status.HTTP_409_CONFLICT,
            TranslationNotFoundError: status.HTTP_404_NOT_FOUND,
            TranslationDeleteNotFoundError: status.HTTP_404_NOT_FOUND,
            TranslationValidationError: status.HTTP_400_BAD_REQUEST,
        }
        
        status_code = next((s for t, s in status_map.items() if isinstance(exc, t)), status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        if status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
            logger.error(f"Unhandled domain exception: {type(exc).__name__}: {exc}")

        return JSONResponse(
            status_code=status_code,
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
