# quack-core/src/quack-core/integrations/google/drive/utils/api.py
"""
API utilities for Google Drive integration.

This module provides wrapper functions for Google Drive API calls,
with consistent error handling and logging.
"""

from collections.abc import Callable
from typing import TypeVar

from googleapiclient.errors import HttpError

from quackcore.errors import QuackApiError
from quackcore.integrations.google.drive.protocols import DriveRequest

T = TypeVar("T")  # Generic type for API response
R = TypeVar("R")  # Generic type for request results


def execute_api_request(
    request: DriveRequest[R], error_message: str, api_method: str
) -> R:
    """
    Execute a Google Drive API request with consistent error handling.

    Args:
        request: Google Drive API request object.
        error_message: Error message prefix for exceptions.
        api_method: Name of the API method being called.

    Returns:
        R: API response.

    Raises:
        QuackApiError: If the API request fails.
    """
    try:
        return request.execute()
    except HttpError as e:
        raise QuackApiError(
            f"{error_message}: {e}",
            service="Google Drive",
            api_method=api_method,
            original_error=e,
        ) from e
    except Exception as e:
        raise QuackApiError(
            f"{error_message}: {e}",
            service="Google Drive",
            api_method=api_method,
            original_error=e,
        ) from e


def with_exponential_backoff(
    func: Callable[..., T],
    max_retries: int = 5,
    initial_delay: float = 1.0,
    max_delay: float = 30.0,
) -> Callable[..., T]:
    """
    Decorator for API calls with exponential backoff retry logic.

    Args:
        func: The function to wrap with retry logic.
        max_retries: Maximum number of retry attempts.
        initial_delay: Initial delay in seconds before the first retry.
        max_delay: Maximum delay in seconds before any retry.

    Returns:
        Callable: Wrapped function with retry logic.
    """
    import time
    from functools import wraps

    @wraps(func)
    def wrapper(*args: object, **kwargs: object) -> T:
        retry_count = 0
        delay = initial_delay

        while True:
            try:
                return func(*args, **kwargs)
            except HttpError as e:
                # Only retry on specific error codes (e.g., 429, 500, 503)
                if e.resp.status not in (429, 500, 503) or retry_count >= max_retries:
                    raise

                retry_count += 1
                time.sleep(delay)
                delay = min(delay * 2, max_delay)
            except Exception:
                # Don't retry on other exceptions
                raise

    return wrapper
