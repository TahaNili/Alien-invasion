"""
MLController
- Uses AIManager.predict(features) to produce actions.
- Decision is made every `decision_interval_ms` to reduce CPU.
- Fallback to BaseController if no model available.

API:
    - __init__(self, entity, params)
    - observe(game_state) -> features dict
    - decide(observation) -> action dict
    - tick(ms_elapsed) -> maybe update internal timer
"""
from typing import Any, Dict
import time

from src.ai_manager import get_ai_manager
from .base_controller import BaseController


class MLController(BaseController):
    def __init__(self, entity: Any, params: Dict[str, Any] | None = None):
        super().__init__(entity, params)
        self.decision_interval_ms = (params or {}).get("decision_interval_ms", 150)
        self._last_decision_ts = 0
        self.ai = get_ai_manager()

    def observe(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        # Build a features dict compatible with AIManager expectations.
        # Minimal: use collect_frame_features shape or the entity-centered subset.
        # Caller responsible to provide a richer game_state if needed.
        features = game_state.get("features", {})
        return features

    def decide(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        now = int(time.time() * 1000)
        if now - self._last_decision_ts < self.decision_interval_ms:
            return self._last_action or {"move": None, "shoot": False}

        try:
            preds = self.ai.predict(observation)
            # preds is a dict per model: {name: {class: int, probabilities: [...]}}
            # choose a model (e.g., logistic) if available
            if "logistic" in preds:
                chosen = preds["logistic"]["class"]
            else:
                chosen = next(iter(preds.values()))["class"]

            # Map class to move action (0 none,1 left,2 right,3 up,4 down)
            move_map = {
                0: None,
                1: ( -1, 0),
                2: ( 1, 0),
                3: ( 0,-1),
                4: ( 0, 1),
            }
            action = {"move": move_map.get(chosen, None), "shoot": False}
            self._last_action = action
            self._last_decision_ts = now
            return action
        except Exception:
            # fallback
            return {"move": None, "shoot": False}
