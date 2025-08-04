"""
MACD Strategy for Backtesting
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
import logging

from ..backtest_engine import Strategy

class MACDStrategy(Strategy):
    """MACD-based trading strategy"""
    
    def __init__(self, parameters: Dict[str, Any] = None):
        default_params = {
            'fast_period': 12,
            'slow_period': 26,
            'signal_period': 9,
            'position_size': 0.1,  # 10% of capital
            'enable_short': False
        }
        
        if parameters:
            default_params.update(parameters)
        
        super().__init__("MACD Strategy", default_params)
        
        self.fast_period = self.parameters['fast_period']
        self.slow_period = self.parameters['slow_period']
        self.signal_period = self.parameters['signal_period']
        self.position_size = self.parameters['position_size']
        self.enable_short = self.parameters['enable_short']
        
        self.logger.info(f"MACD Strategy initialized with parameters: {self.parameters}")
    
    def should_enter_long(self, data: pd.DataFrame, index: int) -> bool:
        """Check if should enter long position based on MACD crossover"""
        if index < self.slow_period:
            return False
        
        try:
            # Get MACD values
            macd_line = data.iloc[index].get('macd_line_12_26', None)
            macd_signal = data.iloc[index].get('macd_signal_12_26_9', None)
            prev_macd_line = data.iloc[index-1].get('macd_line_12_26', None)
            prev_macd_signal = data.iloc[index-1].get('macd_signal_12_26_9', None)
            
            if (macd_line is None or macd_signal is None or 
                prev_macd_line is None or prev_macd_signal is None):
                return False
            
            # Check for bullish crossover (MACD line crosses above signal line)
            bullish_crossover = (prev_macd_line <= prev_macd_signal and 
                               macd_line > macd_signal)
            
            # Additional conditions
            price_above_ema = self._check_price_above_ema(data, index)
            rsi_not_overbought = self._check_rsi_not_overbought(data, index)
            
            return bullish_crossover and price_above_ema and rsi_not_overbought
            
        except Exception as e:
            self.logger.error(f"Error in should_enter_long: {e}")
            return False
    
    def should_exit_long(self, data: pd.DataFrame, index: int) -> bool:
        """Check if should exit long position"""
        if index < self.slow_period:
            return False
        
        try:
            # Get MACD values
            macd_line = data.iloc[index].get('macd_line_12_26', None)
            macd_signal = data.iloc[index].get('macd_signal_12_26_9', None)
            prev_macd_line = data.iloc[index-1].get('macd_line_12_26', None)
            prev_macd_signal = data.iloc[index-1].get('macd_signal_12_26_9', None)
            
            if (macd_line is None or macd_signal is None or 
                prev_macd_line is None or prev_macd_signal is None):
                return False
            
            # Check for bearish crossover (MACD line crosses below signal line)
            bearish_crossover = (prev_macd_line >= prev_macd_signal and 
                               macd_line < macd_signal)
            
            # Additional conditions
            rsi_overbought = self._check_rsi_overbought(data, index)
            
            return bearish_crossover or rsi_overbought
            
        except Exception as e:
            self.logger.error(f"Error in should_exit_long: {e}")
            return False
    
    def should_enter_short(self, data: pd.DataFrame, index: int) -> bool:
        """Check if should enter short position"""
        if not self.enable_short or index < self.slow_period:
            return False
        
        try:
            # Get MACD values
            macd_line = data.iloc[index].get('macd_line_12_26', None)
            macd_signal = data.iloc[index].get('macd_signal_12_26_9', None)
            prev_macd_line = data.iloc[index-1].get('macd_line_12_26', None)
            prev_macd_signal = data.iloc[index-1].get('macd_signal_12_26_9', None)
            
            if (macd_line is None or macd_signal is None or 
                prev_macd_line is None or prev_macd_signal is None):
                return False
            
            # Check for bearish crossover (MACD line crosses below signal line)
            bearish_crossover = (prev_macd_line >= prev_macd_signal and 
                               macd_line < macd_signal)
            
            # Additional conditions
            price_below_ema = self._check_price_below_ema(data, index)
            rsi_not_oversold = self._check_rsi_not_oversold(data, index)
            
            return bearish_crossover and price_below_ema and rsi_not_oversold
            
        except Exception as e:
            self.logger.error(f"Error in should_enter_short: {e}")
            return False
    
    def should_exit_short(self, data: pd.DataFrame, index: int) -> bool:
        """Check if should exit short position"""
        if not self.enable_short or index < self.slow_period:
            return False
        
        try:
            # Get MACD values
            macd_line = data.iloc[index].get('macd_line_12_26', None)
            macd_signal = data.iloc[index].get('macd_signal_12_26_9', None)
            prev_macd_line = data.iloc[index-1].get('macd_line_12_26', None)
            prev_macd_signal = data.iloc[index-1].get('macd_signal_12_26_9', None)
            
            if (macd_line is None or macd_signal is None or 
                prev_macd_line is None or prev_macd_signal is None):
                return False
            
            # Check for bullish crossover (MACD line crosses above signal line)
            bullish_crossover = (prev_macd_line <= prev_macd_signal and 
                               macd_line > macd_signal)
            
            # Additional conditions
            rsi_oversold = self._check_rsi_oversold(data, index)
            
            return bullish_crossover or rsi_oversold
            
        except Exception as e:
            self.logger.error(f"Error in should_exit_short: {e}")
            return False
    
    def get_position_size(self, data: pd.DataFrame, index: int, capital: float) -> float:
        """Calculate position size based on volatility"""
        try:
            # Get ATR for volatility-based position sizing
            atr = data.iloc[index].get('atr_14', None)
            current_price = data.iloc[index].get('close', 100)
            
            if atr and current_price:
                # Use ATR to adjust position size (higher volatility = smaller position)
                volatility_factor = 1.0 / (atr / current_price) if atr > 0 else 1.0
                volatility_factor = max(0.5, min(2.0, volatility_factor))  # Clamp between 0.5 and 2.0
                return capital * self.position_size * volatility_factor
            
            return capital * self.position_size
            
        except Exception as e:
            self.logger.error(f"Error in get_position_size: {e}")
            return capital * self.position_size
    
    def _check_price_above_ema(self, data: pd.DataFrame, index: int) -> bool:
        """Check if price is above EMA"""
        try:
            current_price = data.iloc[index].get('close', 0)
            ema = data.iloc[index].get('ema_20', 0)
            return current_price > ema if ema else True
        except:
            return True
    
    def _check_price_below_ema(self, data: pd.DataFrame, index: int) -> bool:
        """Check if price is below EMA"""
        try:
            current_price = data.iloc[index].get('close', 0)
            ema = data.iloc[index].get('ema_20', 0)
            return current_price < ema if ema else True
        except:
            return True
    
    def _check_rsi_not_overbought(self, data: pd.DataFrame, index: int) -> bool:
        """Check if RSI is not overbought"""
        try:
            rsi = data.iloc[index].get('rsi_14', 50)
            return rsi < 70
        except:
            return True
    
    def _check_rsi_overbought(self, data: pd.DataFrame, index: int) -> bool:
        """Check if RSI is overbought"""
        try:
            rsi = data.iloc[index].get('rsi_14', 50)
            return rsi > 70
        except:
            return False
    
    def _check_rsi_not_oversold(self, data: pd.DataFrame, index: int) -> bool:
        """Check if RSI is not oversold"""
        try:
            rsi = data.iloc[index].get('rsi_14', 50)
            return rsi > 30
        except:
            return True
    
    def _check_rsi_oversold(self, data: pd.DataFrame, index: int) -> bool:
        """Check if RSI is oversold"""
        try:
            rsi = data.iloc[index].get('rsi_14', 50)
            return rsi < 30
        except:
            return False 