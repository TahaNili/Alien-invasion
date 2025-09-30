"""Train a K-Nearest Neighbors classifier on recorder CSV data and save it to models/"""

import argparse
import joblib
import os
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from .utils import find_latest_recording, load_dataset, prepare_xy


def train(csv_path: str | None, out_path: str, k: int = 5):
    if csv_path is None:
        csv_path = find_latest_recording()
        if csv_path is None:
            print("No recording CSV found in data/recordings/")
            return
    print(f"Loading dataset from {csv_path}")
    df = load_dataset(csv_path)
    X, y = prepare_xy(df)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = KNeighborsClassifier(n_neighbors=k)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    print(classification_report(y_test, preds))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    joblib.dump(model, out_path)
    print(f"Saved model to {out_path}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', help='Path to recorder CSV file', default=None)
    parser.add_argument('--out', help='Output model path', default='models/knn.joblib')
    parser.add_argument('--k', help='Number of neighbors', default=5, type=int)
    args = parser.parse_args()
    train(args.csv, args.out, args.k)
