"""A small, deterministic AI controller that emulates player input.

This implementation is intentionally simple and robust:
- No ML dependencies, no background trainer thread.
- Emulates mouse position and mouse button press for firing.
- Emulates arrow/WASD key states for movement.
- Sets `ship._ai_requested_fire = True` when it wants to fire (recorder compatibility).

The AI has two modes:
- passive: do nothing
- combat: target nearest alien and move/aim/fire using simple heuristics

This file is non-destructive: it doesn't remove the old `src/ai_manager.py`.
Use by importing `AIManager` from this module, or aliasing in `alien_invasion.py`.
"""
from __future__ import annotations

import math
from typing import Optional
import pygame


class AIManager:
    """Deterministic AI manager used for testing and as a robust default.

    Methods
    - set_enabled(bool): enable/disable AI
    - was_auto_enabled() -> bool
    - act(stats, ship, aliens, bullets, health, input, ...)
    """

    def __init__(self):
        self.ai_enabled = False
        self._auto_enabled = False
        self.debug = False

    def set_enabled(self, value: bool, auto: bool = False):
        self.ai_enabled = bool(value)
        self._auto_enabled = bool(auto)

    def was_auto_enabled(self) -> bool:
        return bool(self._auto_enabled)

    def _find_nearest_alien(self, ship, aliens):
        nearest = None
        min_d = float("inf")
        sx = ship.rect.centerx
        sy = ship.rect.centery
        for a in aliens.sprites() if hasattr(aliens, 'sprites') else list(aliens):
            ax = getattr(a.rect, 'centerx', getattr(a, 'x', None))
            ay = getattr(a.rect, 'centery', getattr(a, 'y', None))
            if ax is None or ay is None:
                continue
            d = math.hypot(ax - sx, ay - sy)
            if d < min_d:
                min_d = d
                nearest = (a, ax, ay, d)
        return nearest

    def act(self, stats, ship, aliens, bullets, health, input, alien_bullets=None, items=None, cargoes=None, shields=None, hearts=None):
        """Simple act loop:
        - If no aliens: do nothing (clear movement)
        - Otherwise: aim at nearest alien, move horizontally toward it, and fire when roughly aimed.
        """
        # Defensive: do nothing if AI disabled
        if not self.ai_enabled:
            return

        # Prepare key/mouse buffers sized to input.current_key_states if possible
        try:
            key_len = len(input.current_key_states)
        except Exception:
            key_len = 512
        prev_key_buf = [False] * key_len
        cur_key_buf = [False] * key_len

        # mouse buffers (left, middle, right)
        try:
            prev_mouse_buf = list(input.current_mouse_button_states)
            if len(prev_mouse_buf) < 3:
                prev_mouse_buf = [False, False, False]
        except Exception:
            prev_mouse_buf = [False, False, False]
        cur_mouse_buf = [False, False, False]

        def set_key_state(key_code, value):
            try:
                if 0 <= key_code < len(cur_key_buf):
                    cur_key_buf[key_code] = bool(value)
            except Exception:
                pass

        def set_mouse_press(left=False, middle=False, right=False):
            try:
                cur_mouse_buf[0] = bool(left)
                cur_mouse_buf[1] = bool(middle)
                cur_mouse_buf[2] = bool(right)
            except Exception:
                pass

        def commit_input_states():
            try:
                if hasattr(input, 'previous_key_states'):
                    input.previous_key_states = tuple(prev_key_buf)
                if hasattr(input, 'current_key_states'):
                    input.current_key_states = tuple(cur_key_buf)
                if hasattr(input, 'previous_mouse_button_states'):
                    input.previous_mouse_button_states = tuple(prev_mouse_buf)
                if hasattr(input, 'current_mouse_button_states'):
                    input.current_mouse_button_states = tuple(cur_mouse_buf)
            except Exception:
                pass

        # default: stop movement
        set_key_state(pygame.K_LEFT, False)
        set_key_state(pygame.K_RIGHT, False)
        set_key_state(pygame.K_UP, False)
        set_key_state(pygame.K_DOWN, False)

        nearest = self._find_nearest_alien(ship, aliens)
        if nearest is None:
            # apply commit (clear inputs)
            commit_input_states()
            return

        a_sprite, ax, ay, dist = nearest

        # Move horizontally toward the alien when far
        sx = ship.rect.centerx
        sy = ship.rect.centery

        # Simple horizontal steering
        if ax < sx - 8:
            set_key_state(pygame.K_LEFT, True)
            set_key_state(pygame.K_RIGHT, False)
        elif ax > sx + 8:
            set_key_state(pygame.K_RIGHT, True)
            set_key_state(pygame.K_LEFT, False)
        else:
            set_key_state(pygame.K_LEFT, False)
            set_key_state(pygame.K_RIGHT, False)

        # Vertical adjustments (small)
        set_key_state(pygame.K_UP, ay < sy - 16)
        set_key_state(pygame.K_DOWN, ay > sy + 16)

        # Aim: set mouse cursor to target so ship.update computes angle
        try:
            if hasattr(input, 'current_mouse_position'):
                input.current_mouse_position = (int(ax), int(ay))
        except Exception:
            pass

        # Fire heuristic: if roughly aligned horizontally (small angle) and not too many bullets
        try:
            # compute angle between ship nose and target
            dx = ax - sx
            dy = ay - sy
            aim_angle = math.atan2(-dx, -dy)
            ship_angle = getattr(ship, 'angle', 0.0)
            angle_diff = abs((aim_angle - ship_angle + math.pi) % (2 * math.pi) - math.pi)
            bullets_count = len(bullets.sprites()) if hasattr(bullets, 'sprites') else len(bullets)
            if angle_diff < 0.35 and bullets_count < getattr(__import__('src.settings', fromlist=['']).settings, 'BULLETS_ALLOWED', 5):
                # request a single-frame left mouse press
                set_mouse_press(left=True)
                # recorder compatibility
                try:
                    ship._ai_requested_fire = True
                except Exception:
                    pass
        except Exception:
            pass

        # commit to input
        commit_input_states()
