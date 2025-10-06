"""Recorder for collecting per-frame game data and writing to CSV.

This module provides a lightweight Recorder class that writes a predefined set
of frame-level features into CSV files under `data/recordings/`. It avoids any
third-party dependencies and is robust to missing attributes (it will fill
missing fields with None).

Usage:
    from src.recorder import Recorder, collect_frame_features

    rec = Recorder()
    rec.start_session('test_run')
    features = collect_frame_features(...)
    rec.record_frame(frame_index, dt, features)
    rec.stop()

The recorder writes files like: data/recordings/sessionname_YYYYmmdd_HHMMSS.csv
"""

from __future__ import annotations

import csv
import json
# dataclasses removed: use a simple class to avoid import-time introspection issues
from datetime import datetime
import pygame
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


DEFAULT_RECORDING_DIR = Path(__file__).parent.parent / "data" / "recordings"


class Recorder:
    """Record per-frame feature dictionaries into a CSV file.

    The recorder expects callers to provide a dict of features per frame that
    match the `fieldnames` given at `start_session`. If `fieldnames` is None,
    a sensible default set is used.
    """

    def __init__(self, recordings_dir: Optional[Path] = None, fieldnames: Optional[Iterable[str]] = None) -> None:
        self.recordings_dir: Path = recordings_dir or DEFAULT_RECORDING_DIR
        # internal concrete list of fieldnames (set by start_session if not provided)
        self.fieldnames: Optional[list[str]] = list(fieldnames) if fieldnames is not None else None
        self._file: Optional[Any] = None
        self._writer: Optional[csv.DictWriter] = None
        self._path: Optional[Path] = None

    def start_session(self, session_name: Optional[str] = None, fieldnames: Optional[Iterable[str]] = None) -> Path:
        """Create recordings dir (if needed) and open a new CSV for writing.

        Returns the path to the created CSV file.
        """
        self.recordings_dir.mkdir(parents=True, exist_ok=True)

        if session_name is None:
            session_name = "session"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{session_name}_{timestamp}.csv"
        self._path = self.recordings_dir / filename

        # establish fieldnames (resolve to concrete list)
        if fieldnames is not None:
            self.fieldnames = list(fieldnames)
        elif self.fieldnames is None:
            # default columns (useful for simple ML models)
            self.fieldnames = [
                "frame",
                "timestamp",
                "dt",
                "ship_centerx",
                "ship_centery",
                "ship_angle",
                "moving_right",
                "moving_left",
                "moving_up",
                "moving_down",
                "bullets_count",
                "aliens_count",
                "cargoes_count",
                "alien_bullets_count",
                "hearts_count",
                "shields_count",
                "mouse_x",
                "mouse_y",
                "mouse_buttons",
                "score",
                "ships_left",
                "current_region_index",
                "region_name",
            ]

        # open file and write header (do this after fieldnames are resolved)
        self._file = open(self._path, "w", newline="", encoding="utf-8")
        # csv.DictWriter expects a concrete collection (supports __len__ and __contains__)
        fieldnames_resolved = list(self.fieldnames) if self.fieldnames is not None else []
        self._writer = csv.DictWriter(self._file, fieldnames=fieldnames_resolved, extrasaction="ignore")
        self._writer.writeheader()

        return self._path

    def record_frame(self, frame: int, dt: float, features: Dict[str, Any]) -> None:
        """Write a single frame's features to the CSV.

        - frame: integer frame index
        - dt: delta time since previous frame (ms or seconds as caller decides)
        - features: dictionary containing feature values keyed by column name
        """
        if self._writer is None:
            raise RuntimeError("Recorder session is not started. Call start_session().")

        # Validate input parameters
        if not isinstance(frame, (int, float)):
            raise ValueError("Frame must be a number")
        if not isinstance(dt, (int, float)):
            raise ValueError("dt must be a number")
        if not isinstance(features, dict):
            raise ValueError("features must be a dictionary")

        # ensure we have a concrete list of columns
        fieldnames_resolved = list(self.fieldnames) if self.fieldnames is not None else []
        row: dict = {key: None for key in fieldnames_resolved}
        row.update({
            "frame": int(frame),  # Ensure frame is integer
            "dt": float(dt),  # Ensure dt is float
            "timestamp": datetime.now().isoformat()
        })

        # convert non-primitive objects to JSON-friendly strings where reasonable
        for k, v in (features or {}).items():
            if k not in row:
                # ignore unexpected columns by default
                continue
            try:
                if v is None:
                    row[k] = None
                elif isinstance(v, bool):
                    row[k] = bool(v)  # Ensure boolean type
                elif isinstance(v, (int, float)):
                    row[k] = v if not isinstance(v, bool) else int(v)  # Handle numeric types
                elif isinstance(v, str):
                    row[k] = v
                elif isinstance(v, (list, tuple, dict)):
                    row[k] = json.dumps(v, ensure_ascii=False)
                else:
                    # try to extract primitive attributes, otherwise stringify
                    row[k] = str(v)
            except Exception as e:
                row[k] = str(v)

        self._writer.writerow(row)

    def stop(self) -> Optional[Path]:
        """Close the current recording file and return its path."""
        if self._file:
            try:
                self._file.flush()  # Ensure all data is written to disk
                self._file.close()
                # Inform the user where the recording was saved
                try:
                    print(f"Recording saved to: {self._path}")
                except Exception:
                    pass
                return self._path
            except Exception as e:
                print(f"Error closing recording file: {e}")
                return None
            finally:
                self._file = None
                self._writer = None
        return None  # Return None if no file was open


