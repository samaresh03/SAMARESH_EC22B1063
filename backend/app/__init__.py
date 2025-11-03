"""Quant Trading Dashboard Backend Application"""

__version__ = "0.1.0"
__author__ = "Quant Team"

from .models import init_db, get_db

__all__ = ["init_db", "get_db"]
