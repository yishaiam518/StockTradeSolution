"""
Momentum indicators implementation.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from .base_indicator import BaseIndicator
from src.utils.logger import logger


class RSIIndicator(BaseIndicator):
    """Relative Strength Index (RSI) indicator."""
    
    def __init__(self, period: int = 14):
        """
        Initialize RSI indicator.
        
        Args:
            period: Period for RSI calculation
        """
        super().__init__(
            name="RSI",
            description="Relative Strength Index - Momentum oscillator measuring speed and magnitude of price changes"
        )
        self.set_parameters({'period': period})
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate RSI values.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with RSI values added
        """
        if not self.validate_data(data):
            return data
        
        period = self.parameters.get('period', 14)
        if not self._validate_period(period):
            return data
        
        try:
            # Calculate price changes
            delta = data['close'].diff()
            
            # Separate gains and losses
            gains = delta.where(delta > 0, 0)
            losses = -delta.where(delta < 0, 0)
            
            # Calculate average gains and losses
            avg_gains = gains.rolling(window=period).mean()
            avg_losses = losses.rolling(window=period).mean()
            
            # Calculate RS and RSI
            rs = avg_gains / avg_losses
            rsi = 100 - (100 / (1 + rs))
            
            data[f'rsi_{period}'] = rsi
            
            # Add overbought/oversold levels
            data[f'rsi_overbought_{period}'] = 70
            data[f'rsi_oversold_{period}'] = 30
            
            self.calculated = True
            self._log_calculation(len(data), f"RSI({period})")
            
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")
        
        return data
    
    def get_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate trading signals based on RSI.
        
        Args:
            data: DataFrame with RSI values
            
        Returns:
            Dictionary containing signal information
        """
        period = self.parameters.get('period', 14)
        rsi_col = f'rsi_{period}'
        
        if rsi_col not in data.columns:
            return {'signal': 'no_data', 'strength': 0}
        
        latest_data = data.iloc[-1]
        prev_data = data.iloc[-2] if len(data) > 1 else None
        
        current_rsi = latest_data[rsi_col]
        
        signals = {
            'indicator': 'RSI',
            'period': period,
            'current_rsi': current_rsi,
            'overbought': current_rsi > 70,
            'oversold': current_rsi < 30,
            'signal': 'neutral',
            'strength': 0
        }
        
        if prev_data is not None:
            prev_rsi = prev_data[rsi_col]
            
            # RSI crossing above oversold level (bullish)
            if (current_rsi > 30 and prev_rsi <= 30):
                signals['signal'] = 'buy'
                signals['strength'] = 0.8
                signals['signal_type'] = 'oversold_crossover'
            
            # RSI crossing below overbought level (bearish)
            elif (current_rsi < 70 and prev_rsi >= 70):
                signals['signal'] = 'sell'
                signals['strength'] = 0.8
                signals['signal_type'] = 'overbought_crossover'
            
            # RSI divergence signals
            elif current_rsi < 30:
                signals['signal'] = 'buy'
                signals['strength'] = 0.6
                signals['signal_type'] = 'oversold'
            
            elif current_rsi > 70:
                signals['signal'] = 'sell'
                signals['strength'] = 0.6
                signals['signal_type'] = 'overbought'
        
        return signals


class MACDIndicator(BaseIndicator):
    """Moving Average Convergence Divergence (MACD) indicator."""
    
    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        """
        Initialize MACD indicator.
        
        Args:
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line period
        """
        super().__init__(
            name="MACD",
            description="Moving Average Convergence Divergence - Trend-following momentum indicator"
        )
        self.set_parameters({
            'fast_period': fast_period,
            'slow_period': slow_period,
            'signal_period': signal_period
        })
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate MACD values.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with MACD values added
        """
        if not self.validate_data(data):
            return data
        
        fast_period = self.parameters.get('fast_period', 12)
        slow_period = self.parameters.get('slow_period', 26)
        signal_period = self.parameters.get('signal_period', 9)
        
        if not all(self._validate_period(p) for p in [fast_period, slow_period, signal_period]):
            return data
        
        try:
            # Calculate EMAs
            ema_fast = data['close'].ewm(span=fast_period).mean()
            ema_slow = data['close'].ewm(span=slow_period).mean()
            
            # Calculate MACD line
            macd_line = ema_fast - ema_slow
            
            # Calculate signal line
            signal_line = macd_line.ewm(span=signal_period).mean()
            
            # Calculate histogram
            histogram = macd_line - signal_line
            
            # Add to dataframe
            data[f'macd_line_{fast_period}_{slow_period}'] = macd_line
            data[f'macd_signal_{fast_period}_{slow_period}_{signal_period}'] = signal_line
            data[f'macd_histogram_{fast_period}_{slow_period}_{signal_period}'] = histogram
            
            # Calculate crossover signals
            data[f'macd_crossover_up_{fast_period}_{slow_period}_{signal_period}'] = (
                (macd_line > signal_line) & (macd_line.shift(1) <= signal_line.shift(1))
            )
            data[f'macd_crossover_down_{fast_period}_{slow_period}_{signal_period}'] = (
                (macd_line < signal_line) & (macd_line.shift(1) >= signal_line.shift(1))
            )
            
            self.calculated = True
            self._log_calculation(len(data), f"MACD({fast_period},{slow_period},{signal_period})")
            
        except Exception as e:
            logger.error(f"Error calculating MACD: {e}")
        
        return data
    
    def get_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate trading signals based on MACD.
        
        Args:
            data: DataFrame with MACD values
            
        Returns:
            Dictionary containing signal information
        """
        fast_period = self.parameters.get('fast_period', 12)
        slow_period = self.parameters.get('slow_period', 26)
        signal_period = self.parameters.get('signal_period', 9)
        
        macd_line_col = f'macd_line_{fast_period}_{slow_period}'
        signal_col = f'macd_signal_{fast_period}_{slow_period}_{signal_period}'
        histogram_col = f'macd_histogram_{fast_period}_{slow_period}_{signal_period}'
        
        if macd_line_col not in data.columns:
            return {'signal': 'no_data', 'strength': 0}
        
        latest_data = data.iloc[-1]
        prev_data = data.iloc[-2] if len(data) > 1 else None
        
        signals = {
            'indicator': 'MACD',
            'fast_period': fast_period,
            'slow_period': slow_period,
            'signal_period': signal_period,
            'current_macd': latest_data[macd_line_col],
            'current_signal': latest_data[signal_col],
            'current_histogram': latest_data[histogram_col],
            'macd_above_signal': latest_data[macd_line_col] > latest_data[signal_col],
            'signal': 'neutral',
            'strength': 0
        }
        
        if prev_data is not None:
            # MACD crossing above signal line (bullish)
            if (latest_data[macd_line_col] > latest_data[signal_col] and 
                prev_data[macd_line_col] <= prev_data[signal_col]):
                signals['signal'] = 'buy'
                signals['strength'] = 0.8
                signals['signal_type'] = 'crossover_up'
            
            # MACD crossing below signal line (bearish)
            elif (latest_data[macd_line_col] < latest_data[signal_col] and 
                  prev_data[macd_line_col] >= prev_data[signal_col]):
                signals['signal'] = 'sell'
                signals['strength'] = 0.8
                signals['signal_type'] = 'crossover_down'
            
            # Histogram turning positive (bullish)
            elif (latest_data[histogram_col] > 0 and prev_data[histogram_col] <= 0):
                signals['signal'] = 'buy'
                signals['strength'] = 0.6
                signals['signal_type'] = 'histogram_positive'
            
            # Histogram turning negative (bearish)
            elif (latest_data[histogram_col] < 0 and prev_data[histogram_col] >= 0):
                signals['signal'] = 'sell'
                signals['strength'] = 0.6
                signals['signal_type'] = 'histogram_negative'
        
        return signals


class StochasticIndicator(BaseIndicator):
    """Stochastic Oscillator indicator."""
    
    def __init__(self, k_period: int = 14, d_period: int = 3):
        """
        Initialize Stochastic indicator.
        
        Args:
            k_period: %K period
            d_period: %D period
        """
        super().__init__(
            name="Stochastic",
            description="Stochastic Oscillator - Momentum indicator comparing closing price to price range"
        )
        self.set_parameters({'k_period': k_period, 'd_period': d_period})
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Stochastic values.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with Stochastic values added
        """
        if not self.validate_data(data):
            return data
        
        k_period = self.parameters.get('k_period', 14)
        d_period = self.parameters.get('d_period', 3)
        
        if not all(self._validate_period(p) for p in [k_period, d_period]):
            return data
        
        try:
            # Calculate %K
            lowest_low = data['low'].rolling(window=k_period).min()
            highest_high = data['high'].rolling(window=k_period).max()
            
            k_percent = 100 * ((data['close'] - lowest_low) / (highest_high - lowest_low))
            
            # Calculate %D (SMA of %K)
            d_percent = k_percent.rolling(window=d_period).mean()
            
            data[f'stoch_k_{k_period}'] = k_percent
            data[f'stoch_d_{k_period}_{d_period}'] = d_percent
            
            # Add overbought/oversold levels
            data[f'stoch_overbought_{k_period}_{d_period}'] = 80
            data[f'stoch_oversold_{k_period}_{d_period}'] = 20
            
            self.calculated = True
            self._log_calculation(len(data), f"Stochastic({k_period},{d_period})")
            
        except Exception as e:
            logger.error(f"Error calculating Stochastic: {e}")
        
        return data
    
    def get_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate trading signals based on Stochastic.
        
        Args:
            data: DataFrame with Stochastic values
            
        Returns:
            Dictionary containing signal information
        """
        k_period = self.parameters.get('k_period', 14)
        d_period = self.parameters.get('d_period', 3)
        
        k_col = f'stoch_k_{k_period}'
        d_col = f'stoch_d_{k_period}_{d_period}'
        
        if k_col not in data.columns:
            return {'signal': 'no_data', 'strength': 0}
        
        latest_data = data.iloc[-1]
        prev_data = data.iloc[-2] if len(data) > 1 else None
        
        current_k = latest_data[k_col]
        current_d = latest_data[d_col]
        
        signals = {
            'indicator': 'Stochastic',
            'k_period': k_period,
            'd_period': d_period,
            'current_k': current_k,
            'current_d': current_d,
            'overbought': current_k > 80 or current_d > 80,
            'oversold': current_k < 20 or current_d < 20,
            'signal': 'neutral',
            'strength': 0
        }
        
        if prev_data is not None:
            prev_k = prev_data[k_col]
            prev_d = prev_data[d_col]
            
            # %K crossing above %D in oversold area (bullish)
            if (current_k > current_d and prev_k <= prev_d and 
                (current_k < 20 or current_d < 20)):
                signals['signal'] = 'buy'
                signals['strength'] = 0.8
                signals['signal_type'] = 'oversold_crossover'
            
            # %K crossing below %D in overbought area (bearish)
            elif (current_k < current_d and prev_k >= prev_d and 
                  (current_k > 80 or current_d > 80)):
                signals['signal'] = 'sell'
                signals['strength'] = 0.8
                signals['signal_type'] = 'overbought_crossover'
            
            # Oversold condition
            elif current_k < 20 and current_d < 20:
                signals['signal'] = 'buy'
                signals['strength'] = 0.6
                signals['signal_type'] = 'oversold'
            
            # Overbought condition
            elif current_k > 80 and current_d > 80:
                signals['signal'] = 'sell'
                signals['strength'] = 0.6
                signals['signal_type'] = 'overbought'
        
        return signals


class WilliamsRIndicator(BaseIndicator):
    """Williams %R indicator."""
    
    def __init__(self, period: int = 14):
        """
        Initialize Williams %R indicator.
        
        Args:
            period: Period for calculation
        """
        super().__init__(
            name="Williams %R",
            description="Williams %R - Momentum oscillator measuring overbought/oversold levels"
        )
        self.set_parameters({'period': period})
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Williams %R values.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with Williams %R values added
        """
        if not self.validate_data(data):
            return data
        
        period = self.parameters.get('period', 14)
        if not self._validate_period(period):
            return data
        
        try:
            # Calculate Williams %R
            highest_high = data['high'].rolling(window=period).max()
            lowest_low = data['low'].rolling(window=period).min()
            
            williams_r = -100 * ((highest_high - data['close']) / (highest_high - lowest_low))
            
            data[f'williams_r_{period}'] = williams_r
            
            # Add overbought/oversold levels
            data[f'williams_r_overbought_{period}'] = -20
            data[f'williams_r_oversold_{period}'] = -80
            
            self.calculated = True
            self._log_calculation(len(data), f"Williams %R({period})")
            
        except Exception as e:
            logger.error(f"Error calculating Williams %R: {e}")
        
        return data
    
    def get_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate trading signals based on Williams %R.
        
        Args:
            data: DataFrame with Williams %R values
            
        Returns:
            Dictionary containing signal information
        """
        period = self.parameters.get('period', 14)
        williams_col = f'williams_r_{period}'
        
        if williams_col not in data.columns:
            return {'signal': 'no_data', 'strength': 0}
        
        latest_data = data.iloc[-1]
        prev_data = data.iloc[-2] if len(data) > 1 else None
        
        current_williams = latest_data[williams_col]
        
        signals = {
            'indicator': 'Williams %R',
            'period': period,
            'current_williams_r': current_williams,
            'overbought': current_williams > -20,
            'oversold': current_williams < -80,
            'signal': 'neutral',
            'strength': 0
        }
        
        if prev_data is not None:
            prev_williams = prev_data[williams_col]
            
            # Williams %R crossing above oversold level (bullish)
            if (current_williams > -80 and prev_williams <= -80):
                signals['signal'] = 'buy'
                signals['strength'] = 0.8
                signals['signal_type'] = 'oversold_crossover'
            
            # Williams %R crossing below overbought level (bearish)
            elif (current_williams < -20 and prev_williams >= -20):
                signals['signal'] = 'sell'
                signals['strength'] = 0.8
                signals['signal_type'] = 'overbought_crossover'
            
            # Oversold condition
            elif current_williams < -80:
                signals['signal'] = 'buy'
                signals['strength'] = 0.6
                signals['signal_type'] = 'oversold'
            
            # Overbought condition
            elif current_williams > -20:
                signals['signal'] = 'sell'
                signals['strength'] = 0.6
                signals['signal_type'] = 'overbought'
        
        return signals 