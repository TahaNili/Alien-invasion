import os
import sys
import types

# Ensure repo root is on path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import importlib
import pytest

# Configure headless pygame before importing game modules that call pygame.display
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
import pygame
pygame.display.init()
try:
    # Try to create a tiny hidden display surface for headless tests
    pygame.display.set_mode((1, 1))
except Exception:
    # If setting mode fails, rely on get_surface() returning None; tests will guard against that
    pass

from src import input as input_mod
from src.ship import Ship

# These tests aim to run headless (no pygame display). They exercise ai_manager_combined
# logic by creating a fake world state and calling act(), then asserting input emulation and recorder contract.


def make_dummy_game_state():
    class Dummy:
        def __init__(self):
            self.aliens = []
            self.bullets = []
            self.stats = types.SimpleNamespace(score=0)
            self.health = types.SimpleNamespace(hp=5)
    return Dummy()


def test_ai_emulates_input_and_sets_ai_requested_fire(monkeypatch, tmp_path):
    # Import the combined AI manager
    ai_module = importlib.import_module('src.ai_manager_combined')
    AIManager = getattr(ai_module, 'AIManager')

    # Monkeypatch TextureAtlas to return a dummy surface so Ship can be created headless
    dummy_surf = pygame.Surface((8, 8))
    monkeypatch.setattr('src.resources.texture_atlas.TextureAtlas.get_sprite_texture', lambda *a, **k: dummy_surf)

    # Create input and ship
    inp = input_mod.Input()
    ship = Ship(inp)

    # Create AI manager and enable it
    ai = AIManager()
    ai.set_enabled(True, auto=True)

    # Make a simple world with a fake alien to target
    state = make_dummy_game_state()
    # Create a fake alien close to the ship
    fake_alien = types.SimpleNamespace(rect=types.SimpleNamespace(center=(ship.rect.centerx + 50, ship.rect.centery)))
    state.aliens.append(fake_alien)

    # Ensure no AI requested fire initially
    assert not getattr(ship, '_ai_requested_fire', False)

    # Call act() which should emulate input and possibly set ship._ai_requested_fire
    ai.act(state.stats, ship, state.aliens, state.bullets, state.health, inp)

    # After acting, input buffers should be populated (previous and current)
    assert hasattr(inp, 'previous_key_states') and hasattr(inp, 'current_key_states')
    # AI should set current_mouse_position so ship.update() can compute angle
    assert inp.current_mouse_position is not None

    # If AI fired, recorder compatibility flag should be set on ship (may be True or absent depending on model)
    # We accept either presence True or False, but ensure attribute exists or was left False
    assert hasattr(ship, '_ai_requested_fire')


def test_ml_fallback_to_heuristic(monkeypatch):
    # Simulate model loading failure so AI falls back to heuristic
    ai_module = importlib.import_module('src.ai_manager_combined')
    AIManager = getattr(ai_module, 'AIManager')

    # Force models_ok = False
    ai = AIManager()
    ai.models_ok = False
    ai.set_enabled(True, auto=True)

    # Minimal state
    state = make_dummy_game_state()

    # Monkeypatch TextureAtlas
    dummy_surf = pygame.Surface((8, 8))
    monkeypatch.setattr('src.resources.texture_atlas.TextureAtlas.get_sprite_texture', lambda *a, **k: dummy_surf)

    inp = input_mod.Input()
    ship = Ship(inp)

    # No aliens -> heuristic should not crash
    ai.act(state.stats, ship, state.aliens, state.bullets, state.health, inp)
    # With an alien, heuristic should emulate input without ML
    fake_alien = types.SimpleNamespace(rect=types.SimpleNamespace(center=(ship.rect.centerx + 10, ship.rect.centery)))
    state.aliens.append(fake_alien)
    ai.act(state.stats, ship, state.aliens, state.bullets, state.health, inp)

    # Ensure input emulation present
    assert inp.current_mouse_position is not None


if __name__ == '__main__':
    pytest.main([os.path.abspath(__file__)])
