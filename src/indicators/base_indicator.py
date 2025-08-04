"""
Base indicator abstract class for technical indicators.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple, Union
import pandas as pd
import numpy as np
from src.utils.logger import logger


class BaseIndicator(ABC):
    """
    Abstract base class for all technical indicators.
    
    This class provides a common interface and functionality for all indicators.
    Each indicator should inherit from this class and implement the required methods.
    """
    
    def __init__(self, name: str, description: str = ""):
        """
        Initialize the base indicator.
        
        Args:
            name: Name of the indicator
            description: Description of what the indicator measures
        """
        self.name = name
        self.description = description
        self.parameters = {}
        self.calculated = False
        self.data = None
        
    @abstractmethod
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate the indicator values.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with indicator values added
        """
        pass
    
    @abstractmethod
    def get_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate trading signals based on the indicator.
        
        Args:
            data: DataFrame with indicator values
            
        Returns:
            Dictionary containing signal information
        """
        pass
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """
        Validate that the input data has required columns.
        Handles different column name formats (capitalized vs lowercase).
        
        Args:
            data: DataFrame to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        # Define possible column name mappings
        column_mappings = {
            'open': ['open', 'Open', 'OPEN'],
            'high': ['high', 'High', 'HIGH'],
            'low': ['low', 'Low', 'LOW'],
            'close': ['close', 'Close', 'CLOSE'],
            'volume': ['volume', 'Volume', 'VOLUME']
        }
        
        # Check if we have the required columns in any format
        missing_columns = []
        for required_col, possible_names in column_mappings.items():
            if not any(name in data.columns for name in possible_names):
                missing_columns.append(required_col)
        
        if missing_columns:
            logger.error(f"Missing required columns for {self.name}: {missing_columns}")
            logger.error(f"Available columns: {list(data.columns)}")
            return False
        
        if data.empty:
            logger.error(f"Empty data provided for {self.name}")
            return False
        
        return True
    
    def _normalize_column_names(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize column names to lowercase for consistent processing.
        
        Args:
            data: DataFrame with potentially mixed case column names
            
        Returns:
            DataFrame with normalized column names
        """
        # Create a mapping for column name normalization
        column_mapping = {}
        for col in data.columns:
            col_lower = col.lower()
            if col_lower in ['open', 'high', 'low', 'close', 'volume']:
                column_mapping[col] = col_lower
        
        # Only rename if we have mappings
        if column_mapping:
            data = data.rename(columns=column_mapping)
            logger.debug(f"Normalized column names: {column_mapping}")
        
        return data
    
    def set_parameters(self, parameters: Dict[str, Any]) -> None:
        """
        Set indicator parameters.
        
        Args:
            parameters: Dictionary of parameter names and values
        """
        self.parameters.update(parameters)
        logger.debug(f"Set parameters for {self.name}: {parameters}")
    
    def get_parameters(self) -> Dict[str, Any]:
        """
        Get current indicator parameters.
        
        Returns:
            Dictionary of current parameters
        """
        return self.parameters.copy()
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get indicator information.
        
        Returns:
            Dictionary with indicator information
        """
        return {
            'name': self.name,
            'description': self.description,
            'parameters': self.parameters,
            'calculated': self.calculated
        }
    
    def _validate_period(self, period: int, min_period: int = 1, max_period: int = 1000) -> bool:
        """
        Validate that a period parameter is within acceptable range.
        
        Args:
            period: Period to validate
            min_period: Minimum allowed period
            max_period: Maximum allowed period
            
        Returns:
            True if period is valid, False otherwise
        """
        if not isinstance(period, int) or period < min_period or period > max_period:
            logger.error(f"Invalid period {period} for {self.name}. Must be between {min_period} and {max_period}")
            return False
        return True
    
    def _handle_nan_values(self, data: pd.DataFrame, method: str = 'drop') -> pd.DataFrame:
        """
        Handle NaN values in the data.
        
        Args:
            data: DataFrame with potential NaN values
            method: Method to handle NaN values ('drop', 'fill', 'ignore')
            
        Returns:
            DataFrame with NaN values handled
        """
        if method == 'drop':
            return data.dropna()
        elif method == 'fill':
            return data.fillna(method='ffill').fillna(method='bfill')
        elif method == 'ignore':
            return data
        else:
            logger.warning(f"Unknown NaN handling method: {method}. Using 'ignore'")
            return data
    
    def _log_calculation(self, data_length: int, indicator_name: str) -> None:
        """
        Log indicator calculation information.
        
        Args:
            data_length: Number of data points processed
            indicator_name: Name of the indicator being calculated
        """
        logger.debug(f"Calculated {indicator_name} for {data_length} data points")
    
    def __str__(self) -> str:
        """String representation of the indicator."""
        return f"{self.name}: {self.description}"
    
    def __repr__(self) -> str:
        """Detailed string representation of the indicator."""
        return f"{self.__class__.__name__}(name='{self.name}', parameters={self.parameters})" 