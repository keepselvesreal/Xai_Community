"""
External log adapters for collecting logs from various services.
"""

from .vercel_adapter import VercelLogAdapter
from .upstash_adapter import UpstashLogAdapter
from .cloudrun_adapter import CloudRunLogAdapter
from .atlas_adapter import AtlasLogAdapter

__all__ = [
    "VercelLogAdapter",
    "UpstashLogAdapter", 
    "CloudRunLogAdapter",
    "AtlasLogAdapter",
]