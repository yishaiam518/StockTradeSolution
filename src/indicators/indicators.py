"""
Technical indicators implementation for the SMART STOCK TRADING SYSTEM.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple
from src.utils.config_loader import config
from src.utils.logger import logger


class TechnicalIndicators:
    """Technical indicators calculator."""
    
    def __init__(self):
        self.config = config.get_indicators_config()
        self.macd_config = self.config.get('macd', {})
        self.rsi_config = self.config.get('rsi', {})
        self.ema_config = self.config.get('ema', {})
        self.bb_config = self.config.get('bollinger_bands', {})
        self.volume_ma_config = self.config.get('volume_ma', {})
    
    def calculate_all_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all technical indicators for the given data.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with original data plus all indicators
        """
        if data.empty:
            logger.warning("Empty data provided for indicator calculation")
            return data
        
        # Make a copy to avoid modifying original data
        df = data.copy()
        
        # Calculate each indicator
        df = self.calculate_macd(df)
        df = self.calculate_rsi(df)
        df = self.calculate_ema(df)
        df = self.calculate_bollinger_bands(df)
        df = self.calculate_volume_ma(df)
        # Temporarily disable new indicators for testing
        # df = self.calculate_atr(df)
        # df = self.calculate_adx(df)
        
        # Only remove rows with NaN values if we have enough data
        # For short datasets, keep rows even with some NaN values
        if len(df) > 50:
            df = df.dropna()
        else:
            # For short datasets, only remove rows that are completely NaN
            df = df.dropna(how='all')
        
        logger.info(f"Calculated indicators for {len(df)} data points")
        return df
    
    def calculate_macd(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate MACD (Moving Average Convergence Divergence).
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with MACD columns added
        """
        try:
            fast_period = self.macd_config.get('fast_period', 12)
            slow_period = self.macd_config.get('slow_period', 26)
            signal_period = self.macd_config.get('signal_period', 9)
            
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
            data['macd_line'] = macd_line
            data['macd_signal'] = signal_line
            data['macd_histogram'] = histogram
            
            # Calculate crossover signals
            data['macd_crossover_up'] = (macd_line > signal_line) & (macd_line.shift(1) <= signal_line.shift(1))
            data['macd_crossover_down'] = (macd_line < signal_line) & (macd_line.shift(1) >= signal_line.shift(1))
            
            logger.debug(f"MACD calculated with periods: {fast_period}, {slow_period}, {signal_period}")
            
        except Exception as e:
            logger.error(f"Error calculating MACD: {str(e)}")
        
        return data
    
    def calculate_rsi(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate RSI (Relative Strength Index).
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with RSI column added
        """
        try:
            period = self.rsi_config.get('period', 14)
            overbought = self.rsi_config.get('overbought', 70)
            oversold = self.rsi_config.get('oversold', 30)
            
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
            
            # Add to dataframe
            data['rsi'] = rsi
            
            # Add overbought/oversold signals
            data['rsi_overbought'] = rsi > overbought
            data['rsi_oversold'] = rsi < oversold
            data['rsi_neutral'] = (rsi >= oversold) & (rsi <= overbought)
            
            logger.debug(f"RSI calculated with period: {period}")
            
        except Exception as e:
            logger.error(f"Error calculating RSI: {str(e)}")
        
        return data
    
    def calculate_ema(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Exponential Moving Averages.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with EMA columns added
        """
        try:
            short_period = self.ema_config.get('short_period', 20)
            long_period = self.ema_config.get('long_period', 50)
            
            # Calculate EMAs
            ema_short = data['close'].ewm(span=short_period).mean()
            ema_long = data['close'].ewm(span=long_period).mean()
            
            # Add to dataframe
            data['ema_short'] = ema_short
            data['ema_long'] = ema_long
            
            # Calculate EMA signals
            data['price_above_ema_short'] = data['close'] > ema_short
            data['price_above_ema_long'] = data['close'] > ema_long
            data['ema_bullish'] = ema_short > ema_long
            data['ema_bearish'] = ema_short < ema_long
            
            logger.debug(f"EMA calculated with periods: {short_period}, {long_period}")
            
        except Exception as e:
            logger.error(f"Error calculating EMA: {str(e)}")
        
        return data
    
    def calculate_bollinger_bands(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Bollinger Bands.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with Bollinger Bands columns added
        """
        try:
            period = self.bb_config.get('period', 20)
            std_dev = self.bb_config.get('std_dev', 2)
            
            # Calculate SMA
            sma = data['close'].rolling(window=period).mean()
            
            # Calculate standard deviation
            std = data['close'].rolling(window=period).std()
            
            # Calculate bands
            upper_band = sma + (std * std_dev)
            lower_band = sma - (std * std_dev)
            
            # Add to dataframe
            data['bb_upper'] = upper_band
            data['bb_middle'] = sma
            data['bb_lower'] = lower_band
            
            # Calculate BB signals
            data['bb_squeeze'] = (upper_band - lower_band) / sma < 0.1  # 10% bandwidth
            data['price_above_bb_upper'] = data['close'] > upper_band
            data['price_below_bb_lower'] = data['close'] < lower_band
            data['price_in_bb'] = (data['close'] >= lower_band) & (data['close'] <= upper_band)
            
            logger.debug(f"Bollinger Bands calculated with period: {period}, std_dev: {std_dev}")
            
        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands: {str(e)}")
        
        return data
    
    def calculate_volume_ma(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Volume Moving Average.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with Volume MA column added
        """
        try:
            period = self.volume_ma_config.get('period', 20)
            
            # Calculate volume moving average
            volume_ma = data['volume'].rolling(window=period).mean()
            
            # Add to dataframe
            data['volume_ma'] = volume_ma
            
            # Calculate volume signals
            data['volume_above_ma'] = data['volume'] > volume_ma
            data['volume_below_ma'] = data['volume'] < volume_ma
            data['volume_spike'] = data['volume'] > (volume_ma * 1.5)  # 50% above MA
            
            logger.debug(f"Volume MA calculated with period: {period}")
            
        except Exception as e:
            logger.error(f"Error calculating Volume MA: {str(e)}")
        
        return data
    
    def calculate_atr(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Average True Range (ATR).
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with ATR column added
        """
        try:
            period = 14  # Standard ATR period
            
            # Calculate True Range
            high_low = data['high'] - data['low']
            high_close_prev = abs(data['high'] - data['close'].shift(1))
            low_close_prev = abs(data['low'] - data['close'].shift(1))
            
            true_range = pd.concat([high_low, high_close_prev, low_close_prev], axis=1).max(axis=1)
            
            # Calculate ATR
            atr = true_range.rolling(window=period).mean()
            
            # Add to dataframe
            data['atr'] = atr
            data['atr_percent'] = (atr / data['close']) * 100  # ATR as percentage of price
            
            # Volatility signals
            data['high_volatility'] = data['atr_percent'] > 3.0  # High volatility > 3%
            data['low_volatility'] = data['atr_percent'] < 1.0   # Low volatility < 1%
            data['normal_volatility'] = (data['atr_percent'] >= 1.0) & (data['atr_percent'] <= 3.0)
            
            logger.debug(f"ATR calculated with period: {period}")
            
        except Exception as e:
            logger.error(f"Error calculating ATR: {str(e)}")
        
        return data
    
    def calculate_adx(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Average Directional Index (ADX).
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with ADX columns added
        """
        try:
            period = 14  # Standard ADX period
            
            # Calculate +DM and -DM
            high_diff = data['high'] - data['high'].shift(1)
            low_diff = data['low'].shift(1) - data['low']
            
            plus_dm = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0)
            minus_dm = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0)
            
            # Calculate True Range (reuse from ATR)
            high_low = data['high'] - data['low']
            high_close_prev = abs(data['high'] - data['close'].shift(1))
            low_close_prev = abs(data['low'] - data['close'].shift(1))
            true_range = pd.concat([high_low, high_close_prev, low_close_prev], axis=1).max(axis=1)
            
            # Smooth the values
            tr_smooth = true_range.rolling(window=period).mean()
            plus_di_smooth = pd.Series(plus_dm).rolling(window=period).mean()
            minus_di_smooth = pd.Series(minus_dm).rolling(window=period).mean()
            
            # Calculate +DI and -DI
            plus_di = (plus_di_smooth / tr_smooth) * 100
            minus_di = (minus_di_smooth / tr_smooth) * 100
            
            # Calculate DX
            dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100
            
            # Calculate ADX
            adx = dx.rolling(window=period).mean()
            
            # Add to dataframe
            data['adx'] = adx
            data['plus_di'] = plus_di
            data['minus_di'] = minus_di
            
            # Trend strength signals
            data['strong_trend'] = adx > 25  # Strong trend > 25
            data['weak_trend'] = adx < 20    # Weak trend < 20
            data['trend_changing'] = (adx >= 20) & (adx <= 25)  # Trend changing zone
            
            logger.debug(f"ADX calculated with period: {period}")
            
        except Exception as e:
            logger.error(f"Error calculating ADX: {str(e)}")
        
        return data
    
    def get_indicator_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Get current indicator signals for the latest data point.
        
        Args:
            data: DataFrame with calculated indicators
            
        Returns:
            Dictionary with current signals
        """
        if data.empty:
            return {}
        
        latest = data.iloc[-1]
        
        signals = {
            'macd_bullish': latest.get('macd_crossover_up', False),
            'macd_bearish': latest.get('macd_crossover_down', False),
            'rsi_overbought': latest.get('rsi_overbought', False),
            'rsi_oversold': latest.get('rsi_oversold', False),
            'rsi_neutral': latest.get('rsi_neutral', False),
            'price_above_ema_short': latest.get('price_above_ema_short', False),
            'price_above_ema_long': latest.get('price_above_ema_long', False),
            'ema_bullish': latest.get('ema_bullish', False),
            'bb_squeeze': latest.get('bb_squeeze', False),
            'price_above_bb_upper': latest.get('price_above_bb_upper', False),
            'price_below_bb_lower': latest.get('price_below_bb_lower', False),
            'volume_above_ma': latest.get('volume_above_ma', False),
            'volume_spike': latest.get('volume_spike', False),
            'rsi_value': latest.get('rsi', 50),
            'macd_value': latest.get('macd_line', 0),
            'macd_signal': latest.get('macd_signal', 0),
            'close_price': latest.get('close', 0),
            'ema_short': latest.get('ema_short', 0),
            'ema_long': latest.get('ema_long', 0)
        }
        
        return signals
    
    def validate_indicators(self, data: pd.DataFrame) -> bool:
        """
        Validate that all required indicators are present.
        
        Args:
            data: DataFrame with indicators
            
        Returns:
            True if all indicators are present, False otherwise
        """
        required_indicators = [
            'macd_line', 'macd_signal', 'macd_histogram',
            'rsi', 'ema_short', 'ema_long',
            'bb_upper', 'bb_middle', 'bb_lower',
            'volume_ma'
        ]
        
        missing_indicators = [ind for ind in required_indicators if ind not in data.columns]
        
        if missing_indicators:
            logger.warning(f"Missing indicators: {missing_indicators}")
            return False
        
        return True 