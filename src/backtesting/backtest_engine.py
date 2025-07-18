"""
Backtesting Engine for the SMART STOCK TRADING SYSTEM.

This module provides backtesting functionality using the unified scoring system
and strategy+profile architecture.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import json

from ..utils.logger import get_logger
from ..machine_learning.stock_scorer import ScoringMode

logger = get_logger(__name__)


class BacktestEngine:
    """
    Backtesting engine that uses the unified scoring system.
    
    This engine:
    - Creates scoring lists for backtesting mode
    - Generates trading signals using strategy+profile
    - Simulates trading based on signals
    - Provides comprehensive performance metrics
    """
    
    def __init__(self):
        """Initialize the backtesting engine."""
        self.logger = get_logger(__name__)
        
        # Backtest state
        self.current_backtest = None
        self.backtest_results = {}
        
        self.logger.info("Backtest Engine initialized")
    
    def _get_trading_system(self):
        """Lazy load the trading system to avoid circular imports."""
        if not hasattr(self, '_trading_system'):
            from ..trading_system import get_trading_system
            self._trading_system = get_trading_system()
        return self._trading_system
    
    def run_backtest(self, symbol: str, strategy: str, profile: str, start_date: str, 
                    end_date: str, custom_parameters: Dict[str, Any] = None,
                    benchmark: str = None) -> Dict[str, Any]:
        """
        Run a backtest for a specific symbol and strategy+profile.
        
        Args:
            symbol: Stock symbol to backtest
            strategy: Strategy to use
            profile: Strategy profile to use
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            custom_parameters: Custom parameters to override config
            benchmark: Benchmark symbol for comparison
            
        Returns:
            Dictionary with backtest results
        """
        try:
            self.logger.info(f"Starting backtest for {symbol} with {strategy}_{profile}")
            
            # Reset strategy state
            self._get_trading_system().reset_strategy(strategy)
            
            # Update strategy config if custom parameters provided
            if custom_parameters:
                current_config = self._get_trading_system().get_strategy_config(strategy)
                updated_config = self._merge_parameters(current_config, custom_parameters)
                self._get_trading_system().update_strategy_config(strategy, updated_config)
            
            # Create scoring list for backtesting mode
            scoring_list = self._get_trading_system().create_scoring_list(
                mode=ScoringMode.BACKTESTING,
                strategy=strategy,
                profile=profile,
                symbol=symbol,
                max_stocks=1,  # Only the specified symbol
                min_score=0.1   # Low threshold for backtesting
            )
            
            if not scoring_list:
                return {'error': f'No scoring data available for {symbol}'}
            
            # Prepare data using centralized system
            data = self._get_trading_system().prepare_data(symbol, start_date, end_date)
            if data.empty:
                return {'error': f'No data available for {symbol}'}
            
            # Get benchmark data
            benchmark_data = None
            if benchmark and benchmark != symbol:
                benchmark_data = self._get_trading_system().prepare_data(benchmark, start_date, end_date)
            
            # Run backtest simulation
            results = self._run_simulation(data, strategy, profile, benchmark_data)
            
            # Store results
            self.backtest_results = results
            self.current_backtest = {
                'symbol': symbol,
                'strategy': strategy,
                'profile': profile,
                'start_date': start_date,
                'end_date': end_date,
                'results': results
            }
            
            self.logger.info(f"Backtest completed for {symbol}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in backtest: {e}")
            return {'error': str(e)}
    
    def run_historical_backtest(self, strategy: str, profile: str, start_date: str, 
                              end_date: str, benchmark: str = "SPY") -> Dict[str, Any]:
        """
        Run historical backtest using the unified scoring system.
        
        Args:
            strategy: Strategy to use
            profile: Strategy profile to use
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            benchmark: Benchmark symbol for comparison
            
        Returns:
            Dictionary with historical backtest results
        """
        try:
            self.logger.info(f"Starting historical backtest with {strategy}_{profile}")
            
            # Reset strategy state
            self._get_trading_system().reset_strategy(strategy)
            
            # Create scoring list for historical mode
            scoring_list = self._get_trading_system().create_scoring_list(
                mode=ScoringMode.HISTORICAL,
                strategy=strategy,
                profile=profile,
                max_stocks=20,  # Limit to top 20 stocks
                min_score=0.3
            )
            
            if not scoring_list:
                return {'error': 'No stocks selected for historical backtest'}
            
            # Get selected symbols
            selected_symbols = [score.symbol for score in scoring_list]
            
            # Prepare data for all selected stocks
            stock_data = {}
            for symbol in selected_symbols:
                data = self._get_trading_system().prepare_data(symbol, start_date, end_date)
                if not data.empty:
                    stock_data[symbol] = data
            
            if not stock_data:
                return {'error': 'No data available for selected stocks'}
            
            # Get benchmark data
            benchmark_data = None
            if benchmark:
                benchmark_data = self._get_trading_system().prepare_data(benchmark, start_date, end_date)
            
            # Run simulation
            results = self._run_multi_stock_simulation(stock_data, strategy, profile, benchmark_data)
            
            # Store results
            self.backtest_results = results
            self.current_backtest = {
                'strategy': strategy,
                'profile': profile,
                'start_date': start_date,
                'end_date': end_date,
                'symbols': selected_symbols,
                'results': results
            }
            
            self.logger.info(f"Historical backtest completed with {len(selected_symbols)} stocks")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in historical backtest: {e}")
            return {'error': str(e)}
    
    def _run_simulation(self, data: pd.DataFrame, strategy: str, profile: str, 
                       benchmark_data: pd.DataFrame = None) -> Dict[str, Any]:
        """
        Run a single-stock backtest simulation.
        
        Args:
            data: Price data with indicators
            strategy: Strategy name
            profile: Strategy profile
            benchmark_data: Benchmark data for comparison
            
        Returns:
            Dictionary with simulation results
        """
        try:
            # Initialize simulation variables
            initial_capital = 10000
            current_capital = initial_capital
            positions = {}
            trades = []
            portfolio_values = []
            
            # Set strategy profile
            self._get_trading_system().set_strategy_profile(strategy, profile)
            
            # Run simulation day by day
            for i in range(len(data)):
                current_date = data.index[i]
                current_price = data.iloc[i]['close']
                
                # Check for trading signals
                signal_generated, signal_details = self._get_trading_system().run_strategy_signal(
                    strategy, data, i
                )
                
                if signal_generated:
                    action = signal_details.get('action')
                    symbol = data.name if hasattr(data, 'name') else 'UNKNOWN'
                    
                    if action == 'BUY' and symbol not in positions:
                        # Execute buy
                        shares = current_capital / current_price
                        positions[symbol] = {
                            'shares': shares,
                            'entry_price': current_price,
                            'entry_date': current_date
                        }
                        current_capital = 0
                        
                        trades.append({
                            'date': current_date,
                            'symbol': symbol,
                            'action': 'BUY',
                            'shares': shares,
                            'price': current_price,
                            'value': shares * current_price,
                            'strategy': f"{strategy}_{profile}"
                        })
                        
                        self.logger.info(f"BUY {shares:.2f} shares of {symbol} at ${current_price:.2f}")
                    
                    elif action == 'SELL' and symbol in positions:
                        # Execute sell
                        position = positions[symbol]
                        shares = position['shares']
                        entry_price = position['entry_price']
                        
                        # Calculate P&L
                        pnl = (current_price - entry_price) * shares
                        pnl_pct = ((current_price - entry_price) / entry_price) * 100
                        
                        current_capital = shares * current_price
                        
                        trades.append({
                            'date': current_date,
                            'symbol': symbol,
                            'action': 'SELL',
                            'shares': shares,
                            'price': current_price,
                            'value': shares * current_price,
                            'pnl': pnl,
                            'pnl_pct': pnl_pct,
                            'strategy': f"{strategy}_{profile}"
                        })
                        
                        del positions[symbol]
                        
                        self.logger.info(f"SELL {shares:.2f} shares of {symbol} at ${current_price:.2f} (P&L: ${pnl:.2f}, {pnl_pct:.2f}%)")
                
                # Calculate current portfolio value
                portfolio_value = current_capital
                for symbol, position in positions.items():
                    portfolio_value += position['shares'] * current_price
                
                portfolio_values.append({
                    'date': current_date,
                    'value': portfolio_value,
                    'capital': current_capital,
                    'positions': len(positions)
                })
            
            # Calculate performance metrics
            performance = self._calculate_performance_metrics(
                initial_capital, portfolio_values, trades, benchmark_data
            )
            
            return {
                'trades': trades,
                'portfolio_values': portfolio_values,
                'performance': performance,
                'strategy': strategy,
                'profile': profile,
                'symbol': data.name if hasattr(data, 'name') else 'UNKNOWN'
            }
            
        except Exception as e:
            self.logger.error(f"Error in simulation: {e}")
            return {'error': str(e)}
    
    def _run_multi_stock_simulation(self, stock_data: Dict[str, pd.DataFrame], 
                                   strategy: str, profile: str,
                                   benchmark_data: pd.DataFrame = None) -> Dict[str, Any]:
        """
        Run a multi-stock historical backtest simulation.
        
        Args:
            stock_data: Dictionary of stock data
            strategy: Strategy name
            profile: Strategy profile
            benchmark_data: Benchmark data for comparison
            
        Returns:
            Dictionary with simulation results
        """
        try:
            # Initialize simulation variables
            initial_capital = 100000
            current_capital = initial_capital
            positions = {}
            trades = []
            portfolio_values = []
            
            # Set strategy profile
            self._get_trading_system().set_strategy_profile(strategy, profile)
            
            # Get all unique dates
            all_dates = set()
            for data in stock_data.values():
                all_dates.update(data.index)
            all_dates = sorted(list(all_dates))
            
            # Run simulation day by day
            for current_date in all_dates:
                daily_portfolio_value = current_capital
                
                # Check each stock for signals
                for symbol, data in stock_data.items():
                    if current_date in data.index:
                        current_price = data.loc[current_date]['close']
                        
                        # Check for trading signals
                        signal_generated, signal_details = self._get_trading_system().run_strategy_signal(
                            strategy, data, data.index.get_loc(current_date)
                        )
                        
                        if signal_generated:
                            action = signal_details.get('action')
                            
                            if action == 'BUY' and symbol not in positions:
                                # Execute buy (allocate 10% of capital per position)
                                position_size = initial_capital * 0.1
                                if current_capital >= position_size:
                                    shares = float(position_size / current_price)
                                    positions[symbol] = {
                                        'shares': shares,
                                        'entry_price': float(current_price),
                                        'entry_date': str(current_date)
                                    }
                                    current_capital -= position_size
                                    
                                    trades.append({
                                        'date': str(current_date),
                                        'symbol': symbol,
                                        'action': 'BUY',
                                        'shares': shares,
                                        'price': float(current_price),
                                        'value': float(shares * current_price),
                                        'strategy': f"{strategy}_{profile}"
                                    })
                            
                            elif action == 'SELL' and symbol in positions:
                                # Execute sell
                                position = positions[symbol]
                                shares = position['shares']
                                entry_price = position['entry_price']
                                
                                # Calculate P&L
                                pnl = float((current_price - entry_price) * shares)
                                pnl_pct = float(((current_price - entry_price) / entry_price) * 100)
                                
                                current_capital += shares * current_price
                                
                                trades.append({
                                    'date': str(current_date),
                                    'symbol': symbol,
                                    'action': 'SELL',
                                    'shares': float(shares),
                                    'price': float(current_price),
                                    'value': float(shares * current_price),
                                    'pnl': pnl,
                                    'pnl_pct': pnl_pct,
                                    'strategy': f"{strategy}_{profile}"
                                })
                                
                                del positions[symbol]
                
                # Calculate current portfolio value
                for symbol, position in positions.items():
                    if symbol in stock_data and current_date in stock_data[symbol].index:
                        current_price = stock_data[symbol].loc[current_date]['close']
                        daily_portfolio_value += position['shares'] * current_price
                
                portfolio_values.append({
                    'date': str(current_date),
                    'value': float(daily_portfolio_value),
                    'capital': float(current_capital),
                    'positions': int(len(positions))
                })
            
            # Calculate performance metrics
            performance = self._calculate_performance_metrics(
                initial_capital, portfolio_values, trades, benchmark_data
            )
            
            return {
                'trades': trades,
                'portfolio_values': portfolio_values,
                'performance': performance,
                'strategy': strategy,
                'profile': profile,
                'symbols': list(stock_data.keys())
            }
            
        except Exception as e:
            self.logger.error(f"Error in multi-stock simulation: {e}")
            return {'error': str(e)}
    
    def _calculate_performance_metrics(self, initial_capital: float, 
                                     portfolio_values: List[Dict], 
                                     trades: List[Dict],
                                     benchmark_data: pd.DataFrame = None) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics."""
        try:
            if not portfolio_values:
                return {}
            
            # Basic metrics
            final_value = portfolio_values[-1]['value']
            total_return = float(((final_value - initial_capital) / initial_capital) * 100)
            
            # Calculate returns
            returns = []
            for i in range(1, len(portfolio_values)):
                prev_value = portfolio_values[i-1]['value']
                curr_value = portfolio_values[i]['value']
                daily_return = (curr_value - prev_value) / prev_value
                returns.append(daily_return)
            
            # Risk metrics
            if returns:
                volatility = float(np.std(returns) * np.sqrt(252))  # Annualized
                sharpe_ratio = float((np.mean(returns) * 252) / volatility) if volatility > 0 else 0.0
                
                # Maximum drawdown
                cumulative_returns = np.cumprod(1 + np.array(returns))
                running_max = np.maximum.accumulate(cumulative_returns)
                drawdown = (cumulative_returns - running_max) / running_max
                max_drawdown = float(np.min(drawdown) * 100)
            else:
                volatility = 0.0
                sharpe_ratio = 0.0
                max_drawdown = 0.0
            
            # Trade metrics
            total_trades = len(trades)
            winning_trades = len([t for t in trades if t.get('pnl', 0) > 0])
            win_rate = float((winning_trades / total_trades * 100) if total_trades > 0 else 0)
            
            # Average trade metrics
            trade_returns = [t.get('pnl_pct', 0) for t in trades if 'pnl_pct' in t]
            avg_trade_return = float(np.mean(trade_returns) if trade_returns else 0)
            
            # Benchmark comparison
            benchmark_return = 0.0
            if benchmark_data is not None and len(benchmark_data) > 0:
                benchmark_start = benchmark_data.iloc[0]['close']
                benchmark_end = benchmark_data.iloc[-1]['close']
                benchmark_return = float(((benchmark_end - benchmark_start) / benchmark_start) * 100)
            
            alpha = float(total_return - benchmark_return)
            
            return {
                'total_return': total_return,
                'final_value': float(final_value),
                'volatility': volatility,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'total_trades': int(total_trades),
                'winning_trades': int(winning_trades),
                'win_rate': win_rate,
                'avg_trade_return': avg_trade_return,
                'benchmark_return': benchmark_return,
                'alpha': alpha
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating performance metrics: {e}")
            return {}
    
    def _merge_parameters(self, base_config: Dict[str, Any], 
                         custom_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Merge custom parameters with base configuration."""
        merged_config = base_config.copy()
        
        # Handle profile-specific parameters
        if 'profiles' in merged_config:
            for profile_name, profile_config in merged_config['profiles'].items():
                if profile_name in custom_parameters:
                    profile_config.update(custom_parameters[profile_name])
        
        # Handle top-level parameters
        for key, value in custom_parameters.items():
            if key != 'profiles':
                merged_config[key] = value
        
        return merged_config
    
    def get_current_backtest(self) -> Optional[Dict[str, Any]]:
        """Get the current backtest results."""
        return self.current_backtest
    
    def export_results(self, filename: str = None) -> str:
        """Export backtest results to JSON file."""
        if not self.current_backtest:
            return "No backtest results to export"
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backtest_results_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.current_backtest, f, indent=2, default=str)
            
            self.logger.info(f"Results exported to {filename}")
            return filename
            
        except Exception as e:
            self.logger.error(f"Error exporting results: {e}")
            return f"Error exporting results: {str(e)}" 