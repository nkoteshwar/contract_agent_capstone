import uuid
from typing import Callable, Awaitable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from backend.shared.utils.logger import correlation_id_var, get_logger

logger = get_logger(__name__)

class TracingMiddleware(BaseHTTPMiddleware):
    """
    FastAPI Middleware to inject and track a unique correlation ID per request.
    This enables full request observability and correlation across logs and LLM calls.
    """
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # Extract existing correlation ID from headers or generate a new one
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        
        # Set the correlation ID in the current ContextVar block
        token = correlation_id_var.set(correlation_id)
        
        # Optional: Log the incoming request to verify correlation tracks
        logger.info(f"Handling incoming request: {request.method} {request.url.path}")
        
        try:
            # Process request
            response = await call_next(request)
            # Ensure the correlation ID flows back to the client
            response.headers["X-Correlation-ID"] = correlation_id
            return response
        finally:
            # Always reset the context variable afterward to prevent leakages across async tasks
            correlation_id_var.reset(token)
