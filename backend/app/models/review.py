"""
Review model for OpenEdu Git.

This module re-exports the canonical Review model from app.db.models to maintain
backward compatibility with existing imports.
"""

# Re-export canonical model from app.db.models
from app.db.models import Review

# Keep the module namespace clean
__all__ = ["Review"]
