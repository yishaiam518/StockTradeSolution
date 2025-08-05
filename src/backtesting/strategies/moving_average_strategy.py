"""
Moving Average Strategy for Backtesting
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
import logging

from ..backtest_engine import Strategy

class MovingAverageStrategy(Strategy):
    """Moving Average crossover-based trading strategy"""
    
    def __init__(self, parameters: Dict[str, Any] = None):
        default_params = {
            'fast_ma_period': 10,
            'slow_ma_period': 20,
            'position_size': 0.1,  # 10% of capital
            'enable_short': True,
            'use_volume_confirmation': True,
            'use_rsi_filter': True
        }
        
        if parameters:
            default_params.update(parameters)
        
        super().__init__("Moving Average Strategy", default_params)
        
        self.fast_ma_period = self.parameters['fast_ma_period']
        self.slow_ma_period = self.parameters['slow_ma_period']
        self.position_size = self.parameters['position_size']
        self.enable_short = self.parameters['enable_short']
        self.use_volume_confirmation = self.parameters['use_volume_confirmation']
        self.use_rsi_filter = self.parameters['use_rsi_filter']
        
        self.logger.info(f"Moving Average Strategy initialized with parameters: {self.parameters}")
    
    def should_enter_long(self, data: pd.DataFrame, index: int) -> bool:
        """Check if should enter long position based on MA crossover"""
        if index < self.slow_ma_period:
            return False
        
        try:
            # Get moving average values
            fast_ma = data.iloc[index].get(f'sma_{self.fast_ma_period}', None)
            slow_ma = data.iloc[index].get(f'sma_{self.slow_ma_period}', None)
            prev_fast_ma = data.iloc[index-1].get(f'sma_{self.fast_ma_period}', None)
            prev_slow_ma = data.iloc[index-1].get(f'sma_{self.slow_ma_period}', None)
            
            if (fast_ma is None or slow_ma is None or 
                prev_fast_ma is None or prev_slow_ma is None):
                return False
            
            # Check for bullish crossover (fast MA crosses above slow MA)
            bullish_crossover = (prev_fast_ma <= prev_slow_ma and fast_ma > slow_ma)
            
            # Check if price is above both MAs (trend confirmation)
            current_price = data.iloc[index].get('close', 0)
            price_above_mas = current_price > fast_ma and current_price > slow_ma
            
            # RSI filter (not overbought)
            rsi_filter = True
            if self.use_rsi_filter:
                rsi = data.iloc[index].get('rsi_14', 50)
                rsi_filter = rsi < 70
            
            # Volume confirmation
            volume_confirmed = True
            if self.use_volume_confirmation:
                volume_confirmed = self._check_volume_confirmation(data, index)
            
            return bullish_crossover and price_above_mas and rsi_filter and volume_confirmed
            
        except Exception as e:
            self.logger.error(f"Error in should_enter_long: {e}")
            return False
    
    def should_exit_long(self, data: pd.DataFrame, index: int) -> bool:
        """Check if should exit long position"""
        if index < self.slow_ma_period:
            return False
        
        try:
            # Get moving average values
            fast_ma = data.iloc[index].get(f'sma_{self.fast_ma_period}', None)
            slow_ma = data.iloc[index].get(f'sma_{self.slow_ma_period}', None)
            prev_fast_ma = data.iloc[index-1].get(f'sma_{self.fast_ma_period}', None)
            prev_slow_ma = data.iloc[index-1].get(f'sma_{self.slow_ma_period}', None)
            
            if (fast_ma is None or slow_ma is None or 
                prev_fast_ma is None or prev_slow_ma is None):
                return False
            
            # Check for bearish crossover (fast MA crosses below slow MA)
            bearish_crossover = (prev_fast_ma >= prev_slow_ma and fast_ma < slow_ma)
            
            # Check if price is below both MAs (trend reversal)
            current_price = data.iloc[index].get('close', 0)
            price_below_mas = current_price < fast_ma and current_price < slow_ma
            
            # RSI overbought condition
            rsi_overbought = False
            if self.use_rsi_filter:
                rsi = data.iloc[index].get('rsi_14', 50)
                rsi_overbought = rsi > 70
            
            return bearish_crossover or price_below_mas or rsi_overbought
            
        except Exception as e:
            self.logger.error(f"Error in should_exit_long: {e}")
            return False
    
    def should_enter_short(self, data: pd.DataFrame, index: int) -> bool:
        """Check if should enter short position based on MA crossover"""
        if not self.enable_short or index < self.slow_ma_period:
            return False
        
        try:
            # Get moving average values
            fast_ma = data.iloc[index].get(f'sma_{self.fast_ma_period}', None)
            slow_ma = data.iloc[index].get(f'sma_{self.slow_ma_period}', None)
            prev_fast_ma = data.iloc[index-1].get(f'sma_{self.fast_ma_period}', None)
            prev_slow_ma = data.iloc[index-1].get(f'sma_{self.slow_ma_period}', None)
            
            if (fast_ma is None or slow_ma is None or 
                prev_fast_ma is None or prev_slow_ma is None):
                return False
            
            # Check for bearish crossover (fast MA crosses below slow MA)
            bearish_crossover = (prev_fast_ma >= prev_slow_ma and fast_ma < slow_ma)
            
            # Check if price is below both MAs (trend confirmation)
            current_price = data.iloc[index].get('close', 0)
            price_below_mas = current_price < fast_ma and current_price < slow_ma
            
            # RSI filter (not oversold)
            rsi_filter = True
            if self.use_rsi_filter:
                rsi = data.iloc[index].get('rsi_14', 50)
                rsi_filter = rsi > 30
            
            # Volume confirmation
            volume_confirmed = True
            if self.use_volume_confirmation:
                volume_confirmed = self._check_volume_confirmation(data, index)
            
            return bearish_crossover and price_below_mas and rsi_filter and volume_confirmed
            
        except Exception as e:
            self.logger.error(f"Error in should_enter_short: {e}")
            return False
    
    def should_exit_short(self, data: pd.DataFrame, index: int) -> bool:
        """Check if should exit short position"""
        if not self.enable_short or index < self.slow_ma_period:
            return False
        
        try:
            # Get moving average values
            fast_ma = data.iloc[index].get(f'sma_{self.fast_ma_period}', None)
            slow_ma = data.iloc[index].get(f'sma_{self.slow_ma_period}', None)
            prev_fast_ma = data.iloc[index-1].get(f'sma_{self.fast_ma_period}', None)
            prev_slow_ma = data.iloc[index-1].get(f'sma_{self.slow_ma_period}', None)
            
            if (fast_ma is None or slow_ma is None or 
                prev_fast_ma is None or prev_slow_ma is None):
                return False
            
            # Check for bullish crossover (fast MA crosses above slow MA)
            bullish_crossover = (prev_fast_ma <= prev_slow_ma and fast_ma > slow_ma)
            
            # Check if price is above both MAs (trend reversal)
            current_price = data.iloc[index].get('close', 0)
            price_above_mas = current_price > fast_ma and current_price > slow_ma
            
            # RSI oversold condition
            rsi_oversold = False
            if self.use_rsi_filter:
                rsi = data.iloc[index].get('rsi_14', 50)
                rsi_oversold = rsi < 30
            
            return bullish_crossover or price_above_mas or rsi_oversold
            
        except Exception as e:
            self.logger.error(f"Error in should_exit_short: {e}")
            return False
    
    def get_position_size(self, data: pd.DataFrame, index: int, capital: float) -> float:
        """Calculate position size based on MA trend strength"""
        try:
            fast_ma = data.iloc[index].get(f'sma_{self.fast_ma_period}', None)
            slow_ma = data.iloc[index].get(f'sma_{self.slow_ma_period}', None)
            current_price = data.iloc[index].get('close', 100)
            
            if fast_ma and slow_ma:
                # Calculate trend strength as percentage difference
                ma_diff = abs(fast_ma - slow_ma) / current_price
                
                # Adjust position size based on trend strength
                # Stronger trend = larger position
                if ma_diff > 0.05:  # Strong trend
                    size_multiplier = 1.3
                elif ma_diff > 0.02:  # Moderate trend
                    size_multiplier = 1.1
                else:  # Weak trend
                    size_multiplier = 0.8
                
                return capital * self.position_size * size_multiplier
            
            return capital * self.position_size
            
        except Exception as e:
            self.logger.error(f"Error in get_position_size: {e}")
            return capital * self.position_size
    
    def _check_volume_confirmation(self, data: pd.DataFrame, index: int) -> bool:
        """Check if volume confirms the signal"""
        try:
            current_volume = data.iloc[index].get('volume', 0)
            avg_volume = data.iloc[index-10:index]['volume'].mean() if index >= 10 else current_volume
            
            return current_volume > avg_volume * 1.15  # 15% above average
            
        except:
            return True
    
    def _check_ma_alignment(self, data: pd.DataFrame, index: int) -> bool:
        """Check if moving averages are properly aligned"""
        try:
            fast_ma = data.iloc[index].get(f'sma_{self.fast_ma_period}', None)
            slow_ma = data.iloc[index].get(f'sma_{self.slow_ma_period}', None)
            
            if fast_ma and slow_ma:
                # Check if fast MA is above slow MA (bullish alignment)
                return fast_ma > slow_ma
            
            return False
            
        except:
            return False 