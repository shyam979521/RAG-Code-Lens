"""Backward-compatible configuration import.

New modules should import ``Config`` from ``app.config``.
"""

from app.config import Config

__all__ = ["Config"]
