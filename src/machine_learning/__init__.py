"""
Machine Learning Module for the SMART STOCK TRADING SYSTEM.

This module includes:
- Model training and evaluation
- Pattern recognition
- Price prediction
- Risk modeling
- Sentiment analysis
- Independent stock scoring
"""

from .model_trainer import ModelTrainer
from .pattern_recognition import PatternRecognition
from .price_prediction import PricePrediction
from .risk_model import RiskModel
from .sentiment_analysis import SentimentAnalysis
from .stock_scorer import IndependentStockScorer, StockScore, DataSource, ScoringMethod

__all__ = [
    'ModelTrainer',
    'PatternRecognition', 
    'PricePrediction',
    'RiskModel',
    'SentimentAnalysis',
    'IndependentStockScorer',
    'StockScore',
    'DataSource',
    'ScoringMethod'
] 