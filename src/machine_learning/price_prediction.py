"""
Price Prediction Model

Uses machine learning models to predict stock prices and trends.
Supports Random Forest, XGBoost, and LightGBM algorithms.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pickle
import os

from ..utils.config_loader import ConfigLoader
from ..utils.logger import get_logger
from ..data_engine.data_engine import DataEngine


class PricePrediction:
    """Machine learning model for price prediction."""
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        """Initialize the price prediction model."""
        self.config = ConfigLoader(config_path)
        self.logger = get_logger(__name__)
        self.data_engine = DataEngine()
        
        # Model configuration
        self.algorithm = self.config.get('machine_learning.models.price_prediction.algorithm')
        self.lookback_period = self.config.get('machine_learning.models.price_prediction.lookback_period')
        self.prediction_horizon = self.config.get('machine_learning.models.price_prediction.prediction_horizon')
        self.retrain_frequency = self.config.get('machine_learning.models.price_prediction.retrain_frequency')
        
        # Model state
        self.model = None
        self.scaler = None
        self.is_trained = False
        self.last_training_date = None
        
        # Model storage
        self.model_dir = "models/"
        os.makedirs(self.model_dir, exist_ok=True)
        
    def prepare_data(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare data for training/prediction."""
        # Select features - handle both uppercase and lowercase column names
        available_features = []
        feature_mapping = {
            'Open': ['Open', 'open'],
            'High': ['High', 'high'],
            'Low': ['Low', 'low'],
            'Close': ['Close', 'close'],
            'Volume': ['Volume', 'volume']
        }
        
        for feature, possible_names in feature_mapping.items():
            for name in possible_names:
                if name in data.columns:
                    available_features.append(name)
                    break
        
        if len(available_features) < 5:
            # If we don't have enough features, use what we have
            available_features = list(data.columns)[:5]
        
        # Normalize data
        from sklearn.preprocessing import MinMaxScaler
        
        if self.scaler is None:
            self.scaler = MinMaxScaler()
            scaled_data = self.scaler.fit_transform(data[available_features])
        else:
            scaled_data = self.scaler.transform(data[available_features])
        
        # Create sequences
        X, y = self._create_sequences(scaled_data)
        
        return X, y
    
    def _create_sequences(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Create sequences for time series prediction."""
        X, y = [], []
        
        for i in range(self.lookback_period, len(data) - self.prediction_horizon + 1):
            # Flatten the sequence for traditional ML models
            sequence = data[i-self.lookback_period:i].flatten()
            X.append(sequence)
            y.append(data[i:i+self.prediction_horizon, 3])  # Close price
        
        return np.array(X), np.array(y)
    
    def build_model(self, input_shape: Tuple[int, int]) -> 'Model':
        """Build the machine learning model."""
        try:
            if self.algorithm == 'random_forest':
                return self._build_random_forest_model()
            elif self.algorithm == 'xgboost':
                return self._build_xgboost_model()
            elif self.algorithm == 'lightgbm':
                return self._build_lightgbm_model()
            else:
                self.logger.error(f"Unknown algorithm: {self.algorithm}")
                return None
        except ImportError as e:
            self.logger.error(f"Required library not installed: {e}")
            return None
    
    def _build_random_forest_model(self):
        """Build Random Forest model."""
        from sklearn.ensemble import RandomForestRegressor
        
        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        return model
    
    def _build_xgboost_model(self):
        """Build XGBoost model."""
        try:
            import xgboost as xgb
            
            model = xgb.XGBRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                n_jobs=-1
            )
            return model
        except ImportError:
            self.logger.error("XGBoost not installed. Falling back to Random Forest.")
            return self._build_random_forest_model()
    
    def _build_lightgbm_model(self):
        """Build LightGBM model."""
        try:
            import lightgbm as lgb
            
            model = lgb.LGBMRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                n_jobs=-1
            )
            return model
        except ImportError:
            self.logger.error("LightGBM not installed. Falling back to Random Forest.")
            return self._build_random_forest_model()
    
    def train(self, symbol: str, period: str = '2y') -> bool:
        """Train the model on historical data."""
        try:
            # Get historical data
            data = self.data_engine.get_data(symbol, period=period)
            if data.empty:
                self.logger.error(f"No data available for {symbol}")
                return False
            
            # Prepare data
            X, y = self.prepare_data(data)
            
            if len(X) < 100:  # Need sufficient data
                self.logger.warning(f"Insufficient data for training: {len(X)} samples")
                return False
            
            # Split data
            split_idx = int(len(X) * 0.8)
            X_train, X_test = X[:split_idx], X[split_idx:]
            y_train, y_test = y[:split_idx], y[split_idx:]
            
            # Build model
            self.model = self.build_model(X_train.shape[1:])
            if self.model is None:
                return False
            
            # Train model
            self.model.fit(X_train, y_train)
            
            # Evaluate model
            train_score = self.model.score(X_train, y_train)
            test_score = self.model.score(X_test, y_test)
            
            self.logger.info(f"Model trained - Train Score: {train_score:.4f}, Test Score: {test_score:.4f}")
            
            # Save model
            self._save_model(symbol)
            
            self.is_trained = True
            self.last_training_date = datetime.now()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error training model: {e}")
            return False
    
    def predict(self, symbol: str, days_ahead: int = 5) -> Optional[List[float]]:
        """Predict future prices."""
        if not self.is_trained or self.model is None:
            self.logger.warning("Model not trained. Training first...")
            if not self.train(symbol):
                return None
        
        try:
            # Get recent data
            data = self.data_engine.get_data(symbol, period='1m')
            if data.empty:
                return None
            
            # Prepare data
            X, _ = self.prepare_data(data)
            if len(X) == 0:
                return None
            
            # Make prediction
            prediction = self.model.predict(X[-1:])
            
            # Inverse transform
            if self.scaler is not None:
                # Create dummy array for inverse transform
                dummy = np.zeros((1, self.scaler.n_features_in_))
                dummy[0, 3] = prediction[0, 0]  # Close price index
                prediction_rescaled = self.scaler.inverse_transform(dummy)[0, 3]
                
                predictions = []
                for i in range(min(days_ahead, len(prediction[0]))):
                    dummy[0, 3] = prediction[0, i]
                    pred_price = self.scaler.inverse_transform(dummy)[0, 3]
                    predictions.append(pred_price)
                
                return predictions
            
            return prediction[0].tolist()
            
        except Exception as e:
            self.logger.error(f"Error making prediction: {e}")
            return None
    
    def _save_model(self, symbol: str):
        """Save the trained model."""
        model_path = os.path.join(self.model_dir, f"{symbol}_{self.algorithm}_model.pkl")
        scaler_path = os.path.join(self.model_dir, f"{symbol}_{self.algorithm}_scaler.pkl")
        
        if self.model is not None:
            with open(model_path, 'wb') as f:
                pickle.dump(self.model, f)
        
        if self.scaler is not None:
            with open(scaler_path, 'wb') as f:
                pickle.dump(self.scaler, f)
        
        self.logger.info(f"Model saved: {model_path}")
    
    def _load_model(self, symbol: str) -> bool:
        """Load a trained model."""
        model_path = os.path.join(self.model_dir, f"{symbol}_{self.algorithm}_model.pkl")
        scaler_path = os.path.join(self.model_dir, f"{symbol}_{self.algorithm}_scaler.pkl")
        
        try:
            if os.path.exists(model_path) and os.path.exists(scaler_path):
                with open(model_path, 'rb') as f:
                    self.model = pickle.load(f)
                
                with open(scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                
                self.is_trained = True
                self.logger.info(f"Model loaded: {model_path}")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Error loading model: {e}")
            return False
    
    def get_prediction_confidence(self, symbol: str) -> float:
        """Get confidence score for predictions."""
        # This is a simplified confidence metric
        # In practice, you might use ensemble methods or uncertainty quantification
        
        if not self.is_trained:
            return 0.0
        
        try:
            # Get recent data for validation
            data = self.data_engine.get_data(symbol, period='1m')
            if data.empty:
                return 0.0
            
            X, y = self.prepare_data(data)
            if len(X) == 0:
                return 0.0
            
            # Calculate prediction error on recent data
            predictions = self.model.predict(X[-10:])
            actual = y[-10:]
            
            mse = np.mean((predictions - actual) ** 2)
            confidence = max(0, 1 - mse / 100)  # Normalize to 0-1
            
            return confidence
            
        except Exception as e:
            self.logger.error(f"Error calculating confidence: {e}")
            return 0.0
    
    def should_retrain(self, symbol: str) -> bool:
        """Check if model should be retrained."""
        if not self.is_trained or self.last_training_date is None:
            return True
        
        days_since_training = (datetime.now() - self.last_training_date).days
        return days_since_training >= self.retrain_frequency
    
    def get_model_info(self) -> Dict:
        """Get model information."""
        return {
            'algorithm': self.algorithm,
            'lookback_period': self.lookback_period,
            'prediction_horizon': self.prediction_horizon,
            'is_trained': self.is_trained,
            'last_training_date': self.last_training_date,
            'retrain_frequency': self.retrain_frequency
        } 