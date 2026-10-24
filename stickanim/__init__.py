"""stickanim — procedural stick-figure action animation (desktop vs. cursor style)."""

from . import poses
from .actors import Cursor, Figure
from .desktop import Desktop
from .scene import Scene

__all__ = ["Scene", "Figure", "Cursor", "Desktop", "poses"]
