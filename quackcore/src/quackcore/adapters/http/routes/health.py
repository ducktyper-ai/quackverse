# File: quackcore/src/quackcore/adapters/http/routes/health.py
"""
Health check routes.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/live")
def health_live():
    """Liveness check."""
    return {"ok": True}


@router.get("/ready")
def health_ready():
    """Readiness check."""
    return {"ok": True}

