# AI Manager

This document explains how to use `src/ai_manager.py` to train ML models from gameplay recordings.

Overview
--------
`ai_manager` scans `data/recordings/` for CSV files produced by `src/recorder.py`. It preprocesses numeric and boolean features and trains three classifiers:

- Logistic Regression
- Decision Tree
- K-Nearest Neighbors

Trained models are saved under `data/models/` as joblib files. Each saved file contains a dictionary with keys:

- `model`: the trained sklearn pipeline or estimator
- `features`: ordered feature names used for training
- `score`: test accuracy
- `trained_at`: ISO timestamp of training

How to run
----------
Before starting the game, you can run training from the project root:

```powershell
# Train models (will look for recordings in data/recordings)
python -m src.ai_manager --train

# Force retraining even if models exist
python -m src.ai_manager --train --force
```

Notes
-----
- If no recordings are found, the tool will exit with an error.
- If recordings lack the expected movement flags, the training step will warn and abort; play the game while recording to collect richer data.
- Models are saved with metadata so the game can load them for inference.

Integration
-----------
`src.controllers.ml_controller` and `src.ai_manager` can be used together:
- Run `ai_manager` to populate `data/models/` before launching the game
- MLController will attempt to load models at runtime via the AI manager singleton

Troubleshooting
---------------
- If training fails due to missing features, open `data/recordings/*.csv` and ensure columns like `moving_right`, `moving_left`, `moving_up`, `moving_down` are present.
- Use simple sessions (move the ship in different directions) to create balanced data for the classifiers.

Contact
-------
If you want me to tune model hyperparameters, add feature engineering, or implement online learning, tell me which direction you'd prefer.