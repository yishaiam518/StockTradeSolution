"""
Base Strategy class for the SMART STOCK TRADING SYSTEM.
All trading strategies should inherit from this base class.
"""

import pandas as pd
from typing import Dict, Any, Tuple, List, Optional
from abc import ABC, abstractmethod
from src.utils.logger import logger


class BaseStrategy(ABC):
    """Base class for all trading strategies."""
    
    def __init__(self, name: str = "BaseStrategy"):
        self.name = name
        
        # Default entry conditions
        self.entry_conditions = {
            'min_volume': 1000000,
            'min_price': 1.0,
            'max_price': 10000.0
        }
        
        # Default exit conditions
        self.exit_conditions = {
            'take_profit_pct': 5.0,
            'stop_loss_pct': 3.0,
            'max_hold_days': 30
        }
        
        # Default position sizing
        self.position_sizing = {
            'default_pct': 10.0,
            'min_amount': 200.0,
            'max_pct': 10.0
        }
        
        # Profile configurations
        self.profiles = {
            'conservative': {
                'take_profit_pct': 3.0,
                'stop_loss_pct': 2.0,
                'default_pct': 5.0,
                'max_pct': 5.0
            },
            'moderate': {
                'take_profit_pct': 5.0,
                'stop_loss_pct': 3.0,
                'default_pct': 10.0,
                'max_pct': 10.0
            },
            'aggressive': {
                'take_profit_pct': 8.0,
                'stop_loss_pct': 4.0,
                'default_pct': 15.0,
                'max_pct': 15.0
            }
        }
        
        logger.info(f"Initialized {self.name}")
    
    @abstractmethod
    def should_entry(self, data: pd.DataFrame, current_index: int) -> Tuple[bool, Dict[str, Any]]:
        """
        Determine if we should enter a position.
        
        Args:
            data: DataFrame with price and indicator data
            current_index: Current index in the data
            
        Returns:
            Tuple[bool, Dict]: (should_entry, reason_dict)
        """
        pass
    
    @abstractmethod
    def should_exit(self, data: pd.DataFrame, current_index: int, entry_price: float, entry_date: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Determine if we should exit a position.
        
        Args:
            data: DataFrame with price and indicator data
            current_index: Current index in the data
            entry_price: Price when position was entered
            entry_date: Date when position was entered
            
        Returns:
            Tuple[bool, Dict]: (should_exit, reason_dict)
        """
        pass
    
    def configure_profile(self, profile_name: str) -> None:
        """
        Configure strategy with a specific risk profile.
        
        Args:
            profile_name: Name of the profile ('conservative', 'moderate', 'aggressive')
        """
        if profile_name not in self.profiles:
            logger.warning(f"Profile '{profile_name}' not found, using moderate")
            profile_name = 'moderate'
        
        profile_config = self.profiles[profile_name]
        
        # Update exit conditions
        self.exit_conditions.update({
            'take_profit_pct': profile_config.get('take_profit_pct', 5.0),
            'stop_loss_pct': profile_config.get('stop_loss_pct', 3.0)
        })
        
        # Update position sizing
        self.position_sizing.update({
            'default_pct': profile_config.get('default_pct', 10.0),
            'max_pct': profile_config.get('max_pct', 10.0)
        })
        
        logger.info(f"Configured {self.name} with {profile_name} profile")
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals for the entire dataset.
        
        Args:
            data: DataFrame with price and indicator data
            
        Returns:
            DataFrame: DataFrame with signal columns added
        """
        try:
            # Validate data requirements
            if not self.validate_data_requirements(data):
                logger.error(f"Data validation failed for {self.name}")
                return pd.DataFrame()
            
            # Initialize signal columns
            signals = data.copy()
            signals['signal'] = 0  # 0: hold, 1: buy, -1: sell
            signals['strength'] = 0.0
            signals['confidence'] = 0.0
            signals['reason'] = ''
            
            # Generate signals for each data point
            for i in range(len(signals)):
                # Check for entry signal
                should_entry, entry_reason = self.should_entry(signals, i)
                
                if should_entry:
                    signals.iloc[i, signals.columns.get_loc('signal')] = 1
                    signals.iloc[i, signals.columns.get_loc('strength')] = 0.8
                    signals.iloc[i, signals.columns.get_loc('confidence')] = 0.7
                    signals.iloc[i, signals.columns.get_loc('reason')] = entry_reason.get('summary', 'Entry signal')
                
                # Check for exit signal (simplified - in real implementation would track positions)
                should_exit, exit_reason = self.should_exit(signals, i, 0, '')
                
                if should_exit:
                    signals.iloc[i, signals.columns.get_loc('signal')] = -1
                    signals.iloc[i, signals.columns.get_loc('strength')] = 0.8
                    signals.iloc[i, signals.columns.get_loc('confidence')] = 0.7
                    signals.iloc[i, signals.columns.get_loc('reason')] = exit_reason.get('summary', 'Exit signal')
            
            logger.info(f"Generated signals for {self.name}: {len(signals[signals['signal'] != 0])} signals")
            return signals
            
        except Exception as e:
            logger.error(f"Error generating signals for {self.name}: {str(e)}")
            return pd.DataFrame()
    
    def validate_data_requirements(self, data: pd.DataFrame) -> bool:
        """
        Validate that data has all required indicators for this strategy.
        
        Args:
            data: DataFrame with indicators
            
        Returns:
            bool: True if all required indicators are present
        """
        # Base strategy requires basic OHLCV data
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        
        for col in required_columns:
            if col not in data.columns:
                logger.error(f"Missing required column: {col}")
                return False
        
        return True
    
    def get_strategy_description(self) -> str:
        """Get a description of the strategy."""
        return f"Base strategy: {self.name}"
    
    def get_strategy_parameters(self) -> Dict[str, Any]:
        """Get current strategy parameters."""
        return {
            'name': self.name,
            'entry_conditions': self.entry_conditions,
            'exit_conditions': self.exit_conditions,
            'position_sizing': self.position_sizing,
            'description': self.get_strategy_description()
        }
    
    def update_parameters(self, **kwargs) -> None:
        """Update strategy parameters."""
        if 'entry_conditions' in kwargs:
            self.entry_conditions.update(kwargs['entry_conditions'])
        if 'exit_conditions' in kwargs:
            self.exit_conditions.update(kwargs['exit_conditions'])
        if 'position_sizing' in kwargs:
            self.position_sizing.update(kwargs['position_sizing'])
        
        logger.info(f"Updated {self.name} parameters: {kwargs}")
    
    def calculate_position_size(self, capital: float, price: float) -> float:
        """
        Calculate position size based on current parameters.
        
        Args:
            capital: Available capital
            price: Current price
            
        Returns:
            float: Position size in dollars
        """
        try:
            # Calculate position size based on percentage
            position_pct = self.position_sizing.get('default_pct', 10.0) / 100.0
            position_amount = capital * position_pct
            
            # Apply minimum and maximum constraints
            min_amount = self.position_sizing.get('min_amount', 200.0)
            max_pct = self.position_sizing.get('max_pct', 10.0) / 100.0
            max_amount = capital * max_pct
            
            position_amount = max(min_amount, min(position_amount, max_amount))
            
            return position_amount
            
        except Exception as e:
            logger.error(f"Error calculating position size: {str(e)}")
            return 0.0 