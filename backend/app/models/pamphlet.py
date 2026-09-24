"""
Pamphlet and PamphletVersion models for OpenEdu Git.

This module re-exports the canonical models from app.db.models to maintain
backward compatibility with existing imports.
"""

# Re-export canonical models from app.db.models
from app.db.models import (
    Pamphlet,
    PamphletVersion,
    Fork as PamphletFork,
    MergeRequest,
    MergeRequestStatus,
)

# Keep the module namespace clean
__all__ = [
    "Pamphlet",
    "PamphletVersion",
    "PamphletFork",
    "MergeRequest",
    "MergeRequestStatus",
]
