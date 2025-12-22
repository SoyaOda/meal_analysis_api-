"""
Core modules for Cloud Run optimization
"""
from .startup_optimizer import startup_optimizer, connection_pool
from .http_client import get_async_client, close_async_client, health_check_client

__all__ = [
    "startup_optimizer",
    "connection_pool",
    "get_async_client",
    "close_async_client",
    "health_check_client",
]
