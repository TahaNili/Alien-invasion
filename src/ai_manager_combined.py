"""Combined AI manager: ML-backed firing decision + heuristic movement fallback.

This module merges the ML-style AI (from `ai_manager.py`) and the
deterministic heuristic AI (from `ai_manager_new.py`) into a single
AIManager that:
 - Loads ML models (logreg/rf/knn) if present and uses them to decide
   whether to fire.
 - Always uses a robust heuristic for movement/aiming (emulates player
   input exactly like the deterministic AI) so behavior is consistent
   and recorder-compatible.
 - Falls back to the heuristic firing behavior if no models are found or
   if model prediction errors occur.

The AI emulates input by writing into the provided `input` object:
`previous_key_states`, `current_key_states`, `previous_mouse_button_states`,
`current_mouse_button_states`, and `current_mouse_position`. It also sets
`ship._ai_requested_fire = True` when it requests a shot so the recorder
sees AI shots like a human player.
"""
from __future__ import annotations

import threading
import time
import subprocess
from pathlib import Path
from typing import Optional
import atexit
import sys
import math

import joblib
import pygame

from . import settings


class AIManager:
    """Unified AI manager.

    API matches previous AIManagers: set_enabled, was_auto_enabled, act, stop.
    """

    def __init__(self, models_dir: str = "models", trainer_cmd: Optional[list] = None, auto_train_interval: int = 120):
        # ML-related
        self.models_dir = Path(models_dir)
        self.models: dict = {}
        self.models_ok = True
        self._model_error_count = 0
        self._model_error_threshold = 8

        # Trainer (optional)
        self.trainer_cmd = trainer_cmd or []
        self.auto_train_interval = auto_train_interval
        self._stop_trainer = False
        self._trainer_thread = None

        # Enabled state
        self.ai_enabled = False
        self._auto_enabled = False

        # load any models present
        self.load_models()

        # start trainer thread only if a trainer command was provided
        if self.trainer_cmd:
            try:
                self._trainer_thread = threading.Thread(target=self._trainer_loop, daemon=True)
                self._trainer_thread.start()
            except Exception:
                self._trainer_thread = None

        atexit.register(self.stop)

    # --------------------- model loading / trainer ---------------------
    def load_models(self):
        for name in ("logreg", "rf", "knn"):
            path = self.models_dir / f"{name}.joblib"
            if path.exists():
                try:
                    self.models[name] = joblib.load(path)
                except Exception:
                    self.models[name] = None
            else:
                self.models[name] = None

    def _trainer_loop(self):
        while not self._stop_trainer:
            try:
                subprocess.run(self.trainer_cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.load_models()
            except Exception:
                pass
            time.sleep(self.auto_train_interval)

    def stop(self):
        self._stop_trainer = True
        try:
            if self._trainer_thread is not None and self._trainer_thread.is_alive():
                self._trainer_thread.join(timeout=1.0)
        except Exception:
            pass

    def set_enabled(self, value: bool, auto: bool = False):
        self.ai_enabled = bool(value)
        self._auto_enabled = bool(auto)

    def was_auto_enabled(self) -> bool:
        return bool(self._auto_enabled)

    # --------------------- ML prediction for firing ---------------------
    def predict_fire(self, stats, ship, aliens, bullets, health, input):
        """Return True if ML model(s) recommend firing this frame.

        Falls back to False on any error.
        """
        try:
            ship_x = int(ship.center[0]) if hasattr(ship, "center") else int(getattr(ship.rect, "centerx", 0))
            ship_y = int(ship.center[1]) if hasattr(ship, "center") else int(getattr(ship.rect, "centery", 0))
            ship_angle = float(getattr(ship, "angle", 0.0))

            bullets_count = len(bullets.sprites()) if hasattr(bullets, "sprites") else int(len(bullets))
            aliens_count = len(aliens.sprites()) if hasattr(aliens, "sprites") else int(len(aliens))

            ship_cx = ship.center[0] if hasattr(ship, "center") else ship.rect.centerx
            ship_cy = ship.center[1] if hasattr(ship, "center") else ship.rect.centery

            nearest_dx = 0
            nearest_dy = 0
            nearest_dist = 0
            min_dist = float("inf")
            for a in aliens.sprites():
                ax = getattr(a.rect, "centerx", getattr(a, "x", 0))
                ay = getattr(a.rect, "centery", getattr(a, "y", 0))
                dx = ax - ship_cx
                dy = ay - ship_cy
                dist = math.hypot(dx, dy)
                if dist < min_dist:
                    min_dist = dist
                    nearest_dx = dx
                    nearest_dy = dy
                    nearest_dist = dist

            feat = [
                getattr(stats, "score", 0),
                getattr(stats, "ships_left", 0),
                getattr(health, "current_hearts", 0),
                ship_x,
                ship_y,
                ship_angle,
                bool(getattr(ship, "moving_left", False)),
                bool(getattr(ship, "moving_right", False)),
                bool(getattr(ship, "moving_up", False)),
                bool(getattr(ship, "moving_down", False)),
                0,
                0,
                bullets_count,
                aliens_count,
                nearest_dx,
                nearest_dy,
                nearest_dist,
            ]

            model = None
            for name in ("logreg", "rf", "knn"):
                model = self.models.get(name)
                if model is not None:
                    break

            if model is None:
                return False

            import numpy as np

            X = np.array(feat, dtype=float).reshape(1, -1)
            try:
                p = model.predict(X)
                return bool(int(p[0]))
            except Exception:
                try:
                    prob = model.predict_proba(X)[0][1]
                    return prob > 0.5
                except Exception:
                    return False
        except Exception:
            return False

    # --------------------- combined act (heuristic movement + ML firing) ---------------------
    def act(self, stats, ship, aliens, bullets, health, input, alien_bullets=None, items=None, cargoes=None, shields=None, hearts=None):
        """Perform a single AI decision step.

        Movement/aiming is handled by a robust heuristic similar to the
        deterministic AI. Firing decision first tries ML models and
        falls back to the heuristic rule on error or missing models.
        """
        # Defensive: do nothing if AI disabled
        if not self.ai_enabled:
            return

        # Prepare key/mouse buffers sized to input.current_key_states if possible
        try:
            key_len = len(input.current_key_states)
            # ensure a reasonable minimum so key indices used by pygame are valid
            if key_len < 64:
                key_len = 64
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

        def move_toward(tx, ty, thresh=8):
            dx = tx - ship_cx
            dy = ty - ship_cy
            ship.moving_left = dx < -thresh
            ship.moving_right = dx > thresh
            ship.moving_up = dy < -thresh
            ship.moving_down = dy > thresh

        # collect lists
        alien_sprites = aliens.sprites() if hasattr(aliens, "sprites") else list(aliens)

        items_sprites = []
        for g in (hearts, shields, cargoes, items):
            if g is None:
                continue
            if hasattr(g, "sprites"):
                items_sprites.extend(g.sprites())
            else:
                items_sprites.extend(list(g))

        ship_cx = ship.center[0] if hasattr(ship, "center") else ship.rect.centerx
        ship_cy = ship.center[1] if hasattr(ship, "center") else ship.rect.centery

        # default: clear movement
        set_key_state(pygame.K_LEFT, False)
        set_key_state(pygame.K_RIGHT, False)
        set_key_state(pygame.K_UP, False)
        set_key_state(pygame.K_DOWN, False)

        # 1) Collect nearby items
        try:
            if len(items_sprites) > 0:
                best = None
                best_d = float('inf')
                for it in items_sprites:
                    ix = getattr(it.rect, 'centerx', getattr(it, 'x', None))
                    iy = getattr(it.rect, 'centery', getattr(it, 'y', None))
                    if ix is None or iy is None:
                        continue
                    d = math.hypot(ix - ship_cx, iy - ship_cy)
                    if d < best_d:
                        best_d = d
                        best = (ix, iy)
                if best is not None and best_d < 240:
                    move_toward(best[0], best[1], thresh=6)
                    commit_input_states()
                    return
        except Exception:
            pass

        # 2) Dodge incoming bullets
        try:
            dodge_margin = 80
            for b in (alien_bullets.sprites() if (alien_bullets is not None and hasattr(alien_bullets, 'sprites')) else (list(alien_bullets) if alien_bullets is not None else [])):
                bx = getattr(b.rect, 'centerx', getattr(b, 'x', None))
                by = getattr(b.rect, 'centery', getattr(b, 'y', None))
                if bx is None or by is None:
                    continue
                bvx = getattr(b, 'vx', getattr(b, 'dx', 0))
                bvy = getattr(b, 'vy', getattr(b, 'dy', 1))
                relx = bx - ship_cx
                rely = by - ship_cy
                if abs(relx) < dodge_margin and bvy > 0 and rely < 200 and rely > -50:
                    try:
                        screen_w = settings.SCREEN_WIDTH
                    except Exception:
                        # fallback when settings not available
                        screen_w = 1200
                    if ship_cx < screen_w / 2:
                        set_key_state(pygame.K_RIGHT, True)
                        set_key_state(pygame.K_LEFT, False)
                    else:
                        set_key_state(pygame.K_LEFT, True)
                        set_key_state(pygame.K_RIGHT, False)
                    set_key_state(pygame.K_UP, True)
                    set_key_state(pygame.K_DOWN, False)
                    commit_input_states()
                    return
        except Exception:
            pass

        # 3) Attack nearest alien (heuristic movement/aiming)
        if len(alien_sprites) == 0:
            commit_input_states()
            return

        try:
            min_dist = float('inf')
            target = None
            for a in alien_sprites:
                ax = getattr(a.rect, 'centerx', getattr(a, 'x', 0))
                ay = getattr(a.rect, 'centery', getattr(a, 'y', 0))
                d = math.hypot(ax - ship_cx, ay - ship_cy)
                if d < min_dist:
                    min_dist = d
                    target = (ax, ay)

            if target is None:
                commit_input_states()
                return

            aim_x, aim_y = target
            if min_dist > 200:
                move_toward(aim_x, aim_y, thresh=6)
            else:
                if aim_x < ship_cx:
                    set_key_state(pygame.K_LEFT, True)
                    set_key_state(pygame.K_RIGHT, False)
                else:
                    set_key_state(pygame.K_RIGHT, True)
                    set_key_state(pygame.K_LEFT, False)
                set_key_state(pygame.K_UP, abs(aim_y - ship_cy) > 20 and (aim_y < ship_cy))
                set_key_state(pygame.K_DOWN, abs(aim_y - ship_cy) > 20 and (aim_y > ship_cy))

            # default: no fired yet
            fired = False

            # Aim: set mouse cursor to target so ship.update computes angle
            try:
                if hasattr(input, 'current_mouse_position'):
                    input.current_mouse_position = (int(aim_x), int(aim_y))
            except Exception:
                pass

            # Decide whether to fire using ML if available, otherwise use heuristic
            use_ml = any(self.models.get(n) is not None for n in ("logreg", "rf", "knn")) and self.models_ok
            should_fire_ml = False
            if use_ml:
                try:
                    should_fire_ml = self.predict_fire(stats, ship, aliens, bullets, health, input)
                    # reset error count on success
                    self._model_error_count = 0
                except Exception:
                    self._model_error_count += 1
                    if self._model_error_count >= self._model_error_threshold:
                        self.models_ok = False
                    should_fire_ml = False

            if use_ml and should_fire_ml:
                try:
                    ship._ai_requested_fire = True
                except Exception:
                    pass
                # simulate one-frame left-mouse press
                set_mouse_press(left=True)
                # set ship angle best-effort (other code may update it)
                try:
                    ship.angle = float(math.atan2(-(aim_x - ship_cx), -(aim_y - ship_cy)))
                except Exception:
                    pass
                fired = True
            else:
                # Heuristic firing (same logic as ai_manager_new)
                try:
                    dx = aim_x - ship_cx
                    dy = aim_y - ship_cy
                    aim_angle = math.atan2(-dx, -dy)
                    ship_angle = getattr(ship, 'angle', 0.0)
                    angle_diff = abs((aim_angle - ship_angle + math.pi) % (2 * math.pi) - math.pi)
                    try:
                        bullets_count = len(bullets.sprites()) if hasattr(bullets, 'sprites') else int(len(bullets))
                    except Exception:
                        bullets_count = 0
                    try:
                        max_bul = getattr(settings, 'BULLETS_ALLOWED', 5)
                    except Exception:
                        max_bul = 5
                    if angle_diff < 0.35 and bullets_count < max_bul:
                        set_mouse_press(left=True)
                        try:
                            ship._ai_requested_fire = True
                        except Exception:
                            pass
                        fired = True
                except Exception:
                    pass

        except Exception:
            try:
                ship.moving_left = ship.moving_right = ship.moving_up = ship.moving_down = False
            except Exception:
                pass

        # commit simulated input (ensure mouse position committed too)
        try:
            # ensure current_mouse_position present
            if hasattr(input, 'current_mouse_position'):
                # if ship.angle was set directly, keep input.mouse consistent
                try:
                    # leave as-is; already set earlier when aiming
                    _ = input.current_mouse_position
                except Exception:
                    input.current_mouse_position = (int(ship_cx), int(ship_cy))
            commit_input_states()
        except Exception:
            pass
