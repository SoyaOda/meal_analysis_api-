"""
Admin Panel for Freeform USDA Meal Analysis API
Dynamic configuration management with Firestore backend
"""

from .config_manager import ConfigManager, get_config_manager
from .router import router as admin_router

__all__ = ["ConfigManager", "get_config_manager", "admin_router"]
