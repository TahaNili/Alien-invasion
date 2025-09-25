"""Train simple imitation models on recorded gameplay data.

This script expects `data/gameplay_log.csv` to exist and will train models
to predict `mouse_fire` (binary) from low-dim features.

Outputs:
 - prints classification metrics
 - saves models under `models/` (joblib)
"""
from pathlib import Path
import argparse
import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score


DATA_PATH = Path(__file__).parent.parent / "data" / "gameplay_log.csv"
MODELS_DIR = Path(__file__).parent.parent / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


def load_and_preprocess(path: Path):
    df = pd.read_csv(path)

    # Basic cleanup: drop rows with no label
    df = df[df['mouse_fire'].notna()]

    # Fill NA for numeric with 0
    numeric_cols = [
        'score', 'ships_left', 'health', 'ship_x', 'ship_y', 'ship_angle',
        'moving_left', 'moving_right', 'moving_up', 'moving_down',
        'mouse_x', 'mouse_y', 'bullets_count', 'aliens_count',
        'nearest_alien_dx', 'nearest_alien_dy', 'nearest_alien_distance'
    ]
    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

    # Features
    features = [c for c in numeric_cols if c in df.columns]

    X = df[features].values
    y = df['mouse_fire'].astype(int).values

    return X, y, features


def train_and_eval(X, y):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    models = {
        # use class_weight to address class imbalance
        'logreg': Pipeline([('scaler', StandardScaler()), ('clf', LogisticRegression(max_iter=200, class_weight='balanced'))]),
        'knn': Pipeline([('scaler', StandardScaler()), ('clf', KNeighborsClassifier(n_neighbors=5))]),
        'rf': Pipeline([('clf', RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced'))])
    }

    results = {}
    for name, model in models.items():
        print(f"Training {name}...")
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        probs = model.predict_proba(X_test)[:, 1] if hasattr(model, 'predict_proba') else None

        print(f"--- Results for {name} ---")
        print(classification_report(y_test, preds))
        if probs is not None:
            try:
                auc = roc_auc_score(y_test, probs)
                print(f"AUC: {auc:.4f}")
            except Exception:
                pass
        print("Confusion matrix:")
        print(confusion_matrix(y_test, preds))

        # Save model
        joblib.dump(model, MODELS_DIR / f"{name}.joblib")
        results[name] = model

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=str, default=str(DATA_PATH))
    args = parser.parse_args()

    if not Path(args.data).exists():
        print(f"Data file not found: {args.data}")
        return

    X, y, features = load_and_preprocess(Path(args.data))
    print(f"Loaded data. Features: {features}. Samples: {len(y)}")

    train_and_eval(X, y)


if __name__ == '__main__':
    main()