def _safe_len(maybe_group) -> int:
    """Safely get the length of various types of collections."""
    if maybe_group is None:
        return 0
    try:
        # Try direct len() first
        return len(maybe_group)
    except Exception:
        try:
            # For iterator-like objects, convert to list first
            return len(list(maybe_group))
        except Exception:
            try:
                # For pygame sprite groups, try sprites attribute
                return len(getattr(maybe_group, "sprites", lambda: [])())
            except Exception:
                return 0


def collect_frame_features(
    ship=None,
    input_obj=None,
    stats=None,
    bullets=None,
    aliens=None,
    cargoes=None,
    alien_bullets=None,
    hearts=None,
    shields=None,
    region_manager=None,
) -> Dict[str, Any]:
    """Collect a dict of default features from the provided game objects.

    Each argument is optional; the function will return None for missing
    features. The shape matches the default Recorder.fieldnames.
    """
    f: Dict[str, Any] = {}

    # ship
    try:
        center = getattr(ship, "center", None)
        if center and isinstance(center, (list, tuple)) and len(center) >= 2:
            f["ship_centerx"] = float(center[0])
            f["ship_centery"] = float(center[1])
        else:
            # fallback to rect if available
            rect = getattr(ship, "rect", None)
            if rect is not None:
                f["ship_centerx"] = float(getattr(rect, "centerx", None) or getattr(rect, "x", None) or 0)
                f["ship_centery"] = float(getattr(rect, "centery", None) or getattr(rect, "y", None) or 0)
        # safe conversion of angle to float
        if hasattr(ship, "angle") and getattr(ship, "angle", None) is not None:
            try:
                f["ship_angle"] = float(getattr(ship, "angle"))
            except Exception:
                f["ship_angle"] = None
        else:
            f["ship_angle"] = None
        # Get movement states from input_obj. Prefer using input_obj's query
        # methods (is_key_down) when available; fall back to attribute names
        # for older Input implementations.
        try:
            if input_obj is not None:
                # First try using the modern is_key_down method
                if hasattr(input_obj, "is_key_down"):
                    f["moving_right"] = bool(
                        input_obj.is_key_down(pygame.K_RIGHT) or input_obj.is_key_down(pygame.K_d)
                    )
                    f["moving_left"] = bool(
                        input_obj.is_key_down(pygame.K_LEFT) or input_obj.is_key_down(pygame.K_a)
                    )
                    f["moving_up"] = bool(
                        input_obj.is_key_down(pygame.K_UP) or input_obj.is_key_down(pygame.K_w)
                    )
                    f["moving_down"] = bool(
                        input_obj.is_key_down(pygame.K_DOWN) or input_obj.is_key_down(pygame.K_s)
                    )
                # Fallback to checking key states directly (common pattern: key_states mapping)
                elif hasattr(input_obj, "key_states"):
                    key_states = getattr(input_obj, "key_states", {})
                    f["moving_right"] = bool(key_states.get(pygame.K_RIGHT, False) or key_states.get(pygame.K_d, False))
                    f["moving_left"] = bool(key_states.get(pygame.K_LEFT, False) or key_states.get(pygame.K_a, False))
                    f["moving_up"] = bool(key_states.get(pygame.K_UP, False) or key_states.get(pygame.K_w, False))
                    f["moving_down"] = bool(key_states.get(pygame.K_DOWN, False) or key_states.get(pygame.K_s, False))
                # Last resort: check legacy pressed attributes
                else:
                    f["moving_right"] = bool(getattr(input_obj, "right_pressed", False))
                    f["moving_left"] = bool(getattr(input_obj, "left_pressed", False))
                    f["moving_up"] = bool(getattr(input_obj, "up_pressed", False))
                    f["moving_down"] = bool(getattr(input_obj, "down_pressed", False))
            else:
                # No input facade provided: fallback to pygame global state so recorder still captures player input
                try:
                    keys = pygame.key.get_pressed()
                    f["moving_right"] = bool(keys[pygame.K_RIGHT] or keys[pygame.K_d])
                    f["moving_left"] = bool(keys[pygame.K_LEFT] or keys[pygame.K_a])
                    f["moving_up"] = bool(keys[pygame.K_UP] or keys[pygame.K_w])
                    f["moving_down"] = bool(keys[pygame.K_DOWN] or keys[pygame.K_s])
                except Exception:
                    f["moving_right"] = False
                    f["moving_left"] = False
                    f["moving_up"] = False
                    f["moving_down"] = False
        except Exception:
            f["moving_right"] = False
            f["moving_left"] = False
            f["moving_up"] = False
            f["moving_down"] = False
    except Exception:
        pass

    # input / mouse
    try:
        if input_obj is not None:
            # Try modern method first
            if hasattr(input_obj, "get_mouse_cursor_position"):
                mx, my = input_obj.get_mouse_cursor_position()
            # Fallback to direct pygame mouse position
            else:
                mx, my = pygame.mouse.get_pos()
            f["mouse_x"] = int(mx)
            f["mouse_y"] = int(my)

            # Get mouse button states
            if hasattr(input_obj, "current_mouse_button_states"):
                f["mouse_buttons"] = list(getattr(input_obj, "current_mouse_button_states", []))
            elif hasattr(input_obj, "get_mouse_button_state"):
                f["mouse_buttons"] = [input_obj.get_mouse_button_state(i) for i in range(3)]
            else:
                f["mouse_buttons"] = list(pygame.mouse.get_pressed())
    except Exception as e:
        f["mouse_x"] = 0
        f["mouse_y"] = 0
        f["mouse_buttons"] = []

    # counts of groups
    f["bullets_count"] = _safe_len(bullets)
    f["aliens_count"] = _safe_len(aliens)
    f["cargoes_count"] = _safe_len(cargoes)
    f["alien_bullets_count"] = _safe_len(alien_bullets)
    f["hearts_count"] = _safe_len(hearts)
    f["shields_count"] = _safe_len(shields)

    # stats
    if stats is not None:
        f["score"] = int(getattr(stats, "score", 0))
        f["ships_left"] = int(getattr(stats, "ships_left", 0))

    # region
    try:
        if region_manager is not None:
            f["current_region_index"] = int(getattr(region_manager, "current_region_index", -1))
            try:
                region = region_manager.get_current_region()
                f["region_name"] = getattr(region, "region_name", None)
            except Exception:
                f["region_name"] = None
    except Exception:
        pass

    return f


__all__ = ["Recorder", "collect_frame_features"]
