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

        # ensure we have a concrete list of columns
        fieldnames_resolved = list(self.fieldnames) if self.fieldnames is not None else []
        row: dict = {key: None for key in fieldnames_resolved}
        row.update({"frame": frame, "dt": dt, "timestamp": datetime.now().isoformat()})

        # convert non-primitive objects to JSON-friendly strings where reasonable
        for k, v in (features or {}).items():
            if k not in row:
                # ignore unexpected columns by default
                continue
            try:
                if v is None or isinstance(v, (int, float, str, bool)):
                    row[k] = v
                elif isinstance(v, (list, tuple, dict)):
                    row[k] = json.dumps(v, ensure_ascii=False)
                else:
                    # try to extract primitive attributes, otherwise stringify
                    row[k] = str(v)
            except Exception:
                row[k] = str(v)

        self._writer.writerow(row)

    def stop(self) -> Optional[Path]:
        """Close the current recording file and return its path."""
        if self._file:
            try:
                self._file.flush()
                self._file.close()
            finally:
                self._file = None
                self._writer = None
        return self._path


def _safe_len(maybe_group) -> int:
    try:
        return len(maybe_group)
    except Exception:
        try:
            return len(list(maybe_group))
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
        # Get movement states from input_obj instead of ship
        f["moving_right"] = bool(getattr(input_obj, "right_pressed", False) if input_obj else False)
        f["moving_left"] = bool(getattr(input_obj, "left_pressed", False) if input_obj else False)
        f["moving_up"] = bool(getattr(input_obj, "up_pressed", False) if input_obj else False)
        f["moving_down"] = bool(getattr(input_obj, "down_pressed", False) if input_obj else False)
    except Exception:
        pass

    # input / mouse
    try:
        if input_obj is not None and hasattr(input_obj, "get_mouse_cursor_position"):
            mx, my = input_obj.get_mouse_cursor_position()
            f["mouse_x"] = int(mx)
            f["mouse_y"] = int(my)
        if input_obj is not None and hasattr(input_obj, "current_mouse_button_states"):
            f["mouse_buttons"] = list(getattr(input_obj, "current_mouse_button_states", []))
    except Exception:
        pass

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
