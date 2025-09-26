Quick summary (what’s working)

- AI is implemented as a single class (`src/ai_manager.py::AIManager`) which:
  - Loads persisted ML models (`models/logreg.joblib`, `models/rf.joblib`, `models/knn.joblib`).
  - Optionally runs a background trainer to refresh models periodically.
  - Exposes `act(...)` called each frame to produce human-like behavior: pick up items, dodge, approach/strafe enemies, and fire when appropriate.
  - Uses `predict_fire(...)` to build a feature vector and ask the loaded model whether to fire. If models are not available it falls back to simple heuristics.
  - When firing, computes a lead/intercept (if possible), produces a firing angle and calls `game_functions.fire_bullet(..., angle=fire_angle)` — so the ship sprite is not forcibly rotated (avoids visual “cheating”).
- `src/game_functions.fire_bullet` has been updated so that if you pass an `angle`, the bullet is spawned heading in that angle and positioned at the ship’s nose, without mutating `ship.angle`.

---

Small contract (inputs / outputs / success criteria)

- Inputs:
  - Game objects for the current frame: `stats` (score, lives), `ship` (position, rect, movement flags, angle), `aliens` (group), `bullets`, `health`, `input`, and optional `alien_bullets`, `items`, `cargoes`, etc.
- Outputs:
  - Side effects on `ship` movement flags: `ship.moving_left/right/up/down`.
  - Possibly add a bullet to `bullets` (via `fire_bullet`) when AI decides to shoot.
- Success criteria:
  - AI fires with higher probability to hit moving aliens (intercept accuracy within tolerance).
  - No unwanted visual mutation of the ship sprite (ship must not instantly rotate to point at target).
  - All modified modules import cleanly; calling `act()` doesn’t crash the game loop.

Edge cases to consider:
- No enemies present → AI should not try to attack.
- Models exist but `predict()`/`predict_proba()` throws → fallback to heuristic behavior.
- Enemy moves faster than bullet speed → intercept equation may produce no positive root.
- Division by zero / target on top of ship.

---

Feature vector — exactly what the model receives

Inside `predict_fire()` the code builds the following ordered feature vector (order matters — if you add/remove features you must retrain models accordingly):

1. stats.score  
2. stats.ships_left  
3. health.current_hearts  
4. ship_x (pixels)  
5. ship_y (pixels)  
6. ship_angle (float; 0 if not present)  
7. ship.moving_left (bool -> 0/1)  
8. ship.moving_right  
9. ship.moving_up  
10. ship.moving_down  
11. mouse_x (currently 0 in code)  
12. mouse_y (currently 0)  
13. bullets_count (number of own bullets)  
14. aliens_count (number of enemies)  
15. nearest_dx (x offset from ship to nearest alien)  
16. nearest_dy  
17. nearest_dist

The code constructs:
X = np.array(feat, dtype=float).reshape(1, -1)

If you add or change features, you must update `src/recorder.py` and re-train in `tools/train_imitation.py`.

---

Decision pipeline (frame → action)

1. In the main loop, if AI is enabled, the game calls `ai_manager.act(...)` once per frame.
2. `act()` performs three prioritized phases:
   - Collect nearby items (move toward if within threshold).
   - Dodge incoming alien bullets (simple heuristic).
   - Attack the nearest alien:
     - Move toward or strafe the target based on distance thresholds.
     - Call `predict_fire(...)` to decide whether to fire this frame.
     - If model says "fire", compute a lead/intercept target position and `fire_angle`.
     - Call `gf.fire_bullet(ship, bullets, angle=fire_angle)` (fallback: call without `angle` if something fails).

---

Intercept (lead) math — derivation and implementation notes

Goal: compute a time t > 0 such that the bullet and target are at the same position at time t.

Assumptions:
- Bullet starts at ship position (or nose) and has constant speed b (scalar).
- Alien has velocity vector v (estimated). Alien position at t=0 is p_a, ship at p_s.
- Relative vector r = p_a - p_s.

Intercept condition:
|r + v t| = b t

Square both sides:
(r + v t)·(r + v t) = b^2 t^2

Expanding gives a quadratic in t:
( v·v - b^2 ) t^2 + 2 ( r·v ) t + ( r·r ) = 0.

Define:
- a = v·v - b^2
- b = 2 ( r·v )
- c = r·r

Solve:
 t = (-b ± sqrt(b^2 - 4ac)) / (2a)

Implementation notes:
- If a ≈ 0 (i.e., ||v|| ≈ b), use the linear fallback t = -c/b if b ≠ 0.
- Choose positive roots only; pick smallest positive t (earliest intercept).
- If no positive root exists, fall back to aiming at alien current position (no lead).
- After selecting t, compute aim = p_a + v * t and compute firing angle from ship to aim.

Example (numerical, approximate):
- ship = (100,100), alien = (300,120) → r = (200, 20)
- alien_speed = 30 px/s, bullet_speed b = 400 px/s
- estimated v ≈ (-29.85, -2.985) (assuming alien moves toward ship)
- rr = 200^2 + 20^2 = 40400
- rv ≈ 200 * -29.85 + 20 * -2.985 ≈ -6029.7
- vv ≈ 900
- a = vv - b^2 ≈ 900 - 160000 = -159100
- b = 2 * rv ≈ -12059.4
- c = 40400
- Discriminant typically positive; pick minimal positive t; compute aim and then
  fire_angle = atan2(-(aim_x - s_x), -(aim_y - s_y)) (this matches the project's `ShipBullet.set_angle` convention).

Note: because current code estimates v as “direction-to-ship × alien_speed_factor”, it’s only approximate. Using actual per-alien velocities (vx, vy) improves accuracy.

---

Implementation locations (where to change things)

- `src/ai_manager.py`
  - `predict_fire(...)` — builds the features and asks the model. Add more features here if you want richer behavior (remember to retrain).
  - `act(...)` — contains item-collect, dodge and attack logic, plus the intercept math. If you want improved lead logic, modify the intercept section here.
- `src/game_functions.py`
  - `fire_bullet(ship, bullets, angle: float | None = None)` — if `angle` is given, the bullet is set to that angle and placed at the ship nose so the ship sprite doesn’t have to rotate.
- `src/alien.py`
  - To improve lead accuracy you should store each alien’s real per-frame velocity (`alien.vx`, `alien.vy`) and update it in `update()`. Then `ai_manager` should use those velocities instead of guessing.
- `src/recorder.py` and `tools/train_imitation.py`
  - If you add new features (e.g., alien vx/vy), you must record those columns and retrain the models.

---

Recommended improvements (practical)

1. Track real alien velocities:
   - In `src/alien.py` compute `vx, vy` each frame (delta position / dt) and store them as attributes.
   - In `ai_manager.act`, use `target.vx, target.vy` rather than a guess computed from `ai_settings`.
2. Limit intercept time:
   - Accept roots only with t < T_max (e.g., 3 seconds) to avoid unrealistic long-range intercepts.
3. Tolerance check:
   - After computing aim, estimate expected miss distance (closest approach) and only fire if predicted miss < tolerance (e.g., 20 px).
4. Debug overlay:
   - When AI is active, draw:
     - predicted aim point (small colored circle),
     - alien velocity vector,
     - bullet path from ship to aim.
   - That visual feedback helps quickly see where it goes wrong.
5. Retrain models if features change:
   - Update recorder, run `tools/train_imitation.py`, generate new joblib models.

---

Debugging & testing

1. Logging:
   - Add logs inside `ai_manager.act` (or a debug mode) to print nearest alien pos, r, v, bullet_speed, a/b/c, discriminant, chosen t, aim coordinates, `predict_fire` output.
   - Use existing `src/log_manager.py` or Python `logging`.
2. Unit test the intercept math:
   - Extract an isolated helper: `compute_intercept(ship_pos, alien_pos, alien_vel, bullet_speed)` returning `(t, aim_pos)` or `None`.
   - Write unit tests with fixed inputs and expected outputs (happy path and edge cases).
3. Smoke test script:
   - A small script that imports all game modules (already used earlier) to catch syntax errors.
4. Visual debugging:
   - Draw the aim and velocity vectors on screen for a few frames and count hit/miss in a small test scenario.
5. Concurrency:
   - If you let the trainer overwrite model files while AI reads them, consider a lock around `load_models()` or atomic writes to avoid partial reads.

---

Concrete example — step-by-step with numbers

Given:
- ship center = (100, 100)
- alien position = (300, 120)
- alien speed (a_speed) = 30 px/s
- bullet_speed (b) = 400 px/s

Steps:
1. r = (200, 20)
2. direction from alien to ship = (s_x - a_x, s_y - a_y) = (-200, -20); norm ≈ 201
3. v ≈ (-29.85, -2.985)
4. a = v·v - b^2 ≈ 900 - 160000 ≈ -159100
5. b = 2 * (r·v) ≈ -12059.4
6. c = r·r = 40400
7. discriminant = b^2 - 4ac → compute, pick smallest positive t (if any)
8. aim = alien_pos + v * t
9. fire_angle computed from ship to aim and `gf.fire_bullet(..., angle=fire_angle)` called.

Note: check what `ShipBullet.set_angle` expects; the code used `atan2(-(aim_x - s_x), -(aim_y - s_y))` to match existing conventions.

---

Common bug sources (checklist)

- Missing or incorrect `settings.BULLET_SPEED_FACTOR` or `ai_settings.alien_speed_factor`.
- Two sources of truth for ship position (`ship.center` vs `ship.rect.centerx`) — unify to one canonical source.
- Mutating `ship.angle` for AI aiming (visual cheating). Use `fire_bullet(..., angle=...)` instead.
- Not handling discriminant < 0 or negative roots → leads to invalid aims.
- Background trainer overwriting models while `load_models()` reads them — use safe replace or locks.
- Unresolved merge markers or partial functions left in files (we cleaned `game_functions` earlier).

---

Short practical plan to start

1. Commit the fixes already applied (if you want me to do it I can) with message:
   - "fix: resolve merge corruption and restore game_functions logic"
2. For better intercept accuracy:
   - Add `vx/vy` to each alien in `src/alien.py`.
   - Use those `vx/vy` in `ai_manager.act`.
   - Add a debug overlay and logs to evaluate improvements.
3. If you change features (e.g., add `vx, vy` to recorder), update `src/recorder.py` and retrain:
   - `python tools/train_imitation.py` to write new `models/*.joblib`.
4. If you want, I can:
   - Extract `compute_intercept(...)` helper and add unit tests for it.
   - Add the debug overlay to `update_screen`.
   - Add detailed logs inside `ai_manager.act`.

---

If you want me to perform any concrete code work now, choose one:
- Extract `compute_intercept(...)` function + unit tests.
- Add per-alien `vx/vy` and wire them into `ai_manager` (I’ll update `src/alien.py` and `src/ai_manager.py`).
- Add debug overlay (draw aim point, velocity vector, bullet path).
- Commit the current fixes and (optionally) push to your remote (I’ll help with the correct git commands).

Which one do you want first?

---

File-by-file developer guide (AI subsystem)

This section documents every AI-related file in the repository, explains what each file does, lists the most important functions and variables you will touch, and gives concrete examples of small edits and tests you can run locally.

1) src/ai_manager.py
   - Purpose: runtime AI controller. Loads models, runs a background trainer, and exposes the `act(...)` and `predict_fire(...)` methods used by the main loop.
   - Important attributes and methods:
      - `self.models_dir` (Path): where joblib models are loaded from.
      - `self.models` (dict): loaded models under keys `logreg`, `rf`, `knn`.
      - `load_models()` : scans `models/` and joblib-loads available models.
      - `_trainer_loop()` : optional background thread that runs `tools/train_imitation.py` periodically and reloads models.
      - `predict_fire(stats, ship, aliens, bullets, health, input)` : builds the feature vector and returns True/False whether to fire.
      - `act(stats, ship, aliens, bullets, health, input, ...)` : high-level behavior (collect/dodge/attack). This is the function you will normally modify when changing runtime AI behavior.
   - Where to change for common tasks:
      - To add features for model inference: update `predict_fire()` and also extend `Recorder.DEFAULT_FIELDS` and `tools/train_imitation.py` so training uses the same fields.
      - To make lead/aiming better: change the intercept section inside `act()` where `vax,vay` and `b_speed` are computed; or replace that section with a call to a small helper `compute_intercept(...)` (example below).
   - Quick example helper (copy into `src/ai_manager.py` or `src/utils.py`):

```python
def compute_intercept(ship_pos, alien_pos, alien_vel, bullet_speed, t_max=3.0):
      """Return (t, aim_pos) or (None, alien_pos) if no intercept.
      ship_pos, alien_pos, alien_vel: (x,y) tuples. bullet_speed scalar.
      """
      rx = alien_pos[0] - ship_pos[0]
      ry = alien_pos[1] - ship_pos[1]
      rv = rx * alien_vel[0] + ry * alien_vel[1]
      vv = alien_vel[0]**2 + alien_vel[1]**2
      rr = rx**2 + ry**2
      a = vv - bullet_speed**2
      b = 2 * rv
      c = rr
      if abs(a) < 1e-6:
            if abs(b) > 1e-6:
                  t = -c / b
                  if 0 < t <= t_max:
                        return t, (alien_pos[0] + alien_vel[0]*t, alien_pos[1] + alien_vel[1]*t)
            return None, alien_pos
      disc = b*b - 4*a*c
      if disc < 0:
            return None, alien_pos
      sd = math.sqrt(disc)
      t1 = (-b + sd) / (2*a)
      t2 = (-b - sd) / (2*a)
      candidates = [t for t in (t1, t2) if t > 0 and t <= t_max]
      if not candidates:
            return None, alien_pos
      t = min(candidates)
      return t, (alien_pos[0] + alien_vel[0]*t, alien_pos[1] + alien_vel[1]*t)
```

   - Small unit test you can run interactively (Python REPL):

```py
from src.ai_manager import compute_intercept
print(compute_intercept((100,100),(300,120),(-29.85,-2.985),400))
```

2) src/recorder.py
   - Purpose: write per-frame CSV rows used to train models. The `Recorder` is initialized in `alien_invasion.py` and `recorder.record(...)` is called each frame when the game is active.
   - Key parts:
      - `Recorder.DEFAULT_FIELDS` : canonical column order used by `tools/train_imitation.py`.
      - `_build_row(...)` : extracts positions, flags, nearest-alien vectors and returns a dict for CSV.
   - How to add a new feature (example: nearest alien vx/vy):
      - Add two new field names to `DEFAULT_FIELDS` (e.g. `nearest_alien_vx`, `nearest_alien_vy`).
      - In `_build_row`, when iterating aliens, also compute and store their `vx/vy` (you need to ensure aliens populate those attributes — see `src/alien.py` below).
      - Re-run `tools/train_imitation.py` to regenerate models that include these features.

3) tools/train_imitation.py
   - Purpose: offline training. It reads `data/gameplay_log.csv`, preprocesses columns, trains three classifiers (LogisticRegression, KNN, RandomForest) and saves them to `models/` as joblib files.
   - Important notes:
      - The script uses the fixed column names list in `load_and_preprocess()` — if you add fields to the recorder, update this list.
      - The script prints classification metrics; use that output to evaluate class imbalance or bad features.
   - Running it locally:

```powershell
python tools/train_imitation.py --data data/gameplay_log.csv
```

4) src/alien.py
   - Purpose: Alien base class and two concrete types. Aliens move toward the ship and include `update()` that changes position and angle.
   - Key methods/fields to use or extend:
      - `update(self, ship)` : calculates a movement angle and updates `self.x`, `self.y`, and `self.rect`.
      - Suggested change for better AI: add velocity tracking by storing previous position and computing `vx`, `vy` every frame. Example change:

```py
      def __init__(...):
            ...
            self.vx = 0.0
            self.vy = 0.0
            self._prev_x = self.x
            self._prev_y = self.y

      def update(self, ship):
            # ... existing movement code ...
            # after updating self.x/self.y:
            self.vx = self.x - self._prev_x
            self.vy = self.y - self._prev_y
            self._prev_x = self.x
            self._prev_y = self.y
```

      - Then `ai_manager` can read `target.vx` and `target.vy` and pass them directly to the intercept helper.

5) src/bullet.py
   - Purpose: bullet base class plus `ShipBullet` and `AlienBullet`. Bullets store `angle` and move using that angle and `speed_factor`.
   - Important contract:
      - `ShipBullet.set_angle(self, source, target)` returns `(angle, x, y)` used by the Bullet constructor to position the bullet.
      - When AI spawns a bullet with `fire_bullet(..., angle=...)`, the code currently sets `new_bullet.angle = angle` and positions the bullet at the ship nose so visuals match.
   - If you change angle conventions, ensure `ShipBullet.set_angle` and `AlienBullet.set_angle` stay consistent.

6) src/ship.py
   - Purpose: player ship sprite, stores `center`, `rect`, `angle`, and movement flags.
   - Important details:
      - `update()` moves `self.center` based on `moving_*` flags and updates `self.rect`.
      - `self.angle` is computed from mouse position (the player aims with mouse). AI should avoid mutating `self.angle` directly; instead spawn bullets with a computed angle.

7) src/game_functions.py (AI-related points)
   - Purpose: game utilities including `fire_bullet`, bullet/alien updates and collisions.
   - AI integration:
      - `fire_bullet(ship, bullets, angle=None)` supports an explicit `angle` parameter so AI can spawn aimed bullets without rotating the ship.
      - `alien_fire(...)` spawns `AlienBullet` instances (used by enemies).

8) models/ (folder)
   - Stores trained joblib models: `logreg.joblib`, `knn.joblib`, `rf.joblib`.
   - Replacement policy: `tools/train_imitation.py` overwrites them when run. If you want atomic reloads avoid partial reads by writing to a temporary filename and renaming.

How to iterate safely (developer workflow)
- Make one small change at a time. Example: add per-alien `vx,vy` and use it in `ai_manager`.
- Add logging to `ai_manager.act` (or use `print`) to observe decision variables each frame (nearest alien, r, v, discriminant, t, aim, should_fire). Keep logging conditional on a debug flag to avoid spamming.
- Re-train models only after you add and record new fields; check `tools/train_imitation.py` prints for metrics.

Commands you'll run frequently

```powershell
# Run import/smoke checks
python -c "import src.ai_manager, src.game_functions, src.recorder; print('imports OK')"

# Run training (from repo root)
python tools/train_imitation.py --data data/gameplay_log.csv

# Run the game (opens a window)
python alien_invasion.py
```

Final notes
- I added this file-by-file guide so you can open each source file and know exactly which functions/attributes to change for specific improvements.
- If you want, I can now implement one of the concrete improvements end-to-end: either extract `compute_intercept()` and unit-test it, or add per-alien `vx/vy` tracking and wire it into `ai_manager.act` and `recorder` (and then retrain models). Tell me which and I will implement it and run quick smoke tests.
