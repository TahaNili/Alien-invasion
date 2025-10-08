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


class DifficultyManager:
    PRESETS = {
        "Easy": {"controller": BaseController, "hp_mult": 1.0, "speed_mult": 1.0, "decision_interval_ms": 500, "spawn_multiplier": 1.0},
        "Normal": {"controller": MLController, "hp_mult": 2.0, "speed_mult": 1.2, "decision_interval_ms": 200, "spawn_multiplier": 1.0},
        "Hard": {"controller": BehaviorController, "hp_mult": 3.0, "speed_mult": 1.4, "decision_interval_ms": 120, "spawn_multiplier": 1.0},
        "VeryHard": {"controller": BehaviorController, "hp_mult": 4.0, "speed_mult": 1.6, "decision_interval_ms": 100, "spawn_multiplier": 1.5},
        "Unbeatable": {"controller": BehaviorController, "hp_mult": 6.0, "speed_mult": 2.0, "decision_interval_ms": 60, "spawn_multiplier": 3.0},
    }

    def __init__(self, preset_name: str = "Normal"):
        self.preset_name = preset_name
        self.preset = self.PRESETS.get(preset_name, self.PRESETS["Normal"])
    def set_preset(self, preset_name: str):
        self.preset_name = preset_name
        self.preset = self.PRESETS.get(preset_name, self.PRESETS["Normal"])

    def create_alien(self, alien_factory: Callable[[], AlienProtocol]) -> AlienProtocol:
        # alien_factory should be a callable that returns a new alien instance
        alien: AlienProtocol = alien_factory()
        controller_cls = self.preset["controller"]
        params = {"decision_interval_ms": self.preset.get("decision_interval_ms", 150)}
        setattr(alien, 'controller', controller_cls(alien, params))
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
