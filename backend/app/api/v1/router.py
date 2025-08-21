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