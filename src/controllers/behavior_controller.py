"""
BehaviorController
- state-machine: patrol -> chase -> fight -> pickup -> flee
- advanced behaviors: dodge, predictive shooting, use_item

API like other controllers
"""
from typing import Any, Dict
import math

from .base_controller import BaseController


class BehaviorController(BaseController):
    def __init__(self, entity: Any, params: Dict[str, Any] | None = None):
        super().__init__(entity, params)
        self.state = "patrol"
        self.params = params or {}
        self.dodge_cooldown_ms = self.params.get("dodge_cooldown_ms", 1000)
        self.last_dodge_ts = 0

    def observe(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        return {"pos": (self.entity.rect.centerx, self.entity.rect.centery), "hp": getattr(self.entity, "health", None)}

    def decide(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        # Very simple illustrative FSM logic
        dx, dy = 0, 0
        ship = observation.get("ship")
        if ship:
            # compute distance
            dx = ship[0] - self.entity.rect.centerx
            dy = ship[1] - self.entity.rect.centery
            dist = math.hypot(dx, dy)
            if dist < 200:
                self.state = "chase"
            else:
                self.state = "patrol"

        if self.state == "patrol":
            return {"move": (0, 0), "shoot": False}
        elif self.state == "chase":
            # move toward player
            nx = 1 if dx > 0 else -1 if dx < 0 else 0
            ny = 1 if dy > 0 else -1 if dy < 0 else 0
            return {"move": (nx, ny), "shoot": True}
        else:
            return {"move": None, "shoot": False}
