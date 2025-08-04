"""
Moving averages indicators implementation.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from .base_indicator import BaseIndicator
from src.utils.logger import logger


class SMAIndicator(BaseIndicator):
    """Simple Moving Average (SMA) indicator."""
    
    def __init__(self, period: int = 20):
        """
        Initialize SMA indicator.
        
        Args:
            period: Period for the moving average
        """
        super().__init__(
            name="SMA",
            description="Simple Moving Average - Average of closing prices over a period"
        )
        self.set_parameters({'period': period})
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate SMA values.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with SMA values added
        """
        if not self.validate_data(data):
            return data
        
        period = self.parameters.get('period', 20)
        if not self._validate_period(period):
            return data
        
        try:
            # Calculate SMA
            sma = data['close'].rolling(window=period).mean()
            data[f'sma_{period}'] = sma
            
            # Calculate price position relative to SMA
            data[f'price_vs_sma_{period}'] = data['close'] / sma - 1
            
            self.calculated = True
            self._log_calculation(len(data), f"SMA({period})")
            
        except Exception as e:
            logger.error(f"Error calculating SMA: {e}")
        
        return data
    
    def get_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate trading signals based on SMA.
        
        Args:
            data: DataFrame with SMA values
            
        Returns:
            Dictionary containing signal information
        """
        period = self.parameters.get('period', 20)
        sma_col = f'sma_{period}'
        
        if sma_col not in data.columns:
            return {'signal': 'no_data', 'strength': 0}
        
        latest_data = data.iloc[-1]
        prev_data = data.iloc[-2] if len(data) > 1 else None
        
        signals = {
            'indicator': 'SMA',
            'period': period,
            'current_sma': latest_data[sma_col],
            'current_price': latest_data['close'],
            'price_above_sma': latest_data['close'] > latest_data[sma_col],
            'signal': 'neutral',
            'strength': 0
        }
        
        if prev_data is not None:
            # Price crossing above SMA (bullish)
            if (latest_data['close'] > latest_data[sma_col] and 
                prev_data['close'] <= prev_data[sma_col]):
                signals['signal'] = 'buy'
                signals['strength'] = 0.7
                signals['signal_type'] = 'crossover_up'
            
            # Price crossing below SMA (bearish)
            elif (latest_data['close'] < latest_data[sma_col] and 
                  prev_data['close'] >= prev_data[sma_col]):
                signals['signal'] = 'sell'
                signals['strength'] = 0.7
                signals['signal_type'] = 'crossover_down'
        
        return signals


class EMAIndicator(BaseIndicator):
    """Exponential Moving Average (EMA) indicator."""
    
    def __init__(self, period: int = 20):
        """
        Initialize EMA indicator.
        
        Args:
            period: Period for the moving average
        """
        super().__init__(
            name="EMA",
            description="Exponential Moving Average - Weighted average giving more importance to recent prices"
        )
        self.set_parameters({'period': period})
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate EMA values.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with EMA values added
        """
        if not self.validate_data(data):
            return data
        
        period = self.parameters.get('period', 20)
        if not self._validate_period(period):
            return data
        
        try:
            # Calculate EMA
            ema = data['close'].ewm(span=period).mean()
            data[f'ema_{period}'] = ema
            
            # Calculate price position relative to EMA
            data[f'price_vs_ema_{period}'] = data['close'] / ema - 1
            
            self.calculated = True
            self._log_calculation(len(data), f"EMA({period})")
            
        except Exception as e:
            logger.error(f"Error calculating EMA: {e}")
        
        return data
    
    def get_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate trading signals based on EMA.
        
        Args:
            data: DataFrame with EMA values
            
        Returns:
            Dictionary containing signal information
        """
        period = self.parameters.get('period', 20)
        ema_col = f'ema_{period}'
        
        if ema_col not in data.columns:
            return {'signal': 'no_data', 'strength': 0}
        
        latest_data = data.iloc[-1]
        prev_data = data.iloc[-2] if len(data) > 1 else None
        
        signals = {
            'indicator': 'EMA',
            'period': period,
            'current_ema': latest_data[ema_col],
            'current_price': latest_data['close'],
            'price_above_ema': latest_data['close'] > latest_data[ema_col],
            'signal': 'neutral',
            'strength': 0
        }
        
        if prev_data is not None:
            # Price crossing above EMA (bullish)
            if (latest_data['close'] > latest_data[ema_col] and 
                prev_data['close'] <= prev_data[ema_col]):
                signals['signal'] = 'buy'
                signals['strength'] = 0.8
                signals['signal_type'] = 'crossover_up'
            
            # Price crossing below EMA (bearish)
            elif (latest_data['close'] < latest_data[ema_col] and 
                  prev_data['close'] >= prev_data[ema_col]):
                signals['signal'] = 'sell'
                signals['strength'] = 0.8
                signals['signal_type'] = 'crossover_down'
        
        return signals


class WMAIndicator(BaseIndicator):
    """Weighted Moving Average (WMA) indicator."""
    
    def __init__(self, period: int = 20):
        """
        Initialize WMA indicator.
        
        Args:
            period: Period for the moving average
        """
        super().__init__(
            name="WMA",
            description="Weighted Moving Average - Linear weighted average of prices"
        )
        self.set_parameters({'period': period})
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate WMA values.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with WMA values added
        """
        if not self.validate_data(data):
            return data
        
        period = self.parameters.get('period', 20)
        if not self._validate_period(period):
            return data
        
        try:
            # Calculate weights
            weights = np.arange(1, period + 1)
            
            # Calculate WMA using rolling apply
            def wma_apply(x):
                if len(x) < period:
                    return np.nan
                return np.average(x, weights=weights)
            
            wma = data['close'].rolling(window=period).apply(wma_apply)
            data[f'wma_{period}'] = wma
            
            # Calculate price position relative to WMA
            data[f'price_vs_wma_{period}'] = data['close'] / wma - 1
            
            self.calculated = True
            self._log_calculation(len(data), f"WMA({period})")
            
        except Exception as e:
            logger.error(f"Error calculating WMA: {e}")
        
        return data
    
    def get_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate trading signals based on WMA.
        
        Args:
            data: DataFrame with WMA values
            
        Returns:
            Dictionary containing signal information
        """
        period = self.parameters.get('period', 20)
        wma_col = f'wma_{period}'
        
        if wma_col not in data.columns:
            return {'signal': 'no_data', 'strength': 0}
        
        latest_data = data.iloc[-1]
        prev_data = data.iloc[-2] if len(data) > 1 else None
        
        signals = {
            'indicator': 'WMA',
            'period': period,
            'current_wma': latest_data[wma_col],
            'current_price': latest_data['close'],
            'price_above_wma': latest_data['close'] > latest_data[wma_col],
            'signal': 'neutral',
            'strength': 0
        }
        
        if prev_data is not None:
            # Price crossing above WMA (bullish)
            if (latest_data['close'] > latest_data[wma_col] and 
                prev_data['close'] <= prev_data[wma_col]):
                signals['signal'] = 'buy'
                signals['strength'] = 0.6
                signals['signal_type'] = 'crossover_up'
            
            # Price crossing below WMA (bearish)
            elif (latest_data['close'] < latest_data[wma_col] and 
                  prev_data['close'] >= prev_data[wma_col]):
                signals['signal'] = 'sell'
                signals['strength'] = 0.6
                signals['signal_type'] = 'crossover_down'
        
        return signals


class HMAIndicator(BaseIndicator):
    """Hull Moving Average (HMA) indicator."""
    
    def __init__(self, period: int = 20):
        """
        Initialize HMA indicator.
        
        Args:
            period: Period for the moving average
        """
        super().__init__(
            name="HMA",
            description="Hull Moving Average - Smoothed moving average that reduces lag"
        )
        self.set_parameters({'period': period})
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate HMA values.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with HMA values added
        """
        if not self.validate_data(data):
            return data
        
        period = self.parameters.get('period', 20)
        if not self._validate_period(period):
            return data
        
        try:
            # Calculate HMA
            half_period = period // 2
            sqrt_period = int(np.sqrt(period))
            
            # WMA of half period
            wma_half = self._calculate_wma(data['close'], half_period)
            
            # WMA of full period
            wma_full = self._calculate_wma(data['close'], period)
            
            # Raw HMA
            raw_hma = 2 * wma_half - wma_full
            
            # Final HMA (WMA of raw HMA)
            hma = self._calculate_wma(raw_hma, sqrt_period)
            
            data[f'hma_{period}'] = hma
            
            # Calculate price position relative to HMA
            data[f'price_vs_hma_{period}'] = data['close'] / hma - 1
            
            self.calculated = True
            self._log_calculation(len(data), f"HMA({period})")
            
        except Exception as e:
            logger.error(f"Error calculating HMA: {e}")
        
        return data
    
    def _calculate_wma(self, series: pd.Series, period: int) -> pd.Series:
        """Calculate WMA for a series."""
        weights = np.arange(1, period + 1)
        
        def wma_apply(x):
            if len(x) < period:
                return np.nan
            return np.average(x, weights=weights)
        
        return series.rolling(window=period).apply(wma_apply)
    
    def get_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate trading signals based on HMA.
        
        Args:
            data: DataFrame with HMA values
            
        Returns:
            Dictionary containing signal information
        """
        period = self.parameters.get('period', 20)
        hma_col = f'hma_{period}'
        
        if hma_col not in data.columns:
            return {'signal': 'no_data', 'strength': 0}
        
        latest_data = data.iloc[-1]
        prev_data = data.iloc[-2] if len(data) > 1 else None
        
        signals = {
            'indicator': 'HMA',
            'period': period,
            'current_hma': latest_data[hma_col],
            'current_price': latest_data['close'],
            'price_above_hma': latest_data['close'] > latest_data[hma_col],
            'signal': 'neutral',
            'strength': 0
        }
        
        if prev_data is not None:
            # Price crossing above HMA (bullish)
            if (latest_data['close'] > latest_data[hma_col] and 
                prev_data['close'] <= prev_data[hma_col]):
                signals['signal'] = 'buy'
                signals['strength'] = 0.9
                signals['signal_type'] = 'crossover_up'
            
            # Price crossing below HMA (bearish)
            elif (latest_data['close'] < latest_data[hma_col] and 
                  prev_data['close'] >= prev_data[hma_col]):
                signals['signal'] = 'sell'
                signals['strength'] = 0.9
                signals['signal_type'] = 'crossover_down'
        
        return signals 