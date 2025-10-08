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
import numpy as np

from src.ai_manager import get_ai_manager
from .base_controller import BaseController


class MLController(BaseController):
    def __init__(self, entity: Any, params: Dict[str, Any] | None = None):
        super().__init__(entity, params)
        self.decision_interval_ms = (params or {}).get("decision_interval_ms", 150)
        self._last_decision_ts = 0
        self.ai = get_ai_manager()

    def observe(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        # Enhanced feature extraction for better targeting
        features = game_state.get("features", {})
        
        # Add target tracking features
        if "player" in game_state:
            player = game_state["player"]
            features["player_x"] = player.rect.x
            features["player_y"] = player.rect.y
            features["distance_to_player"] = ((self.entity.rect.x - player.rect.x) ** 2 + 
                                           (self.entity.rect.y - player.rect.y) ** 2) ** 0.5
            features["angle_to_player"] = np.arctan2(player.rect.y - self.entity.rect.y,
                                                   player.rect.x - self.entity.rect.x)
            
        # Add dodge features
        if "bullets" in game_state:
            bullets = game_state["bullets"]
            nearest_bullet_dist = float('inf')
            for bullet in bullets:
                if bullet.rect:  # Ensure bullet has position
                    dist = ((self.entity.rect.x - bullet.rect.x) ** 2 + 
                           (self.entity.rect.y - bullet.rect.y) ** 2) ** 0.5
                    nearest_bullet_dist = min(nearest_bullet_dist, dist)
            features["nearest_bullet_distance"] = nearest_bullet_dist
            
        return features

    def decide(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        now = int(time.time() * 1000)
        if now - self._last_decision_ts < self.decision_interval_ms:
            return self._last_action or {"move": None, "shoot": False}

        try:
            preds = self.ai.predict(observation)
            
            # Enhanced movement decision
            if "distance_to_player" in observation and "nearest_bullet_distance" in observation:
                # Dodge if bullet is too close
                if observation["nearest_bullet_distance"] < 100:  # Dodge threshold
                    # Choose perpendicular movement to bullet path
                    dodge_direction = 1 if np.random.random() > 0.5 else -1
                    action = {"move": (dodge_direction, 0), "shoot": True}
                else:
                    # Normal ML-based movement
                    if "logistic" in preds:
                        chosen = preds["logistic"]["class"]
                    else:
                        chosen = next(iter(preds.values()))["class"]
                        
                    # Enhanced movement map with diagonal movements
                    move_map = {
                        0: None,
                        1: (-1, 0),   # Left
                        2: (1, 0),    # Right
                        3: (0, -1),   # Up
                        4: (0, 1),    # Down
                        5: (-1, -1),  # Up-Left
                        6: (1, -1),   # Up-Right
                        7: (-1, 1),   # Down-Left
                        8: (1, 1),    # Down-Right
                    }
                    
                    # Decide whether to shoot based on distance and angle
                    shoot = True
                    if "distance_to_player" in observation:
                        # Only shoot if within reasonable range
                        shoot = observation["distance_to_player"] < 300
                        
                    action = {"move": move_map.get(chosen, None), "shoot": shoot}
            else:
                # Fallback to basic movement if missing features
                action = {"move": None, "shoot": True}
                
            self._last_action = action
            self._last_decision_ts = now
            return action
        except Exception:
            # fallback
            return {"move": None, "shoot": False}
