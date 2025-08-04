"""
Technical indicators module for the SMART STOCK TRADING SYSTEM.
"""

# Import base indicator class
from .base_indicator import BaseIndicator

# Import moving averages
from .moving_averages import (
    SMAIndicator,
    EMAIndicator,
    WMAIndicator,
    HMAIndicator
)

# Import momentum indicators
from .momentum_indicators import (
    RSIIndicator,
    MACDIndicator,
    StochasticIndicator,
    WilliamsRIndicator
)

# Import volatility indicators
from .volatility_indicators import (
    BollingerBandsIndicator,
    ATRIndicator,
    StandardDeviationIndicator
)

# Import volume indicators
from .volume_indicators import (
    OBVIndicator,
    VWAPIndicator,
    MoneyFlowIndexIndicator
)

# Import legacy indicators for backward compatibility
from .indicators import TechnicalIndicators

# Import typing for type hints
from typing import Dict

# Create a comprehensive indicator manager
class IndicatorManager:
    """
    Comprehensive indicator manager that provides access to all indicators.
    """
    
    def __init__(self):
        """Initialize the indicator manager."""
        self.indicators = {}
        self._initialize_indicators()
    
    def _initialize_indicators(self):
        """Initialize all available indicators."""
        # Moving Averages
        self.indicators['sma'] = SMAIndicator(period=20)
        self.indicators['ema'] = EMAIndicator(period=20)
        self.indicators['wma'] = WMAIndicator(period=20)
        self.indicators['hma'] = HMAIndicator(period=20)
        
        # Momentum Indicators
        self.indicators['rsi'] = RSIIndicator(period=14)
        self.indicators['macd'] = MACDIndicator(fast_period=12, slow_period=26, signal_period=9)
        self.indicators['stochastic'] = StochasticIndicator(k_period=14, d_period=3)
        self.indicators['williams_r'] = WilliamsRIndicator(period=14)
        
        # Volatility Indicators
        self.indicators['bollinger_bands'] = BollingerBandsIndicator(period=20, std_dev=2.0)
        self.indicators['atr'] = ATRIndicator(period=14)
        self.indicators['std_dev'] = StandardDeviationIndicator(period=20)
        
        # Volume Indicators
        self.indicators['obv'] = OBVIndicator()
        self.indicators['vwap'] = VWAPIndicator()
        self.indicators['mfi'] = MoneyFlowIndexIndicator(period=14)
        
        # Legacy indicator for backward compatibility
        self.indicators['legacy'] = TechnicalIndicators()
    
    def get_indicator(self, name: str) -> BaseIndicator:
        """
        Get an indicator by name.
        
        Args:
            name: Name of the indicator
            
        Returns:
            Indicator instance
        """
        return self.indicators.get(name)
    
    def get_all_indicators(self) -> Dict[str, BaseIndicator]:
        """
        Get all available indicators.
        
        Returns:
            Dictionary of all indicators
        """
        return self.indicators.copy()
    
    def calculate_all_indicators(self, data):
        """
        Calculate all indicators for the given data.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with all indicators added
        """
        result_data = data.copy()
        
        # Normalize column names first
        if hasattr(result_data, '_normalize_column_names'):
            result_data = result_data._normalize_column_names(result_data)
        else:
            # Create a mapping for column name normalization
            column_mapping = {}
            for col in result_data.columns:
                col_lower = col.lower()
                if col_lower in ['open', 'high', 'low', 'close', 'volume']:
                    column_mapping[col] = col_lower
            
            # Only rename if we have mappings
            if column_mapping:
                result_data = result_data.rename(columns=column_mapping)
                from src.utils.logger import logger
                logger.debug(f"Normalized column names: {column_mapping}")
        
        for name, indicator in self.indicators.items():
            if name != 'legacy':  # Skip legacy indicator
                try:
                    result_data = indicator.calculate(result_data)
                except Exception as e:
                    from src.utils.logger import logger
                    logger.error(f"Error calculating {name}: {e}")
        
        return result_data
    
    def get_all_signals(self, data):
        """
        Get signals from all indicators.
        
        Args:
            data: DataFrame with indicator values
            
        Returns:
            Dictionary of all indicator signals
        """
        signals = {}
        
        for name, indicator in self.indicators.items():
            if name != 'legacy':  # Skip legacy indicator
                try:
                    signals[name] = indicator.get_signals(data)
                except Exception as e:
                    from src.utils.logger import logger
                    logger.error(f"Error getting signals for {name}: {e}")
                    signals[name] = {'signal': 'error', 'strength': 0}
        
        return signals

# Create a global instance for easy access
indicator_manager = IndicatorManager()

# Export main classes and functions
__all__ = [
    'BaseIndicator',
    'IndicatorManager',
    'indicator_manager',
    'SMAIndicator',
    'EMAIndicator',
    'WMAIndicator',
    'HMAIndicator',
    'RSIIndicator',
    'MACDIndicator',
    'StochasticIndicator',
    'WilliamsRIndicator',
    'BollingerBandsIndicator',
    'ATRIndicator',
    'StandardDeviationIndicator',
    'OBVIndicator',
    'VWAPIndicator',
    'MoneyFlowIndexIndicator',
    'TechnicalIndicators'  # Legacy for backward compatibility
] 