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
# 
# api_router.include_router(
#     jobs.router,
#     prefix="/jobs",
#     tags=["jobs"]
# )
# 
# api_router.include_router(
#     qa.router,
#     prefix="/qa",
#     tags=["qa"]
# )