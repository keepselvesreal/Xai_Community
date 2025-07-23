"""
External log adapters for collecting logs from various services.
"""

from .vercel_adapter import VercelLogAdapter
from .upstash_adapter import UpstashLogAdapter
from .cloudrun_adapter import CloudRunLogAdapter
from .atlas_adapter import AtlasLogAdapter
from .sentry_adapter import SentryLogAdapter
from .cache_adapter import LoggingCacheAdapter, get_logging_cache_adapter

__all__ = [
    "VercelLogAdapter",
    "UpstashLogAdapter",
    "CloudRunLogAdapter",
    "AtlasLogAdapter",
    "SentryLogAdapter",
    "LoggingCacheAdapter",
    "get_logging_cache_adapter",
]
