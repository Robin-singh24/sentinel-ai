"""Exceptions for the Conversation Memory subsystem."""

from app.common.exceptions import SentinelBaseException


class SentinelMemoryError(SentinelBaseException):
    """Base exception for all Conversation Memory failures."""
    pass
