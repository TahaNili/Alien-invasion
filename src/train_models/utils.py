"""Utilities for training models from recorder CSV files.

Assumptions:
- The recorder CSV contains a column named 'action' which is the label.
- Feature columns are all other numeric columns.
- If no path is provided, the script will try to find the latest file under data/recordings/.
"""

import os
import glob
import pandas as pd


def find_latest_recording(pattern: str = "data/recordings/*.csv") -> str | None:
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getctime)


def load_dataset(csv_path: str):
    df = pd.read_csv(csv_path)
    return df


def prepare_xy(df: pd.DataFrame):
    if 'action' not in df.columns:
        raise ValueError("Dataset must contain 'action' column as label")
    X = df.select_dtypes(include=["number"]).drop(columns=["action"], errors='ignore')
    y = df['action']
    return X, y
