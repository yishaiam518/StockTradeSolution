"""
RSI Strategy for Backtesting
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
import logging

from ..backtest_engine import Strategy

class RSIStrategy(Strategy):
    """RSI-based trading strategy"""
    
    def __init__(self, parameters: Dict[str, Any] = None):
        default_params = {
            'rsi_period': 14,
            'oversold_threshold': 30,
            'overbought_threshold': 70,
            'position_size': 0.1,  # 10% of capital
            'enable_short': False,
            'use_volume_confirmation': True
        }
        
        if parameters:
            default_params.update(parameters)
        
        super().__init__("RSI Strategy", default_params)
        
        self.rsi_period = self.parameters['rsi_period']
        self.oversold_threshold = self.parameters['oversold_threshold']
        self.overbought_threshold = self.parameters['overbought_threshold']
        self.position_size = self.parameters['position_size']
        self.enable_short = self.parameters['enable_short']
        self.use_volume_confirmation = self.parameters['use_volume_confirmation']
        
        self.logger.info(f"RSI Strategy initialized with parameters: {self.parameters}")
    
    def should_enter_long(self, data: pd.DataFrame, index: int) -> bool:
        """Check if should enter long position based on RSI oversold condition"""
        if index < self.rsi_period:
            return False
        
        try:
            # Get RSI value
            rsi = data.iloc[index].get('rsi_14', None)
            if rsi is None:
                return False
            
            # Check for oversold condition (RSI below threshold)
            oversold = rsi < self.oversold_threshold
            
            # Additional volume confirmation
            volume_confirmed = True
            if self.use_volume_confirmation:
                volume_confirmed = self._check_volume_confirmation(data, index)
            
            # Price above moving average for trend confirmation
            trend_confirmed = self._check_price_above_ma(data, index)
            
            return oversold and volume_confirmed and trend_confirmed
            
        except Exception as e:
            self.logger.error(f"Error in should_enter_long: {e}")
            return False
    
    def should_exit_long(self, data: pd.DataFrame, index: int) -> bool:
        """Check if should exit long position"""
        if index < self.rsi_period:
            return False
        
        try:
            # Get RSI value
            rsi = data.iloc[index].get('rsi_14', None)
            if rsi is None:
                return False
            
            # Check for overbought condition (RSI above threshold)
            overbought = rsi > self.overbought_threshold
            
            # Check for RSI divergence (price making new high but RSI not)
            divergence = self._check_bearish_divergence(data, index)
            
            return overbought or divergence
            
        except Exception as e:
            self.logger.error(f"Error in should_exit_long: {e}")
            return False
    
    def should_enter_short(self, data: pd.DataFrame, index: int) -> bool:
        """Check if should enter short position"""
        if not self.enable_short or index < self.rsi_period:
            return False
        
        try:
            # Get RSI value
            rsi = data.iloc[index].get('rsi_14', None)
            if rsi is None:
                return False
            
            # Check for overbought condition (RSI above threshold)
            overbought = rsi > self.overbought_threshold
            
            # Additional volume confirmation
            volume_confirmed = True
            if self.use_volume_confirmation:
                volume_confirmed = self._check_volume_confirmation(data, index)
            
            # Price below moving average for trend confirmation
            trend_confirmed = self._check_price_below_ma(data, index)
            
            return overbought and volume_confirmed and trend_confirmed
            
        except Exception as e:
            self.logger.error(f"Error in should_enter_short: {e}")
            return False
    
    def should_exit_short(self, data: pd.DataFrame, index: int) -> bool:
        """Check if should exit short position"""
        if not self.enable_short or index < self.rsi_period:
            return False
        
        try:
            # Get RSI value
            rsi = data.iloc[index].get('rsi_14', None)
            if rsi is None:
                return False
            
            # Check for oversold condition (RSI below threshold)
            oversold = rsi < self.oversold_threshold
            
            # Check for RSI divergence (price making new low but RSI not)
            divergence = self._check_bullish_divergence(data, index)
            
            return oversold or divergence
            
        except Exception as e:
            self.logger.error(f"Error in should_exit_short: {e}")
            return False
    
    def get_position_size(self, data: pd.DataFrame, index: int, capital: float) -> float:
        """Calculate position size based on RSI extremes"""
        try:
            rsi = data.iloc[index].get('rsi_14', 50)
            current_price = data.iloc[index].get('close', 100)
            
            # Adjust position size based on RSI extremes
            # More extreme RSI = larger position (stronger signal)
            if rsi < 20 or rsi > 80:
                size_multiplier = 1.5
            elif rsi < 25 or rsi > 75:
                size_multiplier = 1.2
            else:
                size_multiplier = 1.0
            
            return capital * self.position_size * size_multiplier
            
        except Exception as e:
            self.logger.error(f"Error in get_position_size: {e}")
            return capital * self.position_size
    
    def _check_volume_confirmation(self, data: pd.DataFrame, index: int) -> bool:
        """Check if volume confirms the signal"""
        try:
            current_volume = data.iloc[index].get('volume', 0)
            avg_volume = data.iloc[index-10:index]['volume'].mean() if index >= 10 else current_volume
            
            return current_volume > avg_volume * 1.2  # 20% above average
            
        except:
            return True
    
    def _check_price_above_ma(self, data: pd.DataFrame, index: int) -> bool:
        """Check if price is above moving average"""
        try:
            current_price = data.iloc[index].get('close', 0)
            ma = data.iloc[index].get('sma_20', 0)
            return current_price > ma if ma else True
        except:
            return True
    
    def _check_price_below_ma(self, data: pd.DataFrame, index: int) -> bool:
        """Check if price is below moving average"""
        try:
            current_price = data.iloc[index].get('close', 0)
            ma = data.iloc[index].get('sma_20', 0)
            return current_price < ma if ma else True
        except:
            return True
    
    def _check_bearish_divergence(self, data: pd.DataFrame, index: int) -> bool:
        """Check for bearish RSI divergence"""
        try:
            if index < 20:
                return False
            
            # Look for price making new high but RSI not
            price_window = data.iloc[index-20:index+1]['close']
            rsi_window = data.iloc[index-20:index+1]['rsi_14']
            
            if price_window.isna().any() or rsi_window.isna().any():
                return False
            
            price_high = price_window.max()
            rsi_high = rsi_window.max()
            
            current_price = data.iloc[index]['close']
            current_rsi = data.iloc[index]['rsi_14']
            
            # Price at new high but RSI not
            return (current_price >= price_high * 0.99 and 
                   current_rsi < rsi_high * 0.95)
            
        except:
            return False
    
    def _check_bullish_divergence(self, data: pd.DataFrame, index: int) -> bool:
        """Check for bullish RSI divergence"""
        try:
            if index < 20:
                return False
            
            # Look for price making new low but RSI not
            price_window = data.iloc[index-20:index+1]['close']
            rsi_window = data.iloc[index-20:index+1]['rsi_14']
            
            if price_window.isna().any() or rsi_window.isna().any():
                return False
            
            price_low = price_window.min()
            rsi_low = rsi_window.min()
            
            current_price = data.iloc[index]['close']
            current_rsi = data.iloc[index]['rsi_14']
            
            # Price at new low but RSI not
            return (current_price <= price_low * 1.01 and 
                   current_rsi > rsi_low * 1.05)
            
        except:
            return False 