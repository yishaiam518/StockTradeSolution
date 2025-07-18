"""
MACD Strategy implementation for the SMART STOCK TRADING SYSTEM.

Now supports multiple profiles:
- balanced: Standard MACD Strategy with balanced parameters
- canonical: Canonical MACD Strategy with traditional parameters  
- aggressive: Aggressive MACD Strategy for high-frequency trading
- conservative: Conservative MACD Strategy for long-term positions
"""

import pandas as pd
from typing import Dict, Any, Tuple, List
from .base_strategy import BaseStrategy
from src.utils.logger import logger


class MACDStrategy(BaseStrategy):
    """MACD-based trading strategy with multiple risk profiles."""
    
    def __init__(self, config_dict=None, profile="balanced"):
        super().__init__(name="MACDStrategy")
        
        # Set the profile
        self.profile = profile
        
        # Apply configuration if provided
        if config_dict:
            # Handle profile-based configuration
            if 'profiles' in config_dict and profile in config_dict['profiles']:
                profile_config = config_dict['profiles'][profile]
                self._apply_profile_config(profile_config)
            else:
                # Legacy configuration handling
                self._apply_legacy_config(config_dict)
        else:
            # Use default profile configuration
            self._apply_default_profile_config()
        
        logger.info(f"Initialized MACD Strategy with profile: {self.profile}")
    
    def _apply_profile_config(self, profile_config: Dict[str, Any]):
        """Apply configuration from a specific profile."""
        # Entry conditions
        self.entry_conditions = {
            'weights': profile_config.get('entry_weights', {}),
            'threshold': profile_config.get('entry_threshold', 1.0)
        }
        
        # Exit conditions
        self.exit_conditions = {
            'max_drawdown_pct': profile_config.get('max_drawdown_pct', 7.0),
            'take_profit_pct': profile_config.get('take_profit_pct', 20.0),
            'stop_loss_pct': profile_config.get('stop_loss_pct', 3.0),
            'max_hold_days': profile_config.get('max_hold_days', 252)
        }
        
        # Strategy-specific parameters
        self.rsi_range = profile_config.get('rsi_range', [40, 60])
        self.take_profit_pct = self.exit_conditions.get('take_profit_pct', 5.0)
        self.stop_loss_pct = self.exit_conditions.get('stop_loss_pct', 3.0)
        
        # Log configuration
        self._log_config()
    
    def _apply_legacy_config(self, config_dict: Dict[str, Any]):
        """Apply legacy configuration format."""
        # Handle both old and new config structures
        if 'entry_conditions' in config_dict:
            self.entry_conditions = config_dict['entry_conditions']
        else:
            # New structure: config_dict contains entry_weights, entry_threshold directly
            self.entry_conditions = {
                'weights': config_dict.get('entry_weights', {}),
                'threshold': config_dict.get('entry_threshold', 1.0)
            }
        
        if 'exit_conditions' in config_dict:
            self.exit_conditions = config_dict['exit_conditions']
        else:
            # New structure: config_dict contains exit conditions directly
            self.exit_conditions = {
                'max_drawdown_pct': config_dict.get('max_drawdown_pct', 7.0),
                'take_profit_pct': config_dict.get('take_profit_pct', 20.0),
                'stop_loss_pct': config_dict.get('stop_loss_pct', 3.0),
                'max_hold_days': config_dict.get('max_hold_days', 252)
            }
        
        if 'position_sizing' in config_dict:
            self.position_sizing = config_dict['position_sizing']
        if 'name' in config_dict:
            self.name = config_dict['name']
        
        # Strategy-specific parameters
        self.rsi_range = self.entry_conditions.get('rsi_range', [40, 60])
        self.take_profit_pct = self.exit_conditions.get('take_profit_pct', 5.0)
        self.stop_loss_pct = self.exit_conditions.get('stop_loss_pct', 3.0)
        
        # Log configuration
        self._log_config()
    
    def _apply_default_profile_config(self):
        """Apply default configuration for the current profile."""
        # Default balanced profile configuration
        default_config = {
            'entry_weights': {
                'macd_crossover_up': 0.5,
                'rsi_neutral': 0.3,
                'price_above_ema_short': 0.1,
                'price_above_ema_long': 0.1
            },
            'entry_threshold': 0.3,
            'rsi_range': [40, 60],
            'max_drawdown_pct': 5.0,
            'take_profit_pct': 5.0,
            'stop_loss_pct': 3.0,
            'max_hold_days': 30
        }
        
        self._apply_profile_config(default_config)
    
    def _log_config(self):
        """Log the current configuration."""
        entry_weights = self.entry_conditions.get('weights', {})
        entry_threshold = self.entry_conditions.get('threshold', 1.0)
        
        logger.info(f"MACDStrategy profile: {self.profile}")
        logger.info(f"MACDStrategy entry weights: {entry_weights}")
        logger.info(f"MACDStrategy entry threshold: {entry_threshold}")
        logger.info(f"Initialized MACD Strategy with RSI range: {self.rsi_range}")
    
    def get_profile(self) -> str:
        """Get the current profile."""
        return self.profile
    
    def set_profile(self, profile: str, config: Dict[str, Any] = None):
        """Set a new profile and optionally update configuration."""
        self.profile = profile
        
        if config and 'profiles' in config and profile in config['profiles']:
            profile_config = config['profiles'][profile]
            self._apply_profile_config(profile_config)
        else:
            # Use default profile configuration
            self._apply_default_profile_config()
        
        logger.info(f"MACD Strategy profile changed to: {self.profile}")
    
    def should_entry(self, data: pd.DataFrame, current_index: int) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if we should enter a position based on MACD strategy with scoring system.
        """
        if self.current_position is not None:
            return False, {'summary': 'Already in position'}
        if current_index < 1:
            return False, {'summary': 'Insufficient data'}
        try:
            current_row = data.iloc[current_index]
            weights = self.entry_conditions.get('weights', {})
            threshold = self.entry_conditions.get('threshold', 1.0)
            # Individual conditions
            macd_crossover_up = current_row.get('macd_crossover_up', False)
            rsi_value = current_row.get('rsi', 50)
            rsi_neutral = self.rsi_range[0] <= rsi_value <= self.rsi_range[1]
            price_above_ema_short = current_row.get('price_above_ema_short', False)
            price_above_ema_long = current_row.get('price_above_ema_long', False)
            # Scoring
            score = 0.0
            if macd_crossover_up:
                score += weights.get('macd_crossover_up', 0)
            if rsi_neutral:
                score += weights.get('rsi_neutral', 0)
            if price_above_ema_short:
                score += weights.get('price_above_ema_short', 0)
            if price_above_ema_long:
                score += weights.get('price_above_ema_long', 0)
            reason = {
                'summary': f'MACD Strategy Entry (Scoring) - Profile: {self.profile}',
                'profile': self.profile,
                'macd_crossover_up': macd_crossover_up,
                'rsi_neutral': rsi_neutral,
                'rsi_value': rsi_value,
                'price_above_ema_short': price_above_ema_short,
                'price_above_ema_long': price_above_ema_long,
                'score': score,
                'threshold': threshold,
                'close_price': current_row.get('close', 0),
                'ema_short': current_row.get('ema_short', 0),
                'ema_long': current_row.get('ema_long', 0)
            }
            should_entry = score >= threshold
            return should_entry, reason
        except Exception as e:
            logger.error(f"Error in MACD entry logic: {str(e)}")
            return False, {'summary': f'Error: {str(e)}'}
    
    def should_exit(self, data: pd.DataFrame, current_index: int, entry_price: float, entry_date) -> Tuple[bool, Dict[str, Any]]:
        """
        Determine if we should exit the position.
        Implements drawdown protection and take profit as explicit exit signals.
        """
        if current_index < 1:
            return False, {"summary": "Not enough data"}
        
        current_row = data.iloc[current_index]
        previous_row = data.iloc[current_index - 1]
        
        # Get current price
        current_price = current_row['close']
        
        # Calculate drawdown from entry
        drawdown_from_entry = (current_price - entry_price) / entry_price
        
        # Find the highest price since entry
        if 'date' in data.columns:
            # Find the first row where the date matches entry_date
            entry_index = data.index[data['date'] == entry_date]
            if len(entry_index) > 0:
                entry_index = entry_index[0]
            else:
                entry_index = current_index
        else:
            entry_index = current_index
        price_since_entry = data.iloc[entry_index:current_index + 1]['close']
        highest_price = price_since_entry.max()
        drawdown_from_peak = (current_price - highest_price) / highest_price
        
        # Configurable thresholds
        max_drawdown = self.exit_conditions.get('max_drawdown_pct', 5.0) / 100
        take_profit_pct = self.exit_conditions.get('take_profit_pct', 10.0) / 100
        stop_loss_pct = self.exit_conditions.get('stop_loss_pct', 3.0) / 100
        max_hold_days = self.exit_conditions.get('max_hold_days', 252)
        
        # 1. Drawdown protection: sell if price drops X% from peak since entry
        if drawdown_from_peak < -max_drawdown:
            return True, {
                "summary": f"Drawdown protection: {drawdown_from_peak*100:.2f}% from peak (threshold {max_drawdown*100:.2f}%)",
                "profile": self.profile,
                "drawdown_from_peak": drawdown_from_peak*100,
                "threshold": max_drawdown*100,
                "exit_type": "drawdown_protection"
            }
        
        # 2. Take profit: sell if gain exceeds threshold
        if drawdown_from_entry > take_profit_pct:
            return True, {
                "summary": f"Take profit: {drawdown_from_entry*100:.2f}% gain (threshold {take_profit_pct*100:.2f}%)",
                "profile": self.profile,
                "gain_pct": drawdown_from_entry*100,
                "threshold": take_profit_pct*100,
                "exit_type": "take_profit"
            }
        
        # 3. Stop loss: sell if loss exceeds threshold
        if drawdown_from_entry < -stop_loss_pct:
            return True, {
                "summary": f"Stop loss: {drawdown_from_entry*100:.2f}% from entry (threshold {stop_loss_pct*100:.2f}%)",
                "profile": self.profile,
                "loss_pct": abs(drawdown_from_entry*100),
                "threshold": stop_loss_pct*100,
                "exit_type": "stop_loss"
            }
        
        # 4. MACD crossover down
        if current_row.get('macd_crossover_down', False) and previous_row.get('macd_crossover_up', False):
            return True, {
                "summary": "MACD crossover down",
                "profile": self.profile,
                "exit_type": "macd_crossover_down"
            }
        
        # 5. Price below EMA short
        if current_row.get('price_below_ema_short', False):
            return True, {
                "summary": "Price below EMA short",
                "profile": self.profile,
                "exit_type": "price_below_ema_short"
            }
        
        # 6. Time-based exit
        days_held = current_index - entry_index
        if days_held > max_hold_days:
            return True, {
                "summary": f"Time-based exit: held {days_held} days (max {max_hold_days})",
                "profile": self.profile,
                "days_held": days_held,
                "max_hold_days": max_hold_days,
                "exit_type": "time_based_exit"
            }
        
        return False, {"summary": "No exit signal", "profile": self.profile}
    
    def get_strategy_description(self) -> str:
        """Get a description of the strategy."""
        return f"MACD Strategy with {self.profile} profile - Uses MACD crossovers, RSI, and EMA indicators for entry/exit decisions"
    
    def get_strategy_parameters(self) -> Dict[str, Any]:
        """Get the current strategy parameters."""
        return {
            'profile': self.profile,
            'entry_conditions': self.entry_conditions,
            'exit_conditions': self.exit_conditions,
            'rsi_range': self.rsi_range,
            'take_profit_pct': self.take_profit_pct,
            'stop_loss_pct': self.stop_loss_pct
        }
    
    def update_parameters(self, **kwargs) -> None:
        """Update strategy parameters."""
        if 'profile' in kwargs:
            self.set_profile(kwargs['profile'])
        
        if 'entry_conditions' in kwargs:
            self.entry_conditions.update(kwargs['entry_conditions'])
        
        if 'exit_conditions' in kwargs:
            self.exit_conditions.update(kwargs['exit_conditions'])
        
        if 'rsi_range' in kwargs:
            self.rsi_range = kwargs['rsi_range']
        
        logger.info(f"Updated MACD Strategy parameters for profile: {self.profile}")
    
    def validate_data_requirements(self, data: pd.DataFrame) -> bool:
        """Validate that the data meets the strategy requirements."""
        required_columns = ['close', 'macd', 'macd_signal', 'rsi', 'ema_short', 'ema_long']
        
        for col in required_columns:
            if col not in data.columns:
                logger.error(f"Missing required column: {col}")
                return False
        
        return True 