# quack-core/src/quack-core/adapters/http/__init__.py
"""
HTTP Adapter for QuackCore.

Optional FastAPI-based HTTP API that exposes QuackCore operations
via REST endpoints. Only available when the 'http' extra is installed.
"""

try:
    from .app import create_app
    from .config import HttpAdapterConfig
    from .service import run

    __all__ = ["create_app", "HttpAdapterConfig", "run"]
except ImportError:
    # FastAPI not available - this is expected when http extra not installed
    def create_app(*args, **kwargs):
        raise ImportError(
            "HTTP adapter requires FastAPI. Install with: pip install quack-core[http]"
        )


    def run(*args, **kwargs):
        raise ImportError(
            "HTTP adapter requires FastAPI. Install with: pip install quack-core[http]"
        )


    class HttpAdapterConfig:
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "HTTP adapter requires FastAPI. Install with: pip install quack-core[http]"
            )


    __all__ = ["create_app", "HttpAdapterConfig", "run"]