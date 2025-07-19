"""
Service layer implementations for the logging system.
"""

from .log_service import LogService
from .external_log_collector import ExternalLogCollectorService

__all__ = ["LogService", "ExternalLogCollectorService"]