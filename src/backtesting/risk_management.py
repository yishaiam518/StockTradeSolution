"""
Risk Management Module for Backtesting
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple
import logging
from dataclasses import dataclass
from enum import Enum

class PositionSizingMethod(Enum):
    """Position sizing methods"""
    FIXED_PERCENTAGE = "fixed_percentage"
    KELLY_CRITERION = "kelly_criterion"
    VOLATILITY_BASED = "volatility_based"
    RISK_PARITY = "risk_parity"

class StopLossType(Enum):
    """Stop-loss types"""
    FIXED_PERCENTAGE = "fixed_percentage"
    ATR_BASED = "atr_based"
    TRAILING = "trailing"
    TIME_BASED = "time_based"

@dataclass
class RiskParameters:
    """Risk management parameters"""
    # Position sizing
    position_sizing_method: PositionSizingMethod
    stop_loss_type: StopLossType
    max_position_size: float = 0.1  # 10% of capital
    kelly_fraction: float = 0.25  # Conservative Kelly
    
    # Stop-loss
    stop_loss_percentage: float = 0.02  # 2%
    atr_multiplier: float = 2.0
    trailing_stop_percentage: float = 0.01  # 1%
    
    # Take-profit
    take_profit_percentage: float = 0.06  # 6%
    trailing_profit_percentage: float = 0.02  # 2%
    
    # Portfolio limits
    max_portfolio_drawdown: float = 0.20  # 20%
    max_correlation: float = 0.7
    max_sector_exposure: float = 0.3  # 30%
    
    # Volatility limits
    max_volatility: float = 0.25  # 25%
    min_volatility: float = 0.05  # 5%

class RiskManager:
    """Risk management for backtesting"""
    
    def __init__(self, risk_params: RiskParameters):
        self.params = risk_params
        self.logger = logging.getLogger(__name__)
        
        # Track portfolio state
        self.current_drawdown = 0.0
        self.peak_portfolio_value = 0.0
        self.position_correlations = {}
        self.sector_exposures = {}
    
    def calculate_position_size(self, 
                              capital: float,
                              price: float,
                              volatility: Optional[float] = None,
                              win_rate: Optional[float] = None,
                              avg_win: Optional[float] = None,
                              avg_loss: Optional[float] = None) -> float:
        """
        Calculate position size based on risk parameters
        
        Args:
            capital: Available capital
            price: Current asset price
            volatility: Asset volatility (for volatility-based sizing)
            win_rate: Historical win rate (for Kelly criterion)
            avg_win: Average winning trade
            avg_loss: Average losing trade
            
        Returns:
            Position size in dollars
        """
        try:
            if self.params.position_sizing_method == PositionSizingMethod.FIXED_PERCENTAGE:
                return self._fixed_percentage_sizing(capital)
            
            elif self.params.position_sizing_method == PositionSizingMethod.KELLY_CRITERION:
                return self._kelly_criterion_sizing(capital, win_rate, avg_win, avg_loss)
            
            elif self.params.position_sizing_method == PositionSizingMethod.VOLATILITY_BASED:
                return self._volatility_based_sizing(capital, volatility)
            
            elif self.params.position_sizing_method == PositionSizingMethod.RISK_PARITY:
                return self._risk_parity_sizing(capital, volatility)
            
            else:
                return self._fixed_percentage_sizing(capital)
                
        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return capital * 0.05  # Default to 5%
    
    def _fixed_percentage_sizing(self, capital: float) -> float:
        """Fixed percentage position sizing"""
        return capital * self.params.max_position_size
    
    def _kelly_criterion_sizing(self, capital: float, win_rate: float, 
                               avg_win: float, avg_loss: float) -> float:
        """Kelly criterion position sizing"""
        if not all([win_rate, avg_win, avg_loss]) or avg_loss == 0:
            return self._fixed_percentage_sizing(capital)
        
        # Kelly formula: f = (bp - q) / b
        # where b = odds received, p = win probability, q = loss probability
        b = avg_win / abs(avg_loss)  # odds received
        p = win_rate
        q = 1 - win_rate
        
        kelly_fraction = (b * p - q) / b
        
        # Apply conservative Kelly (fraction of full Kelly)
        conservative_kelly = kelly_fraction * self.params.kelly_fraction
        
        # Cap at max position size
        return min(capital * conservative_kelly, 
                  capital * self.params.max_position_size)
    
    def _volatility_based_sizing(self, capital: float, volatility: float) -> float:
        """Volatility-based position sizing"""
        if volatility is None or volatility == 0:
            return self._fixed_percentage_sizing(capital)
        
        # Inverse volatility sizing
        # Higher volatility = smaller position
        volatility_factor = 1 / (volatility * 10)  # Scale factor
        
        # Cap volatility factor
        volatility_factor = min(volatility_factor, 1.0)
        volatility_factor = max(volatility_factor, 0.1)
        
        return capital * self.params.max_position_size * volatility_factor
    
    def _risk_parity_sizing(self, capital: float, volatility: float) -> float:
        """Risk parity position sizing"""
        if volatility is None or volatility == 0:
            return self._fixed_percentage_sizing(capital)
        
        # Risk parity: equal risk contribution
        # For single asset, this reduces to volatility-based sizing
        return self._volatility_based_sizing(capital, volatility)
    
    def calculate_stop_loss(self, 
                           entry_price: float,
                           position_type: str,
                           atr: Optional[float] = None) -> float:
        """
        Calculate stop-loss price
        
        Args:
            entry_price: Entry price
            position_type: 'long' or 'short'
            atr: Average True Range (for ATR-based stops)
            
        Returns:
            Stop-loss price
        """
        try:
            if self.params.stop_loss_type == StopLossType.FIXED_PERCENTAGE:
                return self._fixed_percentage_stop(entry_price, position_type)
            
            elif self.params.stop_loss_type == StopLossType.ATR_BASED:
                return self._atr_based_stop(entry_price, position_type, atr)
            
            elif self.params.stop_loss_type == StopLossType.TRAILING:
                return self._trailing_stop(entry_price, position_type)
            
            else:
                return self._fixed_percentage_stop(entry_price, position_type)
                
        except Exception as e:
            self.logger.error(f"Error calculating stop-loss: {e}")
            return self._fixed_percentage_stop(entry_price, position_type)
    
    def _fixed_percentage_stop(self, entry_price: float, position_type: str) -> float:
        """Fixed percentage stop-loss"""
        if position_type == 'long':
            return entry_price * (1 - self.params.stop_loss_percentage)
        else:  # short
            return entry_price * (1 + self.params.stop_loss_percentage)
    
    def _atr_based_stop(self, entry_price: float, position_type: str, atr: float) -> float:
        """ATR-based stop-loss"""
        if atr is None:
            return self._fixed_percentage_stop(entry_price, position_type)
        
        atr_stop = atr * self.params.atr_multiplier
        
        if position_type == 'long':
            return entry_price - atr_stop
        else:  # short
            return entry_price + atr_stop
    
    def _trailing_stop(self, entry_price: float, position_type: str) -> float:
        """Trailing stop-loss (initial level)"""
        return self._fixed_percentage_stop(entry_price, position_type)
    
    def update_trailing_stop(self, 
                            current_stop: float,
                            current_price: float,
                            position_type: str) -> float:
        """Update trailing stop-loss"""
        if position_type == 'long':
            new_stop = current_price * (1 - self.params.trailing_stop_percentage)
            return max(new_stop, current_stop)  # Only move up
        else:  # short
            new_stop = current_price * (1 + self.params.trailing_stop_percentage)
            return min(new_stop, current_stop)  # Only move down
    
    def calculate_take_profit(self, entry_price: float, position_type: str) -> float:
        """Calculate take-profit price"""
        if position_type == 'long':
            return entry_price * (1 + self.params.take_profit_percentage)
        else:  # short
            return entry_price * (1 - self.params.take_profit_percentage)
    
    def update_trailing_profit(self, 
                              current_take_profit: float,
                              current_price: float,
                              position_type: str) -> float:
        """Update trailing take-profit"""
        if position_type == 'long':
            new_take_profit = current_price * (1 + self.params.trailing_profit_percentage)
            return max(new_take_profit, current_take_profit)
        else:  # short
            new_take_profit = current_price * (1 - self.params.trailing_profit_percentage)
            return min(new_take_profit, current_take_profit)
    
    def check_portfolio_limits(self, 
                             portfolio_value: float,
                             positions: Dict[str, Any],
                             correlations: Optional[Dict] = None) -> Tuple[bool, str]:
        """
        Check if portfolio violates risk limits
        
        Args:
            portfolio_value: Current portfolio value
            positions: Current positions (can be Position objects or dicts)
            correlations: Position correlations
            
        Returns:
            (is_within_limits, reason)
        """
        try:
            # Update peak portfolio value
            if portfolio_value > self.peak_portfolio_value:
                self.peak_portfolio_value = portfolio_value
            
            # Check drawdown limit
            current_drawdown = (self.peak_portfolio_value - portfolio_value) / self.peak_portfolio_value
            if current_drawdown > self.params.max_portfolio_drawdown:
                return False, f"Portfolio drawdown {current_drawdown:.2%} exceeds limit {self.params.max_portfolio_drawdown:.2%}"
            
            # Check correlation limits
            if correlations and self._check_correlation_violations(correlations):
                return False, "Position correlations exceed limits"
            
            # Check sector exposure limits
            if self._check_sector_exposure_violations(positions):
                return False, "Sector exposure exceeds limits"
            
            # Check volatility limits
            portfolio_volatility = self._calculate_portfolio_volatility(positions)
            if portfolio_volatility > self.params.max_volatility:
                return False, f"Portfolio volatility {portfolio_volatility:.2%} exceeds limit {self.params.max_volatility:.2%}"
            
            return True, "All limits satisfied"
            
        except Exception as e:
            self.logger.error(f"Error checking portfolio limits: {e}")
            return True, "Error checking limits, allowing trade"
    
    def _check_correlation_violations(self, correlations: Dict) -> bool:
        """Check for correlation violations"""
        for asset1, asset2 in correlations:
            if abs(correlations[(asset1, asset2)]) > self.params.max_correlation:
                return True
        return False
    
    def _check_sector_exposure_violations(self, positions: Dict[str, Any]) -> bool:
        """Check for sector exposure violations"""
        # This is a simplified implementation
        # In practice, you'd need sector classification data
        total_exposure = 0
        for pos in positions.values():
            if hasattr(pos, 'shares') and hasattr(pos, 'current_price'):  # Position object
                total_exposure += abs(pos.shares * pos.current_price)
            elif isinstance(pos, dict):  # Dictionary
                total_exposure += abs(pos.get('value', 0))
            else:  # Other object types
                total_exposure += abs(getattr(pos, 'value', 0))
        
        if total_exposure == 0:
            return False
        
        for position in positions.values():
            if hasattr(position, 'shares') and hasattr(position, 'current_price'):  # Position object
                position_value = abs(position.shares * position.current_price)
            elif isinstance(position, dict):  # Dictionary
                position_value = abs(position.get('value', 0))
            else:  # Other object types
                position_value = abs(getattr(position, 'value', 0))
            
            position_exposure = position_value / total_exposure
            if position_exposure > self.params.max_sector_exposure:
                return True
        return False
    
    def _calculate_portfolio_volatility(self, positions: Dict[str, Any]) -> float:
        """Calculate portfolio volatility"""
        # Simplified implementation
        # In practice, you'd need covariance matrix
        total_value = 0
        for pos in positions.values():
            if hasattr(pos, 'shares') and hasattr(pos, 'current_price'):  # Position object
                total_value += abs(pos.shares * pos.current_price)
            elif isinstance(pos, dict):  # Dictionary
                total_value += abs(pos.get('value', 0))
            else:  # Other object types
                total_value += abs(getattr(pos, 'value', 0))
        
        if total_value == 0:
            return 0
        
        # Weighted average of individual volatilities
        weighted_vol = 0
        for position in positions.values():
            if hasattr(position, 'shares') and hasattr(position, 'current_price'):  # Position object
                position_value = abs(position.shares * position.current_price)
                weight = position_value / total_value
            elif isinstance(position, dict):  # Dictionary
                position_value = abs(position.get('value', 0))
                weight = position_value / total_value
            else:  # Other object types
                position_value = abs(getattr(position, 'value', 0))
                weight = position_value / total_value
            
            vol = getattr(position, 'volatility', 0.15) if hasattr(position, 'volatility') else 0.15  # Default 15%
            weighted_vol += weight * vol
        
        return weighted_vol
    
    def should_close_position(self, 
                            position: Any,
                            current_price: float,
                            current_time: pd.Timestamp) -> Tuple[bool, str]:
        """
        Check if position should be closed due to risk management
        
        Args:
            position: Position object or dictionary
            current_price: Current asset price
            current_time: Current timestamp
            
        Returns:
            (should_close, reason)
        """
        try:
            # Extract position data
            if hasattr(position, 'entry_price'):  # Position object
                entry_price = position.entry_price
                position_type = position.position_type
                stop_loss = position.stop_loss
                take_profit = position.take_profit
            elif isinstance(position, dict):  # Dictionary
                entry_price = position.get('entry_price', 0)
                position_type = position.get('type', 'long')
                stop_loss = position.get('stop_loss', 0)
                take_profit = position.get('take_profit', 0)
            else:  # Other object types
                entry_price = getattr(position, 'entry_price', 0)
                position_type = getattr(position, 'type', 'long')
                stop_loss = getattr(position, 'stop_loss', 0)
                take_profit = getattr(position, 'take_profit', 0)
            
            # Extract entry_time
            if hasattr(position, 'entry_time'):
                entry_time = position.entry_time
            elif isinstance(position, dict):
                entry_time = position.get('entry_time')
            else:
                entry_time = getattr(position, 'entry_time', None)
            
            # Check stop-loss
            if position_type == 'long' and current_price <= stop_loss:
                return True, "Stop-loss triggered"
            elif position_type == 'short' and current_price >= stop_loss:
                return True, "Stop-loss triggered"
            
            # Check take-profit
            if position_type == 'long' and current_price >= take_profit:
                return True, "Take-profit triggered"
            elif position_type == 'short' and current_price <= take_profit:
                return True, "Take-profit triggered"
            
            # Check time-based exit
            if entry_time and self.params.stop_loss_type == StopLossType.TIME_BASED:
                time_held = current_time - pd.to_datetime(entry_time)
                if time_held.days > 30:  # 30-day time limit
                    return True, "Time-based exit"
            
            return False, "No exit signal"
            
        except Exception as e:
            self.logger.error(f"Error checking position exit: {e}")
            return False, "Error checking exit"
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """Get current risk summary"""
        return {
            'current_drawdown': self.current_drawdown,
            'peak_portfolio_value': self.peak_portfolio_value,
            'max_drawdown_limit': self.params.max_portfolio_drawdown,
            'position_sizing_method': self.params.position_sizing_method.value,
            'stop_loss_type': self.params.stop_loss_type.value,
            'max_position_size': self.params.max_position_size
        } 