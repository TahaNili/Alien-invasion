"""
BaseController
- Wrapper around existing Alien behavior
- API:
    - __init__(self, entity, params)
    - observe(self, game_state) -> dict
    - decide(self, observation) -> dict  # {move: (dx,dy), shoot: bool}
    - on_event(self, event)
"""

from typing import Any, Dict

class BaseController:
    def __init__(self, entity: Any, params: Dict[str, Any] | None = None):
        self.entity = entity
        self.params = params or {}
        self._last_action = None

    def observe(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        # Provide minimal observation derived from entity and game_state
        return {
            "pos": (self.entity.rect.centerx, self.entity.rect.centery),
            "hp": getattr(self.entity, "health", None),
        }

    def decide(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        # Default behavior: delegate back to entity.update-like logic
        # We'll return a simple action dict that the game loop can interpret.
        # Action: {"move": (dx, dy), "shoot": bool}
        # For BaseController we just do no special move (entity.update handles movement)
        return {"move": None, "shoot": False}

    def on_event(self, event: Dict[str, Any]) -> None:
        # Placeholder for event handling (damage, pickup)
        pass
