"""
Volatility indicators implementation.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from .base_indicator import BaseIndicator
from src.utils.logger import logger


class BollingerBandsIndicator(BaseIndicator):
    """Bollinger Bands indicator."""
    
    def __init__(self, period: int = 20, std_dev: float = 2.0):
        """
        Initialize Bollinger Bands indicator.
        
        Args:
            period: Period for SMA calculation
            std_dev: Number of standard deviations
        """
        super().__init__(
            name="Bollinger Bands",
            description="Bollinger Bands - Volatility indicator with upper and lower bands"
        )
        self.set_parameters({'period': period, 'std_dev': std_dev})
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Bollinger Bands values.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with Bollinger Bands values added
        """
        if not self.validate_data(data):
            return data
        
        period = self.parameters.get('period', 20)
        std_dev = self.parameters.get('std_dev', 2.0)
        
        if not self._validate_period(period):
            return data
        
        try:
            # Calculate SMA
            sma = data['close'].rolling(window=period).mean()
            
            # Calculate standard deviation
            std = data['close'].rolling(window=period).std()
            
            # Calculate bands
            upper_band = sma + (std * std_dev)
            lower_band = sma - (std * std_dev)
            
            # Add to dataframe
            data[f'bb_upper_{period}_{std_dev}'] = upper_band
            data[f'bb_middle_{period}_{std_dev}'] = sma
            data[f'bb_lower_{period}_{std_dev}'] = lower_band
            
            # Calculate bandwidth and %B
            bandwidth = (upper_band - lower_band) / sma
            percent_b = (data['close'] - lower_band) / (upper_band - lower_band)
            
            data[f'bb_bandwidth_{period}_{std_dev}'] = bandwidth
            data[f'bb_percent_b_{period}_{std_dev}'] = percent_b
            
            self.calculated = True
            self._log_calculation(len(data), f"Bollinger Bands({period},{std_dev})")
            
        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands: {e}")
        
        return data
    
    def get_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate trading signals based on Bollinger Bands.
        
        Args:
            data: DataFrame with Bollinger Bands values
            
        Returns:
            Dictionary containing signal information
        """
        period = self.parameters.get('period', 20)
        std_dev = self.parameters.get('std_dev', 2.0)
        
        upper_col = f'bb_upper_{period}_{std_dev}'
        lower_col = f'bb_lower_{period}_{std_dev}'
        percent_b_col = f'bb_percent_b_{period}_{std_dev}'
        
        if upper_col not in data.columns:
            return {'signal': 'no_data', 'strength': 0}
        
        latest_data = data.iloc[-1]
        prev_data = data.iloc[-2] if len(data) > 1 else None
        
        current_price = latest_data['close']
        current_upper = latest_data[upper_col]
        current_lower = latest_data[lower_col]
        current_percent_b = latest_data[percent_b_col]
        
        signals = {
            'indicator': 'Bollinger Bands',
            'period': period,
            'std_dev': std_dev,
            'current_price': current_price,
            'upper_band': current_upper,
            'lower_band': current_lower,
            'percent_b': current_percent_b,
            'price_above_upper': current_price > current_upper,
            'price_below_lower': current_price < current_lower,
            'signal': 'neutral',
            'strength': 0
        }
        
        if prev_data is not None:
            prev_price = prev_data['close']
            prev_upper = prev_data[upper_col]
            prev_lower = prev_data[lower_col]
            
            # Price crossing below lower band (bullish - potential bounce)
            if (current_price < current_lower and prev_price >= prev_lower):
                signals['signal'] = 'buy'
                signals['strength'] = 0.7
                signals['signal_type'] = 'lower_band_crossover'
            
            # Price crossing above upper band (bearish - potential reversal)
            elif (current_price > current_upper and prev_price <= prev_upper):
                signals['signal'] = 'sell'
                signals['strength'] = 0.7
                signals['signal_type'] = 'upper_band_crossover'
            
            # Price near lower band (oversold)
            elif current_percent_b < 0.1:
                signals['signal'] = 'buy'
                signals['strength'] = 0.6
                signals['signal_type'] = 'oversold'
            
            # Price near upper band (overbought)
            elif current_percent_b > 0.9:
                signals['signal'] = 'sell'
                signals['strength'] = 0.6
                signals['signal_type'] = 'overbought'
        
        return signals


class ATRIndicator(BaseIndicator):
    """Average True Range (ATR) indicator."""
    
    def __init__(self, period: int = 14):
        """
        Initialize ATR indicator.
        
        Args:
            period: Period for ATR calculation
        """
        super().__init__(
            name="ATR",
            description="Average True Range - Volatility indicator measuring market volatility"
        )
        self.set_parameters({'period': period})
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate ATR values.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with ATR values added
        """
        if not self.validate_data(data):
            return data
        
        period = self.parameters.get('period', 14)
        if not self._validate_period(period):
            return data
        
        try:
            # Calculate True Range
            high_low = data['high'] - data['low']
            high_close = np.abs(data['high'] - data['close'].shift())
            low_close = np.abs(data['low'] - data['close'].shift())
            
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            
            # Calculate ATR
            atr = true_range.rolling(window=period).mean()
            
            # Add to dataframe
            data[f'atr_{period}'] = atr
            data[f'true_range_{period}'] = true_range
            
            # Calculate ATR percentage of price
            data[f'atr_percent_{period}'] = (atr / data['close']) * 100
            
            self.calculated = True
            self._log_calculation(len(data), f"ATR({period})")
            
        except Exception as e:
            logger.error(f"Error calculating ATR: {e}")
        
        return data
    
    def get_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate trading signals based on ATR.
        
        Args:
            data: DataFrame with ATR values
            
        Returns:
            Dictionary containing signal information
        """
        period = self.parameters.get('period', 14)
        atr_col = f'atr_{period}'
        atr_percent_col = f'atr_percent_{period}'
        
        if atr_col not in data.columns:
            return {'signal': 'no_data', 'strength': 0}
        
        latest_data = data.iloc[-1]
        prev_data = data.iloc[-2] if len(data) > 1 else None
        
        current_atr = latest_data[atr_col]
        current_atr_percent = latest_data[atr_percent_col]
        
        signals = {
            'indicator': 'ATR',
            'period': period,
            'current_atr': current_atr,
            'current_atr_percent': current_atr_percent,
            'high_volatility': current_atr_percent > 5.0,
            'low_volatility': current_atr_percent < 1.0,
            'signal': 'neutral',
            'strength': 0
        }
        
        if prev_data is not None:
            prev_atr = prev_data[atr_col]
            
            # Increasing volatility (potential breakout)
            if current_atr > prev_atr * 1.2:
                signals['signal'] = 'volatility_increase'
                signals['strength'] = 0.5
                signals['signal_type'] = 'volatility_spike'
            
            # Decreasing volatility (potential consolidation)
            elif current_atr < prev_atr * 0.8:
                signals['signal'] = 'volatility_decrease'
                signals['strength'] = 0.3
                signals['signal_type'] = 'volatility_contraction'
        
        return signals


class StandardDeviationIndicator(BaseIndicator):
    """Standard Deviation indicator."""
    
    def __init__(self, period: int = 20):
        """
        Initialize Standard Deviation indicator.
        
        Args:
            period: Period for calculation
        """
        super().__init__(
            name="Standard Deviation",
            description="Standard Deviation - Volatility measure of price dispersion"
        )
        self.set_parameters({'period': period})
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Standard Deviation values.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with Standard Deviation values added
        """
        if not self.validate_data(data):
            return data
        
        period = self.parameters.get('period', 20)
        if not self._validate_period(period):
            return data
        
        try:
            # Calculate standard deviation of closing prices
            std_dev = data['close'].rolling(window=period).std()
            
            # Calculate mean for reference
            mean_price = data['close'].rolling(window=period).mean()
            
            # Add to dataframe
            data[f'std_dev_{period}'] = std_dev
            data[f'mean_price_{period}'] = mean_price
            
            # Calculate coefficient of variation
            data[f'cv_{period}'] = (std_dev / mean_price) * 100
            
            # Calculate price position relative to mean
            data[f'price_vs_mean_{period}'] = (data['close'] - mean_price) / std_dev
            
            self.calculated = True
            self._log_calculation(len(data), f"Standard Deviation({period})")
            
        except Exception as e:
            logger.error(f"Error calculating Standard Deviation: {e}")
        
        return data
    
    def get_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate trading signals based on Standard Deviation.
        
        Args:
            data: DataFrame with Standard Deviation values
            
        Returns:
            Dictionary containing signal information
        """
        period = self.parameters.get('period', 20)
        std_col = f'std_dev_{period}'
        cv_col = f'cv_{period}'
        price_vs_mean_col = f'price_vs_mean_{period}'
        
        if std_col not in data.columns:
            return {'signal': 'no_data', 'strength': 0}
        
        latest_data = data.iloc[-1]
        prev_data = data.iloc[-2] if len(data) > 1 else None
        
        current_std = latest_data[std_col]
        current_cv = latest_data[cv_col]
        current_price_vs_mean = latest_data[price_vs_mean_col]
        
        signals = {
            'indicator': 'Standard Deviation',
            'period': period,
            'current_std': current_std,
            'current_cv': current_cv,
            'current_price_vs_mean': current_price_vs_mean,
            'high_volatility': current_cv > 3.0,
            'low_volatility': current_cv < 1.0,
            'price_extreme': abs(current_price_vs_mean) > 2.0,
            'signal': 'neutral',
            'strength': 0
        }
        
        if prev_data is not None:
            prev_std = prev_data[std_col]
            
            # Increasing volatility
            if current_std > prev_std * 1.1:
                signals['signal'] = 'volatility_increase'
                signals['strength'] = 0.4
                signals['signal_type'] = 'std_increase'
            
            # Decreasing volatility
            elif current_std < prev_std * 0.9:
                signals['signal'] = 'volatility_decrease'
                signals['strength'] = 0.3
                signals['signal_type'] = 'std_decrease'
            
            # Price at extreme levels (mean reversion opportunity)
            elif abs(current_price_vs_mean) > 2.0:
                if current_price_vs_mean > 2.0:
                    signals['signal'] = 'sell'
                    signals['strength'] = 0.6
                    signals['signal_type'] = 'mean_reversion_high'
                else:
                    signals['signal'] = 'buy'
                    signals['strength'] = 0.6
                    signals['signal_type'] = 'mean_reversion_low'
        
        return signals 