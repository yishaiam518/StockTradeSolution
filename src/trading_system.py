"""
Centralized Trading System for the SMART STOCK TRADING SYSTEM.

This system serves as the single source of truth for:
- Strategy instances and configurations with profiles
- Position management across all components
- Stock selection and scoring through unified system
- Configuration management
- Integration with scoring and trading signals
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from .utils.config_loader import ConfigLoader
from .utils.logger import get_logger
from .data_engine.data_engine import DataEngine
from .indicators.indicators import TechnicalIndicators
from .portfolio_management.portfolio_manager import PortfolioManager
from .real_time_trading.position_manager import PositionManager
from .strategies.macd_strategy import MACDStrategy
from .strategies.base_strategy import BaseStrategy
from .machine_learning.stock_scorer import UnifiedStockScorer, ScoringMode


# Global trading system instance
_trading_system_instance = None


def get_trading_system() -> 'TradingSystem':
    """Get the global trading system instance."""
    global _trading_system_instance
    if _trading_system_instance is None:
        _trading_system_instance = TradingSystem()
    return _trading_system_instance


class TradingSystem:
    """
    Centralized trading system that manages all trading operations.
    
    This class serves as the single source of truth for:
    - Strategy instances and configurations with profiles
    - Position management across all components
    - Stock selection algorithms through unified scoring
    - Configuration management
    - Integration with scoring and trading signals
    """
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        """Initialize the centralized trading system."""
        self.config = ConfigLoader(config_path)
        self.logger = get_logger(__name__)
        
        # Initialize core components
        self.data_engine = DataEngine()
        self.indicators = TechnicalIndicators()
        self.portfolio_manager = PortfolioManager()
        self.position_manager = PositionManager()
        
        # Initialize unified scoring system
        self.unified_scorer = UnifiedStockScorer(config_path)
        
        # Strategy registry - single instances per strategy type
        self.strategies = {}
        self.strategy_configs = {}
        
        # Performance tracking
        self.performance_history = []
        
        # Initialize the system
        self._initialize_strategies()
        
        self.logger.info("Trading System initialized successfully")
    
    def _initialize_strategies(self):
        """Initialize all available strategies with their configurations."""
        strategies_config = self.config.get('strategies', {})
        
        # Initialize MACD Strategy with profiles
        macd_config = strategies_config.get('MACD', {})
        self.strategies['MACD'] = MACDStrategy(config_dict=macd_config, profile="balanced")
        self.strategy_configs['MACD'] = macd_config
        
        self.logger.info(f"Initialized {len(self.strategies)} strategies")
    
    def get_strategy(self, strategy_name: str) -> Optional[BaseStrategy]:
        """Get a strategy instance by name."""
        return self.strategies.get(strategy_name)
    
    def get_strategy_config(self, strategy_name: str) -> Dict[str, Any]:
        """Get configuration for a strategy."""
        return self.strategy_configs.get(strategy_name, {})
    
    def get_available_profiles(self, strategy_name: str) -> List[str]:
        """Get available profiles for a strategy."""
        if strategy_name == 'MACD':
            return ['balanced', 'canonical', 'aggressive', 'conservative']
        return []
    
    def set_strategy_profile(self, strategy_name: str, profile: str):
        """Set the profile for a strategy."""
        if strategy_name in self.strategies:
            strategy = self.strategies[strategy_name]
            if hasattr(strategy, 'set_profile'):
                strategy.set_profile(profile, self.strategy_configs[strategy_name])
                self.logger.info(f"Set {strategy_name} profile to: {profile}")
            else:
                self.logger.warning(f"Strategy {strategy_name} does not support profiles")
    
    def get_strategy_profile(self, strategy_name: str) -> Optional[str]:
        """Get the current profile for a strategy."""
        if strategy_name in self.strategies:
            strategy = self.strategies[strategy_name]
            if hasattr(strategy, 'get_profile'):
                return strategy.get_profile()
        return None
    
    def update_strategy_config(self, strategy_name: str, new_config: Dict[str, Any]):
        """Update strategy configuration and reinitialize the strategy."""
        if strategy_name in self.strategies:
            # Update config
            self.strategy_configs[strategy_name] = new_config
            
            # Reinitialize strategy with new config
            if strategy_name == 'MACD':
                current_profile = self.get_strategy_profile(strategy_name) or "balanced"
                self.strategies[strategy_name] = MACDStrategy(config_dict=new_config, profile=current_profile)
            
            self.logger.info(f"Updated configuration for {strategy_name}")
    
    def create_scoring_list(self, mode: ScoringMode, strategy: str, profile: str, 
                          symbol: str = None, max_stocks: int = 50, min_score: float = 0.3):
        """
        Create a scoring list using the unified scoring system.
        
        Args:
            mode: Scoring mode (backtesting, historical, automation)
            strategy: Strategy to use
            profile: Strategy profile to use
            symbol: Specific symbol for backtesting (None for historical/automation)
            max_stocks: Maximum number of stocks to score
            min_score: Minimum score threshold
            
        Returns:
            List of stock scores
        """
        return self.unified_scorer.create_scoring_list(
            mode=mode,
            strategy=strategy,
            profile=profile,
            symbol=symbol,
            max_stocks=max_stocks,
            min_score=min_score
        )
    
    def get_scoring_list(self, mode: ScoringMode):
        """Get the current scoring list for a mode."""
        return self.unified_scorer.get_scoring_list(mode)
    
    def generate_trading_signals(self, mode: ScoringMode, strategy: str, profile: str):
        """
        Generate trading signals using the unified scoring system.
        
        Args:
            mode: Scoring mode
            strategy: Strategy to use
            profile: Strategy profile to use
            
        Returns:
            List of trading signals
        """
        return self.unified_scorer.generate_trading_signals(mode, strategy, profile)
    
    def select_stocks(self, max_stocks: int = 10, min_score: float = 0.4) -> List[str]:
        """
        Select stocks using the unified scoring system.
        
        Args:
            max_stocks: Maximum number of stocks to select
            min_score: Minimum score threshold for selection
            
        Returns:
            List of selected stock symbols
        """
        # Use automation mode for stock selection
        scoring_list = self.unified_scorer.get_scoring_list(ScoringMode.AUTOMATION)
        
        if not scoring_list:
            # Create scoring list if it doesn't exist
            self.create_scoring_list(
                mode=ScoringMode.AUTOMATION,
                strategy="MACD",
                profile="balanced",
                max_stocks=max_stocks,
                min_score=min_score
            )
            scoring_list = self.unified_scorer.get_scoring_list(ScoringMode.AUTOMATION)
        
        # Return top stocks from scoring list
        return [score.symbol for score in scoring_list[:max_stocks]]
    
    def prepare_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Prepare data for a symbol with indicators.
        
        Args:
            symbol: Stock symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            DataFrame with price data and indicators
        """
        try:
            # Fetch data
            data = self.data_engine.fetch_data(symbol, start_date, end_date)
            
            if data.empty:
                return pd.DataFrame()
            
            # Calculate indicators
            data_with_indicators = self.indicators.calculate_all_indicators(data)
            
            return data_with_indicators
            
        except Exception as e:
            self.logger.error(f"Error preparing data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def run_strategy_signal(self, strategy_name: str, data: pd.DataFrame, index: int) -> Tuple[bool, Dict[str, Any]]:
        """
        Run a strategy to generate a signal.
        
        Args:
            strategy_name: Name of the strategy
            data: DataFrame with price data and indicators
            index: Current index in the data
            
        Returns:
            Tuple of (signal_generated, signal_details)
        """
        try:
            strategy = self.get_strategy(strategy_name)
            if not strategy:
                return False, {}
            
            # Check for entry signal
            should_entry, entry_reason = strategy.should_entry(data, index)
            
            if should_entry:
                return True, {
                    'action': 'BUY',
                    'reason': entry_reason,
                    'strategy': strategy_name,
                    'timestamp': datetime.now()
                }
            
            return False, {}
            
        except Exception as e:
            self.logger.error(f"Error running strategy signal: {str(e)}")
            return False, {}
    
    def reset_strategy(self, strategy_name: str):
        """Reset a strategy's state."""
        if strategy_name in self.strategies:
            strategy = self.strategies[strategy_name]
            if hasattr(strategy, 'reset'):
                strategy.reset()
                self.logger.info(f"Reset strategy: {strategy_name}")
    
    def get_positions(self, component: str = None) -> Dict[str, Any]:
        """
        Get current positions for a specific component or all components.
        
        Args:
            component: Component name ('backtest', 'automation', 'dashboard') or None for all
            
        Returns:
            Dictionary of positions
        """
        return self.position_manager.get_all_positions()
    
    def execute_trade(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a trade based on a signal.
        
        Args:
            signal: Trading signal from the scoring system
            
        Returns:
            Trade execution result
        """
        try:
            symbol = signal.get('symbol')
            action = signal.get('action')
            price = signal.get('price', 0)
            shares = signal.get('shares', 1)
            
            if not symbol or not action:
                return {'error': 'Invalid signal'}
            
            # Execute the trade through position manager
            result = self.position_manager.execute_trade(
                symbol=symbol,
                action=action,
                shares=shares,
                price=price,
                timestamp=signal.get('timestamp', datetime.now())
            )
            
            self.logger.info(f"Executed trade: {action} {shares} shares of {symbol} at {price}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing trade: {str(e)}")
            return {'error': str(e)}
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary from all components."""
        try:
            # Get positions
            positions = self.get_positions()
            
            # Calculate basic metrics
            total_positions = len(positions)
            total_value = sum(pos.get('current_value', 0) for pos in positions.values())
            total_pnl = sum(pos.get('unrealized_pnl', 0) for pos in positions.values())
            
            return {
                'total_positions': total_positions,
                'total_value': total_value,
                'total_pnl': total_pnl,
                'positions': positions
            }
            
        except Exception as e:
            self.logger.error(f"Error getting performance summary: {str(e)}")
            return {}
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics from the unified scoring system."""
        return self.unified_scorer.get_cache_stats()
    
    def clear_cache(self, mode: ScoringMode = None):
        """Clear cache for the unified scoring system."""
        self.unified_scorer.clear_cache(mode) 