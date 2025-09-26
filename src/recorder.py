import csv
import atexit
import math
from pathlib import Path
from typing import Optional

import pygame


class Recorder:
    """Simple recorder to log gameplay frames and player actions to CSV and console.

    Usage:
        recorder = Recorder("data/gameplay_log.csv")
        recorder.record(stats, ship, aliens, bullets, health, input)
    """

    DEFAULT_FIELDS = [
        "timestamp_ms",
        "score",
        "ships_left",
        "health",
        "ship_x",
        "ship_y",
        "ship_angle",
        "moving_left",
        "moving_right",
        "moving_up",
        "moving_down",
        "mouse_x",
        "mouse_y",
        "mouse_fire",
        "bullets_count",
        "aliens_count",
        "nearest_alien_dx",
        "nearest_alien_dy",
        "nearest_alien_distance",
        # New fields: nearest alien velocity components (units/sec). These are
        # optional and will be None when no aliens present.
        "nearest_alien_vx",
        "nearest_alien_vy",
    ]

    def __init__(self, filepath: str | Path, fieldnames: Optional[list[str]] = None):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self.fieldnames = fieldnames or Recorder.DEFAULT_FIELDS

        # Open CSV file and write header if new
        self._f = open(self.filepath, "a", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._f, fieldnames=self.fieldnames)
        # If file is empty, write header
        try:
            if self._f.tell() == 0:
                self._writer.writeheader()
        except Exception:
            # On some streams tell() may fail; ignore
            pass

        # Ensure file is closed on exit
        atexit.register(self.close)

    def close(self):
        try:
            if not self._f.closed:
                self._f.flush()
                self._f.close()
        except Exception:
            pass

    def record(self, stats, ship, aliens, bullets, health, input):
        """Record a snapshot row built from provided game objects."""
        row = self._build_row(stats, ship, aliens, bullets, health, input)
        # Write to CSV
        try:
            self._writer.writerow(row)
            self._f.flush()
        except Exception:
            # Best-effort: ignore write errors
            pass

        # Also print to console (for variety / inspection)
        print(self._format_row_for_console(row))

    def _build_row(self, stats, ship, aliens, bullets, health, input):
        ts = pygame.time.get_ticks()

        ship_x = int(ship.center[0]) if hasattr(ship, "center") else int(getattr(ship.rect, "centerx", 0))
        ship_y = int(ship.center[1]) if hasattr(ship, "center") else int(getattr(ship.rect, "centery", 0))
        ship_angle = float(getattr(ship, "angle", 0.0))

        mouse_pos = input.get_mouse_cursor_position() if hasattr(input, "get_mouse_cursor_position") else pygame.mouse.get_pos()
        # mouse_fire for player, or AI-requested fire if set by AIManager
        mouse_fire = 0
        try:
            if hasattr(input, "is_mouse_button_pressed"):
                mouse_fire = int(bool(input.is_mouse_button_pressed(0)))
            else:
                mouse_fire = int(bool(pygame.mouse.get_pressed()[0]))
        except Exception:
            mouse_fire = 0

        # AI may request fire by setting ship._ai_requested_fire; prefer that
        # when present so AI shots are logged similarly to player shots.
        try:
            if getattr(ship, "_ai_requested_fire", False):
                mouse_fire = 1
                # clear the flag so it only records once
                try:
                    ship._ai_requested_fire = False
                except Exception:
                    pass
        except Exception:
            pass

        bullets_count = len(bullets.sprites()) if hasattr(bullets, "sprites") else int(len(bullets))
        aliens_count = len(aliens.sprites()) if hasattr(aliens, "sprites") else int(len(aliens))

        # nearest alien (dx, dy, distance)
        nearest_dx = None
        nearest_dy = None
        nearest_dist = None
        nearest_vx = None
        nearest_vy = None
        try:
            ship_cx = ship.center[0] if hasattr(ship, "center") else ship.rect.centerx
            ship_cy = ship.center[1] if hasattr(ship, "center") else ship.rect.centery

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
                    # record per-alien vx/vy when available
                    nearest_vx = getattr(a, "vx", None)
                    nearest_vy = getattr(a, "vy", None)
        except Exception:
            nearest_dx = nearest_dy = nearest_dist = None

        row = {
            "timestamp_ms": ts,
            "score": getattr(stats, "score", 0),
            "ships_left": getattr(stats, "ships_left", getattr(stats, "ships_left", 0)),
            "health": getattr(health, "current_hearts", getattr(health, "current_hearts", 0)),
            "ship_x": ship_x,
            "ship_y": ship_y,
            "ship_angle": ship_angle,
            "moving_left": bool(getattr(ship, "moving_left", False)),
            "moving_right": bool(getattr(ship, "moving_right", False)),
            "moving_up": bool(getattr(ship, "moving_up", False)),
            "moving_down": bool(getattr(ship, "moving_down", False)),
            "mouse_x": mouse_pos[0] if mouse_pos is not None else None,
            "mouse_y": mouse_pos[1] if mouse_pos is not None else None,
            "mouse_fire": int(mouse_fire),
            "bullets_count": bullets_count,
            "aliens_count": aliens_count,
            "nearest_alien_dx": nearest_dx,
            "nearest_alien_dy": nearest_dy,
            "nearest_alien_distance": nearest_dist,
            "nearest_alien_vx": nearest_vx,
            "nearest_alien_vy": nearest_vy,
        }

        # Ensure all fields present
        for k in self.fieldnames:
            if k not in row:
                row[k] = None

        return row

    def _format_row_for_console(self, row: dict) -> str:
        # Compact one-line representation
        parts = [f"t={row.get('timestamp_ms')}", f"score={row.get('score')}", f"hp={row.get('health')}",]
        parts.append(f"ship=({row.get('ship_x')},{row.get('ship_y')})")
        parts.append(f"angle={round(row.get('ship_angle',0),2)}")
        parts.append(f"fire={row.get('mouse_fire')}")
        parts.append(f"aliens={row.get('aliens_count')}")
        if row.get('nearest_alien_distance') is not None:
            parts.append(f"nearest_alien_dist={int(row.get('nearest_alien_distance'))}")
        return " | ".join(parts)
