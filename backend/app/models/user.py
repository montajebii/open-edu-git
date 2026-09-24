"""
User model for OpenEdu Git.

This module re-exports the canonical User model from app.db.models to maintain
backward compatibility with existing imports.
"""

# Re-export canonical model from app.db.models
from app.db.models import User

# Keep the module namespace clean
__all__ = ["User"]
