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
        
        # Add current position tracking
        self.current_position = 0
        self.entry_price = 0.0
        self.entry_date = None
        
        # Apply configuration if provided
        if config_dict:
            # Handle profile-based configuration
            if 'profiles' in config_dict and profile in config_dict['profiles']:
                profile_config = config_dict['profiles'][profile]
                self.entry_conditions.update(profile_config.get('entry_conditions', {}))
                self.exit_conditions.update(profile_config.get('exit_conditions', {}))
                self.position_sizing.update(profile_config.get('position_sizing', {}))
            
            # Handle direct configuration
            if 'entry_conditions' in config_dict:
                self.entry_conditions.update(config_dict['entry_conditions'])
            if 'exit_conditions' in config_dict:
                self.exit_conditions.update(config_dict['exit_conditions'])
            if 'position_sizing' in config_dict:
                self.position_sizing.update(config_dict['position_sizing'])
            if 'name' in config_dict:
                self.name = config_dict['name']
        
        # Configure profile
        self.configure_profile(profile)
        
        # Strategy-specific parameters
        self.take_profit_pct = self.exit_conditions.get('take_profit_pct', 5.0)
        self.stop_loss_pct = self.exit_conditions.get('stop_loss_pct', 3.0)
        
        logger.info(f"Initialized MACD Strategy with {profile} profile")
    
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
        Entry signal: Multiple conditions for more aggressive testing
        """
        if current_index < 1:
            return False, {'summary': 'Insufficient data'}
        try:
            current_row = data.iloc[current_index]
            previous_row = data.iloc[current_index - 1] if current_index > 0 else current_row
            
            # Primary condition: MACD crossover up
            macd_crossover_up = bool(current_row.get('macd_crossover_up', False))
            
            # Additional conditions for more aggressive testing
            price_above_ema_short = bool(current_row.get('price_above_ema_short', False))
            price_above_ema_long = bool(current_row.get('price_above_ema_long', False))
            ema_bullish = bool(current_row.get('ema_bullish', False))
            rsi_neutral = bool(current_row.get('rsi_neutral', False))
            volume_above_ma = bool(current_row.get('volume_above_ma', False))
            
            # More conservative entry conditions to prevent immediate exits
            entry_conditions = [
                macd_crossover_up,  # Primary MACD signal
                price_above_ema_short,  # Price above short EMA
                price_above_ema_long,   # Price above long EMA
                ema_bullish,           # EMA trend is bullish
                rsi_neutral,           # RSI is not overbought
                volume_above_ma        # Volume is above average
            ]
            
            # Require at least 5 out of 6 conditions to be true (VERY STRICT - only high-quality entries)
            conditions_met = sum(entry_conditions)
            should_enter = conditions_met >= 5
            
            # Debug logging
            logger.info(f"MACD Strategy Entry Check:")
            logger.info(f"  macd_crossover_up: {macd_crossover_up}")
            logger.info(f"  price_above_ema_short: {price_above_ema_short}")
            logger.info(f"  price_above_ema_long: {price_above_ema_long}")
            logger.info(f"  ema_bullish: {ema_bullish}")
            logger.info(f"  rsi_neutral: {rsi_neutral}")
            logger.info(f"  volume_above_ma: {volume_above_ma}")
            logger.info(f"  conditions_met: {conditions_met}/6")
            logger.info(f"  should_enter: {should_enter}")
            
            entry_reason = {
                'entry_reason': f'MACD Strategy - {conditions_met}/6 conditions met (STRICT ENTRY)',
                'conditions': {
                    'macd_crossover_up': macd_crossover_up,
                    'price_above_ema_short': price_above_ema_short,
                    'price_above_ema_long': price_above_ema_long,
                    'ema_bullish': ema_bullish,
                    'rsi_neutral': rsi_neutral,
                    'volume_above_ma': volume_above_ma
                },
                'conditions_met': conditions_met,
                'threshold': 5
            }
            
            return should_enter, entry_reason
            
        except Exception as e:
            logger.error(f"Error in MACD entry signal: {e}")
            return False, {'summary': f'Error in entry signal: {e}'}
    
    def should_exit(self, data: pd.DataFrame, current_index: int, entry_price: float, entry_date: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Exit signal: Check for exit conditions with P&L tracking
        """
        if current_index < 1:
            return False, {'summary': 'Insufficient data'}
        
        try:
            current_row = data.iloc[current_index]
            current_price = current_row.get('close', 0)
            
            # Calculate P&L
            pnl_pct = ((current_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0
            
            # Calculate days held
            try:
                from datetime import datetime
                entry_dt = datetime.strptime(entry_date, '%Y-%m-%d')
                
                # Handle different index types (string, datetime, etc.)
                current_date = data.index[current_index]
                
                if isinstance(current_date, str):
                    current_dt = datetime.strptime(current_date, '%Y-%m-%d')
                elif hasattr(current_date, 'strftime'):
                    # It's already a datetime object
                    current_dt = current_date
                else:
                    # Try to convert to string first
                    current_dt = datetime.strptime(str(current_date), '%Y-%m-%d')
                
                days_held = (current_dt - entry_dt).days
            except Exception as e:
                # Log the error for debugging
                print(f"Error calculating days_held: {e}")
                print(f"entry_date: {entry_date}, current_date: {data.index[current_index]}")
                days_held = 0
            
            # Get exit thresholds - tight stop-loss, moderate take-profit
            take_profit_pct = self.exit_conditions.get('take_profit_pct', 7.0)   # Moderate profit-taking
            stop_loss_pct = self.exit_conditions.get('stop_loss_pct', 3.0)       # Tight stop-loss to cut losses quickly
            max_hold_days = self.exit_conditions.get('max_hold_days', 45)        # Shorter max hold
            max_drawdown_pct = self.exit_conditions.get('max_drawdown_pct', 6.0) # Tighter drawdown control
            
            # Check take profit
            if pnl_pct >= take_profit_pct:
                return True, {
                    'summary': f'Take profit triggered ({pnl_pct:.2f}%)',
                    'exit_type': 'take_profit',
                    'pnl_pct': pnl_pct,
                    'days_held': days_held
                }
            
            # Check stop loss
            if pnl_pct <= -stop_loss_pct:
                return True, {
                    'summary': f'Stop loss triggered ({pnl_pct:.2f}%)',
                    'exit_type': 'stop_loss',
                    'pnl_pct': pnl_pct,
                    'days_held': days_held
                }
            
            # Check max hold days
            if days_held >= max_hold_days:
                return True, {
                    'summary': f'Max hold days reached ({days_held} days)',
                    'exit_type': 'time_exit',
                    'pnl_pct': pnl_pct,
                    'days_held': days_held
                }
            
            # Check drawdown from peak (if we have enough data)
            if current_index > 0:
                # Find the highest price since entry
                prices_since_entry = data.iloc[:current_index + 1]['close']
                highest_price = prices_since_entry.max()
                drawdown_from_peak = ((current_price - highest_price) / highest_price) * 100
                
                if drawdown_from_peak <= -max_drawdown_pct:
                    return True, {
                        'summary': f'Max drawdown exceeded ({drawdown_from_peak:.2f}%)',
                        'exit_type': 'drawdown',
                        'pnl_pct': pnl_pct,
                        'drawdown_from_peak': drawdown_from_peak,
                        'days_held': days_held
                    }
            
            # Technical exit conditions
            macd_crossover_down = bool(current_row.get('macd_crossover_down', False))
            price_below_ema_short = bool(current_row.get('price_below_ema_short', False))
            price_below_ema_long = bool(current_row.get('price_below_ema_long', False))
            ema_bearish = bool(current_row.get('ema_bearish', False))
            rsi_overbought = bool(current_row.get('rsi_overbought', False))
            volume_below_ma = bool(current_row.get('volume_below_ma', False))
            
            # Count technical exit conditions
            technical_exit_conditions = sum([
                macd_crossover_down,
                price_below_ema_short,
                price_below_ema_long,
                ema_bearish,
                rsi_overbought,
                volume_below_ma
            ])
            
            # Exit if at least 2 technical conditions are met (RELAXED - easier to exit and lock profits)
            if technical_exit_conditions >= 2:
                return True, {
                    'summary': f'Technical exit signal ({technical_exit_conditions}/6 conditions) - RELAXED EXIT',
                    'exit_type': 'technical',
                    'pnl_pct': pnl_pct,
                    'days_held': days_held,
                    'macd_crossover_down': macd_crossover_down,
                    'price_below_ema_short': price_below_ema_short,
                    'price_below_ema_long': price_below_ema_long,
                    'ema_bearish': ema_bearish,
                    'rsi_overbought': rsi_overbought,
                    'volume_below_ma': volume_below_ma,
                    'technical_conditions': technical_exit_conditions
                }
            
            # No exit signal
            return False, {
                'summary': f'Holding position (PnL: {pnl_pct:.2f}%, Days: {days_held})',
                'pnl_pct': pnl_pct,
                'days_held': days_held
            }
            
        except Exception as e:
            logger.error(f"Error in should_exit: {str(e)}")
            return False, {'summary': f'Error: {str(e)}'}
    
    def reset(self):
        """Reset the strategy state."""
        self.current_position = 0
        self.entry_price = 0.0
        self.entry_date = None
        logger.info(f"Reset {self.name} state")
    
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