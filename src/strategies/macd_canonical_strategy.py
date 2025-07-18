"""
Canonical MACD Strategy implementation for the SMART STOCK TRADING SYSTEM.
This is a pure MACD crossover strategy without additional filters.
"""

import pandas as pd
from typing import Dict, Any, Tuple
from .base_strategy import BaseStrategy
from src.utils.logger import logger


class MACDCanonicalStrategy(BaseStrategy):
    """Pure MACD crossover strategy without additional filters."""
    
    def __init__(self, config_dict=None):
        super().__init__(name="MACDCanonicalStrategy")
        
        # Apply configuration if provided
        if config_dict:
            if 'entry_conditions' in config_dict:
                self.entry_conditions = config_dict['entry_conditions']
            if 'exit_conditions' in config_dict:
                self.exit_conditions = config_dict['exit_conditions']
            if 'position_sizing' in config_dict:
                self.position_sizing = config_dict['position_sizing']
            if 'name' in config_dict:
                self.name = config_dict['name']
        
        # Strategy-specific parameters
        self.take_profit_pct = self.exit_conditions.get('take_profit_pct', 5.0)
        self.stop_loss_pct = self.exit_conditions.get('stop_loss_pct', 3.0)
        
        logger.info(f"Initialized Canonical MACD Strategy")
    
    def should_entry(self, data: pd.DataFrame, current_index: int) -> Tuple[bool, Dict[str, Any]]:
        """
        Entry signal: MACD line crosses above signal line (canonical MACD entry)
        """
        try:
            current_row = data.iloc[current_index]
            macd_crossover_up = bool(current_row.get('macd_crossover_up', False))
            reason = {
                'summary': 'Canonical MACD Strategy Entry',
                'macd_crossover_up': macd_crossover_up,
                'close_price': current_row.get('close', 0)
            }
            return macd_crossover_up, reason
        except Exception as e:
            logger.error(f"Error in MACDCanonicalStrategy.should_entry: {str(e)}")
            return False, {'summary': f'Error: {str(e)}'}

    def should_exit(self, data: pd.DataFrame, current_index: int, entry_price: float, entry_date: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Exit signal: MACD line crosses below signal line (canonical MACD exit)
        """
        try:
            current_row = data.iloc[current_index]
            macd_crossover_down = bool(current_row.get('macd_crossover_down', False))
            reason = {
                'summary': 'Canonical MACD Strategy Exit',
                'macd_crossover_down': macd_crossover_down,
                'close_price': current_row.get('close', 0),
                'exit_type': 'macd_crossover_down'
            }
            return macd_crossover_down, reason
        except Exception as e:
            logger.error(f"Error in MACDCanonicalStrategy.should_exit: {str(e)}")
            return False, {'summary': f'Error: {str(e)}'}
    
    def get_strategy_description(self) -> str:
        """Get a description of the Canonical MACD strategy."""
        return """
        Canonical MACD Strategy:
        
        Entry Conditions:
        - MACD line crosses above signal line (MACD crossover up)
        - No current position
        
        Exit Conditions:
        - Take profit at 5% gain
        - Stop loss at 3% loss
        - MACD line crosses below signal line (MACD crossover down)
        
        Position Sizing:
        - Default: 10% of capital per trade
        - Minimum: $200 per trade
        - Maximum: 10% of capital per position
        """
    
    def get_strategy_parameters(self) -> Dict[str, Any]:
        """Get current strategy parameters."""
        return {
            'name': self.name,
            'take_profit_pct': self.take_profit_pct,
            'stop_loss_pct': self.stop_loss_pct,
            'position_sizing': self.position_sizing,
            'description': self.get_strategy_description()
        }
    
    def update_parameters(self, **kwargs) -> None:
        """Update strategy parameters."""
        if 'take_profit_pct' in kwargs:
            self.take_profit_pct = kwargs['take_profit_pct']
        if 'stop_loss_pct' in kwargs:
            self.stop_loss_pct = kwargs['stop_loss_pct']
        
        logger.info(f"Updated Canonical MACD Strategy parameters: {kwargs}")
    
    def validate_data_requirements(self, data: pd.DataFrame) -> bool:
        """
        Validate that data has all required indicators for this strategy.
        
        Args:
            data: DataFrame with indicators
            
        Returns:
            bool: True if all required indicators are present
        """
        required_indicators = ['macd_line', 'macd_signal', 'macd_crossover_up', 'macd_crossover_down']
        
        for indicator in required_indicators:
            if indicator not in data.columns:
                logger.error(f"Missing required indicator: {indicator}")
                return False
        
        return True 