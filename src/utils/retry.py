"""
Retry logic for production reliability.

Uses tenacity library for exponential backoff and retry handling.
Specifically designed for AWS Bedrock throttling and network issues.
"""

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log
)
import logging
from typing import Callable, TypeVar, Any
from utils.logger import get_logger

# Get structured logger
logger = get_logger(__name__)

# Type variable for generic functions
T = TypeVar('T')


def bedrock_retry(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator for Bedrock API calls with retry logic.

    Retries on:
    - Throttling errors (ThrottlingException)
    - Service errors (ServiceUnavailableException)
    - Network timeouts
    - Connection errors

    Strategy:
    - Max 3 attempts
    - Exponential backoff: 2s, 4s, 8s
    - Logs each retry attempt

    Args:
        func: Function to wrap with retry logic

    Returns:
        Wrapped function with retry capability

    Example:
        >>> @bedrock_retry
        ... def invoke_model(model_id, prompt):
        ...     return bedrock_client.invoke_model(...)
    """

    @retry(
        # Stop after 3 attempts total (1 initial + 2 retries)
        stop=stop_after_attempt(3),

        # Exponential backoff: 2s, 4s, 8s
        wait=wait_exponential(multiplier=1, min=2, max=10),

        # Retry on any exception (will log and retry)
        retry=retry_if_exception_type(Exception),

        # Log before sleeping for retry
        before_sleep=before_sleep_log(logger, logging.WARNING),

        # Log after each attempt
        after=after_log(logger, logging.DEBUG)
    )
    def wrapper(*args, **kwargs) -> T:
        """Wrapper function with retry logic."""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Check if it's a known retriable error
            error_str = str(e).lower()

            if any(keyword in error_str for keyword in [
                'throttling',
                'rate exceeded',
                'too many requests',
                'service unavailable',
                'timeout',
                'connection',
                'network'
            ]):
                # Log and let tenacity retry
                logger.warning("retriable_error_encountered",
                              error_message=str(e),
                              error_type=type(e).__name__)
                raise  # Re-raise to trigger retry

            # Non-retriable error, don't retry
            logger.error("non_retriable_error",
                        error_message=str(e),
                        error_type=type(e).__name__)
            raise  # Fail immediately

    return wrapper


def embedding_retry(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator for embedding API calls with retry logic.

    Similar to bedrock_retry but optimized for embedding operations
    which may have different rate limits.

    Args:
        func: Function to wrap with retry logic

    Returns:
        Wrapped function with retry capability
    """

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type(Exception),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    def wrapper(*args, **kwargs) -> T:
        """Wrapper function with retry logic."""
        return func(*args, **kwargs)

    return wrapper


def with_fallback(primary_func: Callable[..., T],
                  fallback_func: Callable[..., T],
                  fallback_exceptions: tuple = (Exception,)) -> Callable[..., T]:
    """
    Execute function with fallback on failure.

    Tries primary function first, falls back to fallback function
    if specified exceptions occur.

    Args:
        primary_func: Primary function to try
        fallback_func: Fallback function if primary fails
        fallback_exceptions: Exceptions that trigger fallback

    Returns:
        Function that tries primary then fallback

    Example:
        >>> def use_bedrock():
        ...     return bedrock_client.invoke(...)
        >>> def use_local():
        ...     return local_model.generate(...)
        >>> safe_generate = with_fallback(use_bedrock, use_local)
        >>> result = safe_generate()
    """

    def wrapper(*args, **kwargs) -> T:
        """Wrapper with fallback logic."""
        try:
            return primary_func(*args, **kwargs)
        except fallback_exceptions as e:
            logger.warning(
                "Primary function failed, using fallback",
                primary_error=str(e),
                fallback_func=fallback_func.__name__
            )
            return fallback_func(*args, **kwargs)

    return wrapper


def timeout_retry(timeout_seconds: int = 30):
    """
    Decorator for operations that might timeout.

    Args:
        timeout_seconds: Maximum time to wait before timeout

    Returns:
        Decorator function

    Example:
        >>> @timeout_retry(timeout_seconds=60)
        ... def long_running_operation():
        ...     # ... slow operation ...
        ...     pass
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @retry(
            stop=stop_after_attempt(2),
            wait=wait_exponential(multiplier=1, min=1, max=5),
            retry=retry_if_exception_type((TimeoutError, ConnectionError)),
            before_sleep=before_sleep_log(logger, logging.WARNING)
        )
        def wrapper(*args, **kwargs) -> T:
            """Wrapper with timeout and retry."""
            import signal

            def timeout_handler(signum, frame):
                raise TimeoutError(f"Operation timed out after {timeout_seconds}s")

            # Set timeout (Unix only)
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout_seconds)

            try:
                result = func(*args, **kwargs)
                signal.alarm(0)  # Cancel alarm
                return result
            finally:
                signal.signal(signal.SIGALRM, old_handler)

        return wrapper

    return decorator
