"""AI Manager for handling ML model training, inference, and evaluation.

This module provides a centralized manager for ML models in the game:
- Automatic training when needed
- Model inference during gameplay
- Live metrics and evaluation
"""

import os
import glob
import logging
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
import joblib

logger = logging.getLogger(__name__)

class AIManager:
    """Manages ML models for the game's AI system."""

    def __init__(self, models_dir='models', recordings_dir='data/recordings'):
        self.models_dir = Path(models_dir)
        self.recordings_dir = Path(recordings_dir)
        self.models = {}
        self.latest_features = None
        self.latest_predictions = {}
        self.model_metrics = {}
        
        # Ensure directories exist
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
    def _find_latest_recording(self):
        """Find the most recent CSV recording file."""
        files = glob.glob(str(self.recordings_dir / "*.csv"))
        if not files:
            return None
        return max(files, key=os.path.getctime)
    
    def _prepare_training_data(self, csv_path):
        """Load and prepare training data from CSV.

        Returns a tuple (X, y). If the CSV cannot be used for training the
        function returns (empty DataFrame, empty Series).
        """
        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            logger.error(f"Error reading CSV {csv_path}: {e}")
            return pd.DataFrame(), pd.Series()

        if df.empty:
            logger.error("Empty CSV file")
            return pd.DataFrame(), pd.Series()

        # Select numeric and boolean columns and fill NaNs with 0
        X = df.select_dtypes(include=['float64', 'int64', 'bool']).fillna(0)

        # Drop common non-feature columns if present
        non_feature_cols = ['frame', 'timestamp', 'dt', 'region_name']
        X = X.drop([c for c in non_feature_cols if c in X.columns], axis=1, errors='ignore')

        if X.empty:
            logger.error("No numeric data found in CSV")
            return pd.DataFrame(), pd.Series()

        # Required movement columns
        movement_cols = ['moving_right', 'moving_left', 'moving_up', 'moving_down']
        missing_cols = [col for col in movement_cols if col not in X.columns]
        if missing_cols:
            logger.warning(f"Missing movement columns in training data: {missing_cols}")
            logger.info("Aborting training data preparation because movement columns are missing")
            return pd.DataFrame(), pd.Series()

        # Build target and remove target columns from X
        try:
            # Convert movement flags to multi-class target: 0=none, 1=left, 2=right, 3=up, 4=down
            y = pd.Series(0, index=X.index)  # Default to 0 (no movement)
            # Set class based on movement flags (prioritize in order: left, right, up, down)
            if 'moving_left' in X.columns:
                y.loc[X['moving_left']] = 1
            if 'moving_right' in X.columns:
                y.loc[X['moving_right']] = 2
            if 'moving_up' in X.columns:
                y.loc[X['moving_up']] = 3
            if 'moving_down' in X.columns:
                y.loc[X['moving_down']] = 4
        except Exception as e:
            logger.error(f"Error constructing target variable: {e}")
            return pd.DataFrame(), pd.Series()

        X = X.drop(movement_cols, axis=1, errors='ignore')

        # Store the exact feature names used for training so we can reindex
        # prediction inputs to the same columns later.
        self.trained_feature_names = list(X.columns)

        return X, y
    
    def train_models_if_needed(self, force=False):
        """Train or reload models as needed."""
        latest_recording = self._find_latest_recording()
        if not latest_recording:
            logger.warning("No recording files found for training")
            return False
            
        recording_time = os.path.getmtime(latest_recording)
        
        # Check if we need to train new models
        models_exist = all(
            os.path.exists(self.models_dir / f"{name}.joblib")
            for name in ['logistic', 'tree', 'knn']
        )
        
        if not force and models_exist:
            # Check if models are newer than recording
            models_time = min(
                os.path.getmtime(self.models_dir / f"{name}.joblib")
                for name in ['logistic', 'tree', 'knn']
            )
            if models_time > recording_time:
                # Models are up to date, load them and verify feature compatibility
                self._load_models()
                # Try to prepare training data columns (without creating y)
                X_candidate, _ = self._prepare_training_data(latest_recording)
                if X_candidate.empty:
                    # Can't validate against recording; assume models are OK
                    return True
                # If loaded models exposed feature metadata, check compatibility
                if hasattr(self, 'trained_feature_names') and self.trained_feature_names:
                    trained_cols = list(self.trained_feature_names)
                    current_cols = list(X_candidate.columns)
                    if trained_cols == current_cols:
                        return True
                    else:
                        logger.info("Existing models feature set differs from latest recording; retraining required")
                        # fall through to retrain
                else:
                    # No feature metadata available; accept existing models
                    return True
        
        # Train new models
        logger.info("Training new models...")
        try:
            X, y = self._prepare_training_data(latest_recording)
            if X.empty or len(y) == 0:
                logger.error("No valid training data available")
                return False
            
            # Check number of available classes
            unique_classes = np.unique(y)
            if len(unique_classes) < 2:
                logger.error("Training data must contain at least two classes")
                logger.info("Please play the game first to collect training data")
                return False
                
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
        except Exception as e:
            logger.error(f"Error preparing training data: {e}")
            return False
        
        # Print class distribution
        logger.info(f"Class distribution: {pd.Series(y).value_counts().sort_index()}")
        
        # Train each model type for multi-class classification
        models = {
            'logistic': LogisticRegression(max_iter=2000, multi_class='multinomial', class_weight='balanced'),
            'tree': DecisionTreeClassifier(max_depth=5, class_weight='balanced'),
            'knn': KNeighborsClassifier(n_neighbors=5)
        }
        
        for name, model in models.items():
            model.fit(X_train, y_train)
            score = model.score(X_test, y_test)
            self.model_metrics[name] = {
                'accuracy': score,
                'train_size': len(X_train),
                'test_size': len(X_test)
            }
            
            # Save model
            joblib.dump(model, self.models_dir / f"{name}.joblib")
            logger.info(f"Trained {name} model (accuracy: {score:.2f})")
        
        self.models = models
        return True
    
    def _load_models(self):
        """Load saved models from disk."""
        self.models = {}
        loaded_feature_sets = []
        for name in ['logistic', 'tree', 'knn']:
            try:
                model_path = self.models_dir / f"{name}.joblib"
                if model_path.exists():
                    self.models[name] = joblib.load(model_path)
                    logger.info(f"Loaded {name} model")
                    # If model exposes feature names recorded during fit, keep them
                    try:
                        feat = getattr(self.models[name], 'feature_names_in_', None)
                        if feat is not None:
                            loaded_feature_sets.append(list(feat))
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"Error loading {name} model: {e}")
        # If one or more models provided feature name metadata, choose the
        # first (they should match if models were trained together).
        if loaded_feature_sets:
            self.trained_feature_names = loaded_feature_sets[0]
    
    def predict(self, features):
        """Get predictions from all models for the current game state."""
        if not self.models:
            logger.warning("No models loaded for prediction")
            return {}
            
        # Store features for metrics/visualization
        self.latest_features = features
        # Prepare feature vector (ensure same columns as training)
        X_raw = pd.DataFrame([features])

        # If we have recorded the trained feature names, reindex to those
        # columns and fill missing values with 0. Otherwise attempt to use
        # numeric columns from the current features.
        if hasattr(self, 'trained_feature_names') and self.trained_feature_names:
            X = X_raw.reindex(columns=self.trained_feature_names).fillna(0)
        else:
            X = X_raw.select_dtypes(include=['float64', 'int64']).fillna(0)
        
        # Get predictions from each model
        predictions = {}
        for name, model in self.models.items():
            try:
                if hasattr(model, 'predict_proba'):
                    pred_proba = model.predict_proba(X)
                    pred_class = int(model.predict(X)[0])
                    predictions[name] = {
                        'class': pred_class,
                        'probabilities': pred_proba[0].tolist()
                    }
                else:
                    pred_class = int(model.predict(X)[0])
                    # For non-probabilistic models, create a one-hot probability vector
                    pred_proba = [0.0] * 5  # One for each class (none, left, right, up, down)
                    pred_proba[pred_class] = 1.0
                    predictions[name] = {
                        'class': pred_class,
                        'probabilities': pred_proba
                    }
            except Exception as e:
                logger.error(f"Prediction error for {name}: {e}")
                predictions[name] = {
                    'class': 0,
                    'probabilities': [1.0, 0.0, 0.0, 0.0, 0.0]  # Default to "no movement"
                }
                
        self.latest_predictions = predictions
        return predictions
    
    def get_visualization_data(self):
        """Get data for visualization plots."""
        if not self.latest_predictions:
            return {
                'probabilities': {},
                'accuracy': self.model_metrics
            }
            
        return {
            'probabilities': {
                name: data['probabilities']
                for name, data in self.latest_predictions.items()
            },
            'accuracy': self.model_metrics
        }

# Global singleton instance
_instance = None

def get_ai_manager():
    """Get or create the global AI manager instance."""
    global _instance
    if _instance is None:
        _instance = AIManager()
    return _instance