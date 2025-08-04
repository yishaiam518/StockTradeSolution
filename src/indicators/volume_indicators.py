"""
Volume indicators implementation.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from .base_indicator import BaseIndicator
from src.utils.logger import logger


class OBVIndicator(BaseIndicator):
    """On-Balance Volume (OBV) indicator."""
    
    def __init__(self):
        """
        Initialize OBV indicator.
        """
        super().__init__(
            name="OBV",
            description="On-Balance Volume - Volume-based indicator measuring buying and selling pressure"
        )
        self.set_parameters({})
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate OBV values.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with OBV values added
        """
        if not self.validate_data(data):
            return data
        
        try:
            # Calculate price changes
            price_change = data['close'].diff()
            
            # Initialize OBV
            obv = pd.Series(index=data.index, dtype=float)
            obv.iloc[0] = data['volume'].iloc[0]
            
            # Calculate OBV
            for i in range(1, len(data)):
                if price_change.iloc[i] > 0:
                    obv.iloc[i] = obv.iloc[i-1] + data['volume'].iloc[i]
                elif price_change.iloc[i] < 0:
                    obv.iloc[i] = obv.iloc[i-1] - data['volume'].iloc[i]
                else:
                    obv.iloc[i] = obv.iloc[i-1]
            
            # Add to dataframe
            data['obv'] = obv
            
            # Calculate OBV moving average for reference
            data['obv_ma_20'] = obv.rolling(window=20).mean()
            
            # Calculate OBV rate of change
            data['obv_roc'] = obv.pct_change() * 100
            
            self.calculated = True
            self._log_calculation(len(data), "OBV")
            
        except Exception as e:
            logger.error(f"Error calculating OBV: {e}")
        
        return data
    
    def get_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate trading signals based on OBV.
        
        Args:
            data: DataFrame with OBV values
            
        Returns:
            Dictionary containing signal information
        """
        if 'obv' not in data.columns:
            return {'signal': 'no_data', 'strength': 0}
        
        latest_data = data.iloc[-1]
        prev_data = data.iloc[-2] if len(data) > 1 else None
        
        current_obv = latest_data['obv']
        current_price = latest_data['close']
        current_obv_ma = latest_data['obv_ma_20']
        
        signals = {
            'indicator': 'OBV',
            'current_obv': current_obv,
            'current_price': current_price,
            'obv_above_ma': current_obv > current_obv_ma,
            'signal': 'neutral',
            'strength': 0
        }
        
        if prev_data is not None:
            prev_obv = prev_data['obv']
            prev_price = prev_data['close']
            
            # OBV divergence signals
            # Price making new high but OBV not confirming (bearish divergence)
            if (current_price > prev_price and current_obv < prev_obv):
                signals['signal'] = 'sell'
                signals['strength'] = 0.7
                signals['signal_type'] = 'bearish_divergence'
            
            # Price making new low but OBV not confirming (bullish divergence)
            elif (current_price < prev_price and current_obv > prev_obv):
                signals['signal'] = 'buy'
                signals['strength'] = 0.7
                signals['signal_type'] = 'bullish_divergence'
            
            # OBV crossing above its MA (bullish)
            elif (current_obv > current_obv_ma and prev_obv <= prev_data['obv_ma_20']):
                signals['signal'] = 'buy'
                signals['strength'] = 0.6
                signals['signal_type'] = 'obv_ma_crossover_up'
            
            # OBV crossing below its MA (bearish)
            elif (current_obv < current_obv_ma and prev_obv >= prev_data['obv_ma_20']):
                signals['signal'] = 'sell'
                signals['strength'] = 0.6
                signals['signal_type'] = 'obv_ma_crossover_down'
        
        return signals


class VWAPIndicator(BaseIndicator):
    """Volume Weighted Average Price (VWAP) indicator."""
    
    def __init__(self):
        """
        Initialize VWAP indicator.
        """
        super().__init__(
            name="VWAP",
            description="Volume Weighted Average Price - Average price weighted by volume"
        )
        self.set_parameters({})
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate VWAP values.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with VWAP values added
        """
        if not self.validate_data(data):
            return data
        
        try:
            # Calculate typical price
            typical_price = (data['high'] + data['low'] + data['close']) / 3
            
            # Calculate volume-weighted price
            vwap = (typical_price * data['volume']).cumsum() / data['volume'].cumsum()
            
            # Add to dataframe
            data['vwap'] = vwap
            
            # Calculate price position relative to VWAP
            data['price_vs_vwap'] = (data['close'] / vwap - 1) * 100
            
            # Calculate VWAP bands (1 and 2 standard deviations)
            vwap_std = (typical_price * data['volume']).rolling(window=20).std()
            data['vwap_upper_1'] = vwap + vwap_std
            data['vwap_lower_1'] = vwap - vwap_std
            data['vwap_upper_2'] = vwap + (2 * vwap_std)
            data['vwap_lower_2'] = vwap - (2 * vwap_std)
            
            self.calculated = True
            self._log_calculation(len(data), "VWAP")
            
        except Exception as e:
            logger.error(f"Error calculating VWAP: {e}")
        
        return data
    
    def get_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate trading signals based on VWAP.
        
        Args:
            data: DataFrame with VWAP values
            
        Returns:
            Dictionary containing signal information
        """
        if 'vwap' not in data.columns:
            return {'signal': 'no_data', 'strength': 0}
        
        latest_data = data.iloc[-1]
        prev_data = data.iloc[-2] if len(data) > 1 else None
        
        current_price = latest_data['close']
        current_vwap = latest_data['vwap']
        current_price_vs_vwap = latest_data['price_vs_vwap']
        
        signals = {
            'indicator': 'VWAP',
            'current_price': current_price,
            'current_vwap': current_vwap,
            'price_vs_vwap_percent': current_price_vs_vwap,
            'price_above_vwap': current_price > current_vwap,
            'signal': 'neutral',
            'strength': 0
        }
        
        if prev_data is not None:
            prev_price = prev_data['close']
            prev_vwap = prev_data['vwap']
            
            # Price crossing above VWAP (bullish)
            if (current_price > current_vwap and prev_price <= prev_vwap):
                signals['signal'] = 'buy'
                signals['strength'] = 0.7
                signals['signal_type'] = 'vwap_crossover_up'
            
            # Price crossing below VWAP (bearish)
            elif (current_price < current_vwap and prev_price >= prev_vwap):
                signals['signal'] = 'sell'
                signals['strength'] = 0.7
                signals['signal_type'] = 'vwap_crossover_down'
            
            # Price significantly above VWAP (overbought)
            elif current_price_vs_vwap > 2.0:
                signals['signal'] = 'sell'
                signals['strength'] = 0.5
                signals['signal_type'] = 'overbought_vwap'
            
            # Price significantly below VWAP (oversold)
            elif current_price_vs_vwap < -2.0:
                signals['signal'] = 'buy'
                signals['strength'] = 0.5
                signals['signal_type'] = 'oversold_vwap'
        
        return signals


class MoneyFlowIndexIndicator(BaseIndicator):
    """Money Flow Index (MFI) indicator."""
    
    def __init__(self, period: int = 14):
        """
        Initialize MFI indicator.
        
        Args:
            period: Period for MFI calculation
        """
        super().__init__(
            name="MFI",
            description="Money Flow Index - Volume-weighted RSI measuring buying and selling pressure"
        )
        self.set_parameters({'period': period})
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate MFI values.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with MFI values added
        """
        if not self.validate_data(data):
            return data
        
        period = self.parameters.get('period', 14)
        if not self._validate_period(period):
            return data
        
        try:
            # Calculate typical price
            typical_price = (data['high'] + data['low'] + data['close']) / 3
            
            # Calculate raw money flow
            raw_money_flow = typical_price * data['volume']
            
            # Calculate positive and negative money flow
            price_change = typical_price.diff()
            positive_money_flow = raw_money_flow.where(price_change > 0, 0)
            negative_money_flow = raw_money_flow.where(price_change < 0, 0)
            
            # Calculate money flow ratio
            positive_mf = positive_money_flow.rolling(window=period).sum()
            negative_mf = negative_money_flow.rolling(window=period).sum()
            
            money_ratio = positive_mf / negative_mf
            
            # Calculate MFI
            mfi = 100 - (100 / (1 + money_ratio))
            
            # Add to dataframe
            data[f'mfi_{period}'] = mfi
            
            # Add overbought/oversold levels
            data[f'mfi_overbought_{period}'] = 80
            data[f'mfi_oversold_{period}'] = 20
            
            self.calculated = True
            self._log_calculation(len(data), f"MFI({period})")
            
        except Exception as e:
            logger.error(f"Error calculating MFI: {e}")
        
        return data
    
    def get_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate trading signals based on MFI.
        
        Args:
            data: DataFrame with MFI values
            
        Returns:
            Dictionary containing signal information
        """
        period = self.parameters.get('period', 14)
        mfi_col = f'mfi_{period}'
        
        if mfi_col not in data.columns:
            return {'signal': 'no_data', 'strength': 0}
        
        latest_data = data.iloc[-1]
        prev_data = data.iloc[-2] if len(data) > 1 else None
        
        current_mfi = latest_data[mfi_col]
        
        signals = {
            'indicator': 'MFI',
            'period': period,
            'current_mfi': current_mfi,
            'overbought': current_mfi > 80,
            'oversold': current_mfi < 20,
            'signal': 'neutral',
            'strength': 0
        }
        
        if prev_data is not None:
            prev_mfi = prev_data[mfi_col]
            
            # MFI crossing above oversold level (bullish)
            if (current_mfi > 20 and prev_mfi <= 20):
                signals['signal'] = 'buy'
                signals['strength'] = 0.8
                signals['signal_type'] = 'oversold_crossover'
            
            # MFI crossing below overbought level (bearish)
            elif (current_mfi < 80 and prev_mfi >= 80):
                signals['signal'] = 'sell'
                signals['strength'] = 0.8
                signals['signal_type'] = 'overbought_crossover'
            
            # MFI divergence signals
            elif current_mfi < 20:
                signals['signal'] = 'buy'
                signals['strength'] = 0.6
                signals['signal_type'] = 'oversold'
            
            elif current_mfi > 80:
                signals['signal'] = 'sell'
                signals['strength'] = 0.6
                signals['signal_type'] = 'overbought'
        
        return signals 