"""
Base controller implementation for alien entities.
"""
from typing import Any, Dict, Optional

from src.protocols import ControllerProtocol

class DefaultController(ControllerProtocol):
    """A simple default controller that does nothing."""
    
    def __init__(self, entity: Any, params: Optional[Dict[str, Any]] = None) -> None:
        """Initialize with entity reference."""
        self.entity = entity
        self.params = params or {}
    
    def decide(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """Return no-op decision."""
        return {"move": None, "shoot": False}
    
    def observe(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """Return empty observation."""
        return {}