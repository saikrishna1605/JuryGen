"""
Main API router for v1 endpoints.
"""

from fastapi import APIRouter

from .endpoints import health

# Create main API router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
    health.router,
    tags=["health"]
)

# Include auth endpoints
try:
    from .endpoints import auth
    api_router.include_router(
        auth.router,
        prefix="/auth",
        tags=["authentication"]
    )
except ImportError:
    pass  # Auth endpoints not available in minimal mode

# Include upload endpoints
try:
    from .endpoints import upload
    api_router.include_router(
        upload.router,
        tags=["upload"]
    )
except ImportError:
    pass  # Upload endpoints not available in minimal mode

# Include agents endpoints
try:
    from .endpoints import agents
    api_router.include_router(
        agents.router,
        tags=["agents"]
    )
except ImportError:
    pass  # Agents endpoints not available in minimal mode

# Include streaming endpoints
try:
    from .endpoints import streaming
    api_router.include_router(
        streaming.router,
        prefix="/streaming",
        tags=["streaming"]
    )
except ImportError:
    pass  # Streaming endpoints not available in minimal mode

# Include speech endpoints
try:
    from .endpoints import speech
    api_router.include_router(
        speech.router,
        tags=["speech"]
    )
except ImportError:
    pass  # Speech endpoints not available in minimal mode

# Include Q&A endpoints
try:
    from .endpoints import qa
    api_router.include_router(
        qa.router,
        tags=["qa"]
    )
except ImportError:
    pass  # Q&A endpoints not available in minimal mode

# Include translation endpoints
try:
    from .endpoints import translation
    api_router.include_router(
        translation.router,
        tags=["translation"]
    )
except ImportError:
    pass  # Translation endpoints not available in minimal mode

# Include jurisdiction endpoints
try:
    from .endpoints import jurisdiction
    api_router.include_router(
        jurisdiction.router,
        prefix="/jurisdiction",
        tags=["jurisdiction"]
    )
except ImportError:
    pass  # Jurisdiction endpoints not available in minimal mode

# Include PII endpoints
try:
    from .endpoints import pii
    api_router.include_router(
        pii.router,
        prefix="/pii",
        tags=["pii"]
    )
except ImportError:
    pass  # PII endpoints not available in minimal mode

# Include documents endpoints
try:
    from .endpoints import documents_simple as documents
    api_router.include_router(
        documents.router,
        tags=["documents"]
    )
except ImportError as e:
    print(f"Documents endpoints not available: {e}")
    pass  # Documents endpoints not available in minimal mode

# Include public documents endpoints (no auth required)
try:
    from .endpoints import documents_public
    api_router.include_router(
        documents_public.router,
        prefix="/public",
        tags=["public-documents"]
    )
except ImportError as e:
    print(f"Public documents endpoints not available: {e}")
    pass