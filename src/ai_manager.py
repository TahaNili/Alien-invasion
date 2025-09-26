import threading
import time
import subprocess
from pathlib import Path
from typing import Optional
import atexit
import sys

import joblib
import math

import src.game_functions as gf
from . import settings


class AIManager:
    """Runtime manager for the game's imitation-style AI.

    Responsibilities:
        - Load persisted ML models (joblib files) used to decide whether to fire.
        - Optionally run a background trainer subprocess to refresh models
          periodically.
        - Expose a high-level `act(...)` method which implements prioritized,
          human-like behavior (collect items, dodge bullets, approach/strafe
          enemies, and fire when appropriate).

    Implementation notes:
        - Movement is applied by toggling boolean flags on the `ship` object
          (ship.moving_left/right/up/down). The main loop should call
          `ai_manager.act(...)` before `ship.update()` so movement takes effect
          in the same frame.
        - The firing decision prefers a loaded ML model; if unavailable, a
          simple heuristic is used.
    """

    def __init__(self, models_dir: str = "models", trainer_cmd: Optional[list] = None, auto_train_interval: int = 120):
        self.models_dir = Path(models_dir)
        self.models = {}

        # default to same Python executable
        self.trainer_cmd = trainer_cmd or [sys.executable, str(Path("tools") / "train_imitation.py")]
        self.auto_train_interval = auto_train_interval
        self._stop_trainer = False

        self.ai_enabled = False
        self._auto_enabled = False

        # Load existing models if present
        self.load_models()

        # Start background trainer thread (only if trainer_cmd provided)
        self._trainer_thread = None
        if self.trainer_cmd:
            self._trainer_thread = threading.Thread(target=self._trainer_loop, daemon=True)
            self._trainer_thread.start()

        atexit.register(self.stop)

    def load_models(self):
        """Load models named logreg/rf/knn from the models directory if present."""
        for name in ("logreg", "rf", "knn"):
            path = self.models_dir / f"{name}.joblib"
            if path.exists():
                try:
                    self.models[name] = joblib.load(path)
                except Exception:
                    self.models[name] = None

    def _trainer_loop(self):
        """Background loop that periodically runs the training script and reloads models."""
        while not self._stop_trainer:
            try:
                subprocess.run(self.trainer_cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.load_models()
            except Exception:
                pass
            time.sleep(self.auto_train_interval)

    def stop(self):
        """Signal trainer thread to stop and join it."""
        self._stop_trainer = True
        try:
            if self._trainer_thread is not None and self._trainer_thread.is_alive():
                self._trainer_thread.join(timeout=1.0)
        except Exception:
            pass

    def set_enabled(self, value: bool, auto: bool = False):
        """Enable or disable the AI. If auto=True, mark as auto-enabled."""
        self.ai_enabled = bool(value)
        self._auto_enabled = bool(auto)

    def was_auto_enabled(self) -> bool:
        return bool(self._auto_enabled)

    def predict_fire(self, stats, ship, aliens, bullets, health, input):
        """Return True if AI (model) thinks the ship should fire this frame.

        Builds a feature vector compatible with the training script and calls the
        preferred loaded model. Falls back to conservative False on any error.
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
                0,  # mouse_x not used
                0,  # mouse_y
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

    def act(self, stats, ship, aliens, bullets, health, input, alien_bullets=None, items=None, cargoes=None, shields=None, hearts=None):
        """High-level behavior: collect -> dodge -> attack.

        Sets ship movement flags and fires via gf.fire_bullet when appropriate.
        """
        alien_sprites = aliens.sprites() if hasattr(aliens, "sprites") else list(aliens)
        alien_bullets_sprites = alien_bullets.sprites() if (alien_bullets is not None and hasattr(alien_bullets, "sprites")) else (list(alien_bullets) if alien_bullets is not None else [])

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

        def move_toward(tx, ty, thresh=8):
            dx = tx - ship_cx
            dy = ty - ship_cy
            ship.moving_left = dx < -thresh
            ship.moving_right = dx > thresh
            ship.moving_up = dy < -thresh
            ship.moving_down = dy > thresh

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
                    return
        except Exception:
            pass

        # 2) Dodge incoming bullets
        try:
            dodge_margin = 80
            for b in alien_bullets_sprites:
                bx = getattr(b.rect, 'centerx', getattr(b, 'x', None))
                by = getattr(b.rect, 'centery', getattr(b, 'y', None))
                if bx is None or by is None:
                    continue
                bvx = getattr(b, 'vx', getattr(b, 'dx', 0))
                bvy = getattr(b, 'vy', getattr(b, 'dy', 1))
                relx = bx - ship_cx
                rely = by - ship_cy
                if abs(relx) < dodge_margin and bvy > 0 and rely < 200 and rely > -50:
                    screen_w = 1200
                    try:
                        from src.settings import SCREEN_WIDTH
                        screen_w = SCREEN_WIDTH
                    except Exception:
                        pass
                    if ship_cx < screen_w / 2:
                        ship.moving_right = True
                        ship.moving_left = False
                    else:
                        ship.moving_left = True
                        ship.moving_right = False
                    ship.moving_up = True
                    ship.moving_down = False
                    return
        except Exception:
            pass

        # 3) Attack nearest alien
        if len(alien_sprites) == 0:
            ship.moving_left = ship.moving_right = ship.moving_up = ship.moving_down = False
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
                return

            aim_x, aim_y = target
            if min_dist > 200:
                move_toward(aim_x, aim_y, thresh=6)
            else:
                if aim_x < ship_cx:
                    ship.moving_left = True
                    ship.moving_right = False
                else:
                    ship.moving_right = True
                    ship.moving_left = False
                ship.moving_up = abs(aim_y - ship_cy) > 20 and (aim_y < ship_cy)
                ship.moving_down = abs(aim_y - ship_cy) > 20 and (aim_y > ship_cy)

            fired = False
            try:
                should_fire = self.predict_fire(stats, ship, aliens, bullets, health, input)
                if should_fire:
                    # Improve aiming: compute a lead angle toward the target so bullets
                    # are more likely to intercept moving aliens. We pick the nearest
                    # alien and predict its future position assuming it continues
                    # moving toward the ship at its configured speed.
                    try:
                        # choose nearest alien again (best-effort)
                        target = None
                        min_d = float('inf')
                        s_x = ship.rect.centerx
                        s_y = ship.rect.centery
                        for a in alien_sprites:
                            ax = getattr(a.rect, 'centerx', getattr(a, 'x', 0))
                            ay = getattr(a.rect, 'centery', getattr(a, 'y', 0))
                            d = math.hypot(ax - s_x, ay - s_y)
                            if d < min_d:
                                min_d = d
                                target = a

                        if target is not None:
                            # Relative vector from ship to alien
                            ax = getattr(target.rect, 'centerx', getattr(target, 'x', 0))
                            ay = getattr(target.rect, 'centery', getattr(target, 'y', 0))
                            rx = ax - s_x
                            ry = ay - s_y

                            # Estimate alien velocity: assume it moves toward the ship
                            # using its ai_settings.alien_speed_factor (units per second).
                            try:
                                a_speed = float(getattr(target.ai_settings, 'alien_speed_factor', 0.0))
                            except Exception:
                                a_speed = 0.0

                            # direction from alien to ship
                            try:
                                dir_x = (s_x - ax)
                                dir_y = (s_y - ay)
                                norm = math.hypot(dir_x, dir_y) or 1.0
                                vax = (dir_x / norm) * a_speed
                                vay = (dir_y / norm) * a_speed
                            except Exception:
                                vax = vay = 0.0

                            # bullet speed (units per second)
                            b_speed = float(getattr(settings, 'BULLET_SPEED_FACTOR', 0.0))

                            # Solve quadratic for intercept time: |r + v*t| = b_speed * t
                            # (v·v - b^2) t^2 + 2 r·v t + r·r = 0
                            rv = rx * vax + ry * vay
                            vv = vax * vax + vay * vay
                            rr = rx * rx + ry * ry
                            a_q = vv - b_speed * b_speed
                            b_q = 2 * rv
                            c_q = rr
                            t = None
                            if abs(a_q) < 1e-6:
                                if abs(b_q) > 1e-6:
                                    tt = -c_q / b_q
                                    if tt > 0:
                                        t = tt
                            else:
                                disc = b_q * b_q - 4 * a_q * c_q
                                if disc >= 0:
                                    sd = math.sqrt(disc)
                                    t1 = (-b_q + sd) / (2 * a_q)
                                    t2 = (-b_q - sd) / (2 * a_q)
                                    candidates = [x for x in (t1, t2) if x > 0]
                                    if candidates:
                                        t = min(candidates)

                            if t is not None:
                                aim_x = ax + vax * t
                                aim_y = ay + vay * t
                            else:
                                aim_x = ax
                                aim_y = ay

                            # compute firing angle compatible with ShipBullet.set_angle
                            fire_angle = math.atan2(-(aim_x - s_x), -(aim_y - s_y))
                            
                    except Exception:
                        pass

                    # Use the player's firing contract: set the ship's angle to the
                    # computed aim and fire normally. This ensures AI fires using
                    # the exact same logic as a human player (bullet direction
                    # comes from ship.angle), avoiding an alternate "cheating"
                    # path where bullets ignore the ship's facing.
                    try:
                        # Set ship.angle like the player would (this is the same
                        # value that would result if the player aimed with the
                        # mouse). Then call the standard fire path which uses
                        # ship.angle to determine bullet direction.
                        ship.angle = float(fire_angle)
                        gf.fire_bullet(ship, bullets)
                    except Exception:
                        # Fallback: try the override path if something fails.
                        try:
                            gf.fire_bullet(ship, bullets, angle=fire_angle)
                        except Exception:
                            gf.fire_bullet(ship, bullets)
                    fired = True
            except Exception:
                pass

            if not fired:
                try:
                    if abs(aim_x - ship_cx) < 16 or min_dist < 160:
                        gf.fire_bullet(ship, bullets)
                except Exception:
                    pass
        except Exception:
            try:
                ship.moving_left = ship.moving_right = ship.moving_up = ship.moving_down = False
            except Exception:
                pass
