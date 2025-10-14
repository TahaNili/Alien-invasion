"""
DifficultyManager
- Defines difficulty presets and a factory to create aliens with controllers & params
- API:
    - get_preset(level_name) -> params dict
    - create_alien(level_name, alien_factory_callable) -> alien instance with controller injected

This is a lightweight manager: actual spawn hook should call create_alien.
"""
from typing import Callable, Dict, Protocol

class AISettings(Protocol):
    alien_speed_factor: float

class AlienProtocol(Protocol):
    health: int
    ai_settings: AISettings
    controller: object
    rect: object
    x: float
    y: float

from src.controllers.base_controller import BaseController
from src.controllers.ml_controller import MLController
from src.controllers.behavior_controller import BehaviorController
from src.settings import DIFFICULTY_PRESETS


class DifficultyManager:

    _CONTROLLER_MAP = {
        "BaseController": BaseController,
        "MLController": MLController,
        "BehaviorController": BehaviorController
    }

    def __init__(self, preset_name: str = "Normal"):
        self.preset_name = preset_name
        self.preset = DIFFICULTY_PRESETS.get(preset_name, DIFFICULTY_PRESETS["Normal"])
        self.current_score_mult = self.preset.get("score_mult", 1.0)
        
    def set_preset(self, preset_name: str):
        self.preset_name = preset_name
        self.preset = DIFFICULTY_PRESETS.get(preset_name, DIFFICULTY_PRESETS["Normal"])
        self.current_score_mult = self.preset.get("score_mult", 1.0)
        # Update global current difficulty
        from src import settings
        settings.CURRENT_DIFFICULTY = preset_name

    def create_alien(self, alien_factory: Callable[[], AlienProtocol]) -> AlienProtocol:
        # alien_factory should be a callable that returns a new alien instance
        alien: AlienProtocol = alien_factory()
        
        # Get controller class from name
        controller_name = self.preset["controller"]
        controller_cls = self._CONTROLLER_MAP[controller_name]
        
        # Base params from preset
        params = {"decision_interval_ms": self.preset.get("decision_interval_ms", 150)}

        # Inject per-alien personality with a small random variation to diversify behaviors
        try:
            import random
            personality = {
                "aggression": float(self.preset.get("base_aggression", 1.0) * (0.85 + random.random() * 0.3)),
                "accuracy": float(self.preset.get("base_accuracy", 1.0) * (0.6 + random.random() * 0.8)),
                "reaction_jitter_ms": int(params["decision_interval_ms"] * (0.8 + random.random() * 0.4)),
                "dodge_tendency": float(self.preset.get("base_dodge", 1.0) * (0.5 + random.random() * 1.0)),
            }
            params["personality"] = personality
        except Exception:
            # If random import fails for any reason, proceed without personality
            pass

        setattr(alien, 'controller', controller_cls(alien, params))
        # also attach personality to the alien object so other systems can read it
        try:
            if isinstance(params.get("personality"), dict):
                setattr(alien, 'personality', params.get("personality"))
        except Exception:
            pass
        
        # apply hp/speed multipliers if alien exposes them
        if hasattr(alien, "health"):
            try:
                alien.health = int(alien.health * self.preset.get("hp_mult", 1.0))
            except Exception:
                pass
                
        if hasattr(alien, "ai_settings") and hasattr(alien.ai_settings, "alien_speed_factor"):
            try:
                alien.ai_settings.alien_speed_factor *= self.preset.get("speed_mult", 1.0)
            except Exception:
                pass
                
        return alien
