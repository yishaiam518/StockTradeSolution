"""
Bollinger Bands Strategy for Backtesting
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
import logging

from ..backtest_engine import Strategy

class BollingerBandsStrategy(Strategy):
    """Bollinger Bands-based trading strategy"""
    
    def __init__(self, parameters: Dict[str, Any] = None):
        default_params = {
            'bb_period': 20,
            'bb_std_dev': 2.0,
            'position_size': 0.1,  # 10% of capital
            'enable_short': True,
            'use_rsi_confirmation': True,
            'use_volume_confirmation': True
        }
        
        if parameters:
            default_params.update(parameters)
        
        super().__init__("Bollinger Bands Strategy", default_params)
        
        self.bb_period = self.parameters['bb_period']
        self.bb_std_dev = self.parameters['bb_std_dev']
        self.position_size = self.parameters['position_size']
        self.enable_short = self.parameters['enable_short']
        self.use_rsi_confirmation = self.parameters['use_rsi_confirmation']
        self.use_volume_confirmation = self.parameters['use_volume_confirmation']
        
        self.logger.info(f"Bollinger Bands Strategy initialized with parameters: {self.parameters}")
    
    def should_enter_long(self, data: pd.DataFrame, index: int) -> bool:
        """Check if should enter long position based on price touching lower band"""
        if index < self.bb_period:
            return False
        
        try:
            # Get Bollinger Bands values
            bb_lower = data.iloc[index].get(f'bb_lower_{self.bb_period}_{self.bb_std_dev}', None)
            bb_middle = data.iloc[index].get(f'bb_middle_{self.bb_period}_{self.bb_std_dev}', None)
            current_price = data.iloc[index].get('close', None)
            
            if bb_lower is None or bb_middle is None or current_price is None:
                return False
            
            # Check if price is near or below lower band
            price_near_lower = current_price <= bb_lower * 1.01
            
            # Check if price is below middle band (trend confirmation)
            price_below_middle = current_price < bb_middle
            
            # RSI confirmation (not overbought)
            rsi_confirmed = True
            if self.use_rsi_confirmation:
                rsi = data.iloc[index].get('rsi_14', 50)
                rsi_confirmed = rsi < 70
            
            # Volume confirmation
            volume_confirmed = True
            if self.use_volume_confirmation:
                volume_confirmed = self._check_volume_confirmation(data, index)
            
            return price_near_lower and price_below_middle and rsi_confirmed and volume_confirmed
            
        except Exception as e:
            self.logger.error(f"Error in should_enter_long: {e}")
            return False
    
    def should_exit_long(self, data: pd.DataFrame, index: int) -> bool:
        """Check if should exit long position"""
        if index < self.bb_period:
            return False
        
        try:
            # Get Bollinger Bands values
            bb_upper = data.iloc[index].get(f'bb_upper_{self.bb_period}_{self.bb_std_dev}', None)
            bb_middle = data.iloc[index].get(f'bb_middle_{self.bb_period}_{self.bb_std_dev}', None)
            current_price = data.iloc[index].get('close', None)
            
            if bb_upper is None or bb_middle is None or current_price is None:
                return False
            
            # Check if price is near or above upper band
            price_near_upper = current_price >= bb_upper * 0.99
            
            # Check if price is above middle band (profit taking)
            price_above_middle = current_price > bb_middle
            
            # RSI overbought condition
            rsi_overbought = False
            if self.use_rsi_confirmation:
                rsi = data.iloc[index].get('rsi_14', 50)
                rsi_overbought = rsi > 70
            
            return price_near_upper or price_above_middle or rsi_overbought
            
        except Exception as e:
            self.logger.error(f"Error in should_exit_long: {e}")
            return False
    
    def should_enter_short(self, data: pd.DataFrame, index: int) -> bool:
        """Check if should enter short position based on price touching upper band"""
        if not self.enable_short or index < self.bb_period:
            return False
        
        try:
            # Get Bollinger Bands values
            bb_upper = data.iloc[index].get(f'bb_upper_{self.bb_period}_{self.bb_std_dev}', None)
            bb_middle = data.iloc[index].get(f'bb_middle_{self.bb_period}_{self.bb_std_dev}', None)
            current_price = data.iloc[index].get('close', None)
            
            if bb_upper is None or bb_middle is None or current_price is None:
                return False
            
            # Check if price is near or above upper band
            price_near_upper = current_price >= bb_upper * 0.99
            
            # Check if price is above middle band (trend confirmation)
            price_above_middle = current_price > bb_middle
            
            # RSI confirmation (not oversold)
            rsi_confirmed = True
            if self.use_rsi_confirmation:
                rsi = data.iloc[index].get('rsi_14', 50)
                rsi_confirmed = rsi > 30
            
            # Volume confirmation
            volume_confirmed = True
            if self.use_volume_confirmation:
                volume_confirmed = self._check_volume_confirmation(data, index)
            
            return price_near_upper and price_above_middle and rsi_confirmed and volume_confirmed
            
        except Exception as e:
            self.logger.error(f"Error in should_enter_short: {e}")
            return False
    
    def should_exit_short(self, data: pd.DataFrame, index: int) -> bool:
        """Check if should exit short position"""
        if not self.enable_short or index < self.bb_period:
            return False
        
        try:
            # Get Bollinger Bands values
            bb_lower = data.iloc[index].get(f'bb_lower_{self.bb_period}_{self.bb_std_dev}', None)
            bb_middle = data.iloc[index].get(f'bb_middle_{self.bb_period}_{self.bb_std_dev}', None)
            current_price = data.iloc[index].get('close', None)
            
            if bb_lower is None or bb_middle is None or current_price is None:
                return False
            
            # Check if price is near or below lower band
            price_near_lower = current_price <= bb_lower * 1.01
            
            # Check if price is below middle band (profit taking)
            price_below_middle = current_price < bb_middle
            
            # RSI oversold condition
            rsi_oversold = False
            if self.use_rsi_confirmation:
                rsi = data.iloc[index].get('rsi_14', 50)
                rsi_oversold = rsi < 30
            
            return price_near_lower or price_below_middle or rsi_oversold
            
        except Exception as e:
            self.logger.error(f"Error in should_exit_short: {e}")
            return False
    
    def get_position_size(self, data: pd.DataFrame, index: int, capital: float) -> float:
        """Calculate position size based on Bollinger Bands width"""
        try:
            bb_upper = data.iloc[index].get(f'bb_upper_{self.bb_period}_{self.bb_std_dev}', None)
            bb_lower = data.iloc[index].get(f'bb_lower_{self.bb_period}_{self.bb_std_dev}', None)
            current_price = data.iloc[index].get('close', 100)
            
            if bb_upper and bb_lower:
                # Calculate BB width as percentage of price
                bb_width = (bb_upper - bb_lower) / current_price
                
                # Adjust position size based on volatility
                # Wider bands = smaller position (higher volatility)
                if bb_width > 0.1:  # Very wide bands
                    size_multiplier = 0.7
                elif bb_width > 0.05:  # Wide bands
                    size_multiplier = 0.9
                else:  # Normal bands
                    size_multiplier = 1.0
                
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
            
            return current_volume > avg_volume * 1.1  # 10% above average
            
        except:
            return True
    
    def _check_bb_squeeze(self, data: pd.DataFrame, index: int) -> bool:
        """Check if Bollinger Bands are in a squeeze (low volatility)"""
        try:
            bb_upper = data.iloc[index].get(f'bb_upper_{self.bb_period}_{self.bb_std_dev}', None)
            bb_lower = data.iloc[index].get(f'bb_lower_{self.bb_period}_{self.bb_std_dev}', None)
            current_price = data.iloc[index].get('close', 100)
            
            if bb_upper and bb_lower:
                bb_width = (bb_upper - bb_lower) / current_price
                return bb_width < 0.03  # Very narrow bands
            
            return False
            
        except:
            return False 