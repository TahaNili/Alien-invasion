"""
Shared protocols and type definitions for the game.
"""
from typing import Protocol, Any, Dict

class AISettings(Protocol):
    """Protocol defining the required attributes for AI settings."""
    alien_speed_factor: float
    screen_width: int
    screen_height: int
    alien_l2_spawn_chance: int
    alien_l2_health: int
    alien_l1_health: int
    delta_time: float

class AlienProtocol(Protocol):
    """Protocol defining the required attributes and methods for aliens."""
    health: int
    ai_settings: AISettings
    controller: Any
    rect: Any
    x: float
    y: float

    def update(self, ship: Any) -> None:
        """Update alien's position."""
        ...

class ControllerProtocol(Protocol):
    """Protocol defining the required methods for alien controllers."""
    def decide(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """Make a decision based on current observation."""
        ...

    def observe(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """Observe the current game state."""
        ...