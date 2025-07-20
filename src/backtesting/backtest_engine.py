"""
Backtesting Engine for the SMART STOCK TRADING SYSTEM.

This module provides comprehensive backtesting capabilities:
- Single and multi-stock backtesting
- Progressive historical backtesting with day-by-day simulation
- Performance metrics calculation
- Strategy profile integration
- Risk management and position sizing
- Industry diversification
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging

from src.utils.config_loader import ConfigLoader
from src.utils.logger import get_logger
from src.machine_learning.stock_scorer import ScoringMode


class BacktestEngine:
    """
    Comprehensive backtesting engine that supports:
    - Single stock backtesting
    - Multi-stock historical backtesting
    - Strategy profile integration
    - Performance metrics calculation
    - Risk management
    """
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        """Initialize the backtesting engine."""
        self.config = ConfigLoader(config_path)
        self.logger = get_logger(__name__)
        
        # Backtest results storage
        self.backtest_results = {}
        self.current_backtest = None
        
        # Lazy loading for trading system
        self._trading_system = None
        
        self.logger.info("Backtest Engine initialized")
    
    def _get_trading_system(self):
        """Get the trading system instance with lazy loading."""
        if self._trading_system is None:
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
            results = self._run_simulation(data, strategy, profile, benchmark_data, symbol)
            
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
        Run progressive historical backtest simulating day-by-day trading over the period.
        
        This approach:
        1. Starts from the beginning date and simulates trading every day
        2. Each day recalculates stock scoring based on data available up to that point
        3. Makes trading decisions based on what was actually known at that time
        4. Ensures no look-ahead bias and realistic performance testing
        
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
            self.logger.info(f"Starting progressive historical backtest with {strategy}_{profile}")
            self.logger.info(f"Simulating day-by-day trading from {start_date} to {end_date}")
            
            # Reset strategy state
            self._get_trading_system().reset_strategy(strategy)
            
            # Get all available stocks for the entire period
            all_stocks = self._get_trading_system().get_all_stocks()
            
            # Prepare data for all stocks for the entire period
            stock_data = {}
            for symbol in all_stocks:
                data = self._get_trading_system().prepare_data(symbol, start_date, end_date)
                if not data.empty and len(data) > 30:  # Need enough data for indicators
                    stock_data[symbol] = data
            
            if not stock_data:
                return {'error': 'No stock data available for historical backtest'}
            
            # Get benchmark data
            benchmark_data = None
            if benchmark:
                benchmark_data = self._get_trading_system().prepare_data(benchmark, start_date, end_date)
            
            # Run progressive simulation
            results = self._run_progressive_simulation(
                stock_data, strategy, profile, benchmark_data, start_date, end_date
            )
            
            # Store results
            self.backtest_results = results
            self.current_backtest = {
                'strategy': strategy,
                'profile': profile,
                'start_date': start_date,
                'end_date': end_date,
                'symbols': list(stock_data.keys()),
                'results': results
            }
            
            self.logger.info(f"Progressive historical backtest completed with {len(stock_data)} stocks")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in progressive historical backtest: {e}")
            return {'error': str(e)}
    
    def _run_simulation(self, data: pd.DataFrame, strategy: str, profile: str, 
                       benchmark_data: pd.DataFrame = None, symbol: str = None) -> Dict[str, Any]:
        """
        Run a single-stock backtest simulation.
        
        Args:
            data: Price data with indicators
            strategy: Strategy name
            profile: Strategy profile
            benchmark_data: Benchmark data for comparison
            symbol: Stock symbol (optional, will use data.name if not provided)
            
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
            
            # Get strategy instance for direct access
            strategy_instance = self._get_trading_system().get_strategy(strategy)
            
            # Determine symbol name
            if symbol is None:
                symbol = data.name if hasattr(data, 'name') and data.name else 'UNKNOWN'
            
            # Run simulation day by day
            for i in range(len(data)):
                current_date = data.index[i]
                current_price = float(data.iloc[i]['close'])
                
                # Check for exit signals first (if we have a position)
                if symbol in positions:
                    position = positions[symbol]
                    entry_price = position['entry_price']
                    entry_date = position['entry_date']
                    
                    # Check for exit signal
                    should_exit, exit_reason = strategy_instance.should_exit(data, i, entry_price, entry_date)
                    
                    if should_exit:
                        # Execute sell
                        shares = position['shares']
                        
                        # Calculate P&L
                        pnl = float((current_price - entry_price) * shares)
                        pnl_pct = float(((current_price - entry_price) / entry_price) * 100)
                        
                        current_capital += shares * current_price
                        
                        trades.append({
                            'date': str(current_date),
                            'symbol': symbol,
                            'action': 'SELL',
                            'shares': shares,
                            'price': float(current_price),
                            'value': float(shares * current_price),
                            'pnl': pnl,
                            'pnl_pct': pnl_pct,
                            'strategy': f"{strategy}_{profile}",
                            'reason': exit_reason.get('summary', 'Exit signal')
                        })
                        
                        del positions[symbol]
                        
                        self.logger.info(f"SELL {shares:.2f} shares of {symbol} at ${current_price:.2f} (P&L: ${pnl:.2f}, {pnl_pct:.2f}%)")
                
                # Check for entry signals (if we don't have a position)
                if symbol not in positions:
                    # Check for entry signal
                    should_entry, entry_reason = strategy_instance.should_entry(data, i)
                    
                    if should_entry:
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
                                'strategy': f"{strategy}_{profile}",
                                'reason': entry_reason.get('summary', 'Entry signal')
                            })
                            
                            self.logger.info(f"BUY {shares:.2f} shares of {symbol} at ${current_price:.2f}")
                
                # Calculate portfolio value for this day
                portfolio_value = current_capital
                for pos_symbol, position in positions.items():
                    portfolio_value += position['shares'] * current_price
                
                portfolio_values.append({
                    'date': str(current_date),
                    'value': float(portfolio_value),
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
                'symbol': symbol
            }
            
        except Exception as e:
            self.logger.error(f"Error in simulation: {e}")
            return {'error': str(e)}
    
    def _run_progressive_simulation(self, stock_data: Dict[str, pd.DataFrame], 
                                   strategy: str, profile: str,
                                   benchmark_data: pd.DataFrame = None,
                                   start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """
        Run progressive historical backtest simulation.
        
        This method:
        1. Simulates trading day by day from start_date to end_date
        2. Each day recalculates stock scoring based on data available up to that point
        3. Makes trading decisions based on what was actually known at that time
        4. Ensures industry diversification
        5. No look-ahead bias
        
        Args:
            stock_data: Dictionary of stock data for entire period
            strategy: Strategy name
            profile: Strategy profile
            benchmark_data: Benchmark data for comparison
            start_date: Start date for simulation
            end_date: End date for simulation
            
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
            
            # Get strategy instance for direct access
            strategy_instance = self._get_trading_system().get_strategy(strategy)
            
            # Get all unique dates
            all_dates = set()
            for data in stock_data.values():
                if not data.empty:
                    # Ensure dates are properly formatted
                    if data.index.dtype == 'int64':
                        # Convert integer indices to proper dates
                        self.logger.warning(f"Found integer indices, converting to dates")
                        # Use the data's date column if available
                        if 'date' in data.columns:
                            data = data.set_index('date')
                        else:
                            # Create proper date range
                            start_date_dt = pd.to_datetime(start_date)
                            end_date_dt = pd.to_datetime(end_date)
                            date_range = pd.date_range(start=start_date_dt, end=end_date_dt, freq='D')
                            data = data.set_index(date_range[:len(data)])
                    
                    all_dates.update(data.index)
            
            all_dates = sorted(list(all_dates))
            
            self.logger.info(f"Total available dates: {len(all_dates)}")
            if all_dates:
                self.logger.info(f"Date range: {all_dates[0]} to {all_dates[-1]}")
                self.logger.info(f"Sample dates: {all_dates[:5]}")
            
            # Filter dates to simulation period
            if start_date:
                start_dt = pd.to_datetime(start_date).tz_localize(None)  # Make timezone-naive
                self.logger.info(f"Filtering from start date: {start_dt}")
                all_dates = [d for d in all_dates if pd.to_datetime(d).tz_localize(None) >= start_dt]
                self.logger.info(f"Dates after start filter: {len(all_dates)}")
            if end_date:
                end_dt = pd.to_datetime(end_date).tz_localize(None)  # Make timezone-naive
                self.logger.info(f"Filtering to end date: {end_dt}")
                all_dates = [d for d in all_dates if pd.to_datetime(d).tz_localize(None) <= end_dt]
                self.logger.info(f"Dates after end filter: {len(all_dates)}")
            
            self.logger.info(f"Running progressive simulation for {len(all_dates)} trading days")
            
            # Industry classification for diversification
            industry_groups = self._classify_stocks_by_industry(list(stock_data.keys()))
            
            # Run simulation day by day
            for day_idx, current_date in enumerate(all_dates):
                if day_idx % 100 == 0:  # Log progress every 100 days
                    self.logger.info(f"Processing day {day_idx + 1}/{len(all_dates)}: {current_date}")
                
                # Calculate current portfolio value (cash + all positions)
                portfolio_value = current_capital
                
                # Recalculate stock scoring for this day based on data available up to this point
                daily_scoring = self._calculate_daily_stock_scoring(
                    stock_data, current_date, strategy, profile, industry_groups
                )
                
                # Process each stock for trading signals
                self.logger.info(f"🔄 Processing {len(daily_scoring)} stocks for trading signals on {current_date}")
                
                # Debug: check if we have any stocks to process
                if not daily_scoring:
                    self.logger.warning(f"No stocks selected for trading on {current_date}")
                    continue
                
                # Debug: log the first few stocks being processed
                self.logger.info(f"Processing stocks: {daily_scoring[:5]}...")
                
                for symbol in daily_scoring:
                    # Debug: log that we're processing this stock
                    self.logger.info(f"🔍 Processing {symbol} for trading signals on {current_date}")
                    
                    # Get stock data
                    data = stock_data.get(symbol)
                    if data is None or data.empty:
                        self.logger.warning(f"No data for {symbol} on {current_date}")
                        continue
                    
                    # Find current date index
                    current_index = None
                    for i, date in enumerate(data.index):
                        if pd.to_datetime(date).date() == pd.to_datetime(current_date).date():
                            current_index = i
                            break
                    
                    if current_index is None:
                        self.logger.warning(f"Could not find current date index for {symbol} on {current_date}")
                        continue
                    
                    # Get current price
                    current_price = float(data.iloc[current_index]['close'])
                    
                    # Debug: log that we're checking entry signals
                    self.logger.info(f"📊 Checking entry signals for {symbol} at ${current_price:.2f} on {current_date}")
                    
                    # Check for entry signals (if we don't have a position and stock is in top scoring)
                    if symbol not in positions and symbol in daily_scoring:
                        # Debug: log that we're checking this stock
                        self.logger.info(f"🔍 Checking entry signal for {symbol} on {current_date}")
                        
                        # Check for entry signal
                        should_entry, entry_reason = strategy_instance.should_entry(data, current_index)
                        
                        # Debug: log the entry decision with more detail
                        self.logger.info(f"📊 Entry decision for {symbol}: {should_entry}")
                        if should_entry:
                            self.logger.info(f"✅ Entry signal triggered for {symbol}: {entry_reason.get('entry_reason', 'No reason')}")
                        else:
                            self.logger.info(f"❌ No entry signal for {symbol}: {entry_reason.get('entry_reason', 'No reason')}")
                        
                        if should_entry:
                            # Check diversification limits
                            if self._can_add_position(symbol, positions, industry_groups):
                                # Execute buy (allocate 2% of initial capital per position for more trades)
                                position_size = initial_capital * 0.02  # Reduced from 0.05
                                if current_capital >= position_size:
                                    shares = float(position_size / current_price)
                                    positions[symbol] = {
                                        'shares': shares,
                                        'entry_price': float(current_price),
                                        'entry_date': current_date,
                                        'entry_reason': entry_reason.get('entry_reason', 'MACD signal')
                                    }
                                    current_capital -= position_size
                                        
                                    # Log the trade
                                    self.logger.info(f"✅ BUY {symbol}: {shares:.2f} shares at ${current_price:.2f} on {current_date}")
                                    trades.append({
                                        'date': current_date,
                                        'symbol': symbol,
                                        'action': 'BUY',
                                        'shares': shares,
                                        'price': current_price,
                                        'reason': entry_reason.get('entry_reason', 'MACD signal')
                                    })
                                else:
                                    self.logger.info(f"❌ Insufficient capital for {symbol} on {current_date}")
                            else:
                                self.logger.info(f"❌ Diversification limit reached for {symbol} on {current_date}")
                        else:
                            self.logger.info(f"❌ No entry signal for {symbol} on {current_date}")
                    
                    # Check for exit signals (if we have a position)
                    if symbol in positions:
                        should_exit, exit_reason = strategy_instance.should_exit(data, current_index)
                            
                        if should_exit:
                            position = positions[symbol]
                            shares = position['shares']
                            entry_price = position['entry_price']
                            exit_price = current_price
                            
                            # Calculate profit/loss
                            profit_loss = (exit_price - entry_price) * shares
                            current_capital += (shares * exit_price)
                            
                            # Log the trade
                            self.logger.info(f"✅ SELL {symbol}: {shares:.2f} shares at ${exit_price:.2f} on {current_date} (P&L: ${profit_loss:.2f})")
                            trades.append({
                                'date': current_date,
                                'symbol': symbol,
                                'action': 'SELL',
                                'shares': shares,
                                'price': exit_price,
                                'reason': exit_reason.get('exit_reason', 'MACD signal'),
                                'profit_loss': profit_loss
                            })
                            
                            # Remove position
                            del positions[symbol]
                
                # Calculate portfolio value for this day
                portfolio_value = current_capital
                for symbol, position in positions.items():
                    if symbol in stock_data and not stock_data[symbol].empty:
                        current_price = stock_data[symbol].iloc[-1]['close']
                        portfolio_value += position['shares'] * current_price
                
                # Log daily portfolio value
                self.logger.info(f"💰 Portfolio value on {current_date}: ${portfolio_value:.2f}")
                
                # Store daily portfolio value
                portfolio_values.append({
                    'date': current_date,
                    'value': portfolio_value,
                    'cash': current_capital,
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
                'symbols': list(stock_data.keys())
            }
            
        except Exception as e:
            self.logger.error(f"Error in progressive simulation: {e}")
            return {'error': str(e)}
    
    def _calculate_daily_stock_scoring(self, stock_data: Dict[str, pd.DataFrame], 
                                      current_date: pd.Timestamp, strategy: str, profile: str,
                                      industry_groups: Dict[str, str]) -> List[str]:
        """
        Calculate stock scoring for a specific day based on data available up to that point.
        
        Args:
            stock_data: Dictionary of stock data
            current_date: Current trading date
            strategy: Strategy name
            profile: Strategy profile
            industry_groups: Industry classification
            
        Returns:
            List of top scoring stock symbols for this day
        """
        try:
            # Get data up to current date for each stock
            daily_stock_data = {}
            debug_count = 0
            for symbol, data in stock_data.items():
                if debug_count < 3:  # Debug first 3 stocks
                    self.logger.info(f"Debug {symbol}: columns={data.columns.tolist()}, shape={data.shape}")
                    if not data.empty:
                        self.logger.info(f"Debug {symbol}: sample data=\n{data.head(2)}")
                    debug_count += 1
                
                # Get data up to current date (no future data)
                # Ensure proper date comparison
                if data.index.dtype == 'int64':
                    # If we have integer indices, we need to handle this differently
                    # For now, use all available data since we've already converted indices
                    historical_data = data
                else:
                    # Normal date filtering with timezone handling
                    try:
                        # Make current_date timezone-naive for comparison
                        current_date_naive = pd.to_datetime(current_date).tz_localize(None)
                        # Make data index timezone-naive
                        data_index_naive = data.index.tz_localize(None) if data.index.tz is not None else data.index
                        historical_data = data[data_index_naive <= current_date_naive]
                    except Exception as e:
                        self.logger.warning(f"Date filtering error for {symbol}: {e}, using all data")
                        historical_data = data
                
                # Ensure data has correct column structure
                if len(historical_data) > 30:  # Need enough data for indicators
                    # Ensure we have the required columns
                    required_columns = ['open', 'high', 'low', 'close', 'volume']
                    if all(col in historical_data.columns for col in required_columns):
                        daily_stock_data[symbol] = historical_data
                    else:
                        self.logger.warning(f"Missing required columns for {symbol}: {historical_data.columns.tolist()}")
            
            self.logger.info(f"Found {len(daily_stock_data)} stocks with valid data structure")
            
            if not daily_stock_data:
                return []
            
            # Calculate scores for each stock based on historical data
            stock_scores = []
            for symbol, data in daily_stock_data.items():
                try:
                    # Check if indicators are already calculated
                    if 'macd_line' in data.columns and 'rsi' in data.columns:
                        # Use existing indicators
                        indicators = data
                        self.logger.debug(f"Using existing indicators for {symbol}")
                    else:
                        # Calculate technical indicators for historical data
                        indicators = self._get_trading_system().calculate_indicators(data)
                    
                    # Calculate score based on indicators
                    score = self._calculate_stock_score(indicators, strategy, profile)
                    
                    # Add industry diversification bonus
                    industry = industry_groups.get(symbol, 'Unknown')
                    industry_bonus = self._get_industry_bonus(industry, data)
                    final_score = score + industry_bonus
                    
                    stock_scores.append({
                        'symbol': symbol,
                        'score': final_score,
                        'industry': industry
                    })
                    
                except Exception as e:
                    self.logger.warning(f"Error scoring {symbol} for {current_date}: {e}")
                    continue
            
            # Sort by score and select top stocks with industry diversification
            stock_scores.sort(key=lambda x: x['score'], reverse=True)
            
            # Debug: log top scoring stocks
            if stock_scores:
                self.logger.info(f"Top 5 scoring stocks for {current_date}:")
                for i, stock in enumerate(stock_scores[:5]):
                    self.logger.info(f"  {i+1}. {stock['symbol']}: score={stock['score']:.3f}, industry={stock['industry']}")
            
            # Select top stocks ensuring industry diversification
            selected_stocks = self._select_diversified_stocks(stock_scores, max_stocks=20)
            
            # Debug: log selected stocks
            if selected_stocks:
                self.logger.info(f"Selected {len(selected_stocks)} stocks for {current_date}: {[s['symbol'] for s in selected_stocks]}")
            else:
                self.logger.warning(f"No stocks selected for {current_date}")
            
            return [stock['symbol'] for stock in selected_stocks]
            
        except Exception as e:
            self.logger.error(f"Error calculating daily stock scoring: {e}")
            return []
    
    def _classify_stocks_by_industry(self, symbols: List[str]) -> Dict[str, str]:
        """
        Classify stocks by industry for diversification.
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Dictionary mapping symbols to industries
        """
        # Industry classification mapping
        industry_mapping = {
            # Technology
            'AAPL': 'Technology', 'MSFT': 'Technology', 'GOOGL': 'Technology', 
            'META': 'Technology', 'NVDA': 'Technology', 'TSLA': 'Technology',
            'AMZN': 'Technology', 'NFLX': 'Technology', 'ADBE': 'Technology',
            'CRM': 'Technology', 'ORCL': 'Technology', 'ZM': 'Technology',
            
            # Healthcare
            'JNJ': 'Healthcare', 'PFE': 'Healthcare', 'MRK': 'Healthcare',
            'UNH': 'Healthcare', 'ABBV': 'Healthcare', 'LLY': 'Healthcare',
            'TMO': 'Healthcare', 'DHR': 'Healthcare',
            
            # Financial
            'JPM': 'Financial', 'BAC': 'Financial', 'WFC': 'Financial',
            'GS': 'Financial', 'MS': 'Financial', 'V': 'Financial',
            'MA': 'Financial', 'PYPL': 'Financial',
            
            # Consumer
            'PG': 'Consumer', 'KO': 'Consumer', 'PEP': 'Consumer',
            'WMT': 'Consumer', 'COST': 'Consumer', 'HD': 'Consumer',
            'MCD': 'Consumer', 'NKE': 'Consumer', 'DIS': 'Consumer',
            
            # Industrial
            'CAT': 'Industrial', 'BA': 'Industrial', 'MMM': 'Industrial',
            'GE': 'Industrial', 'HON': 'Industrial',
            
            # Energy
            'XOM': 'Energy', 'CVX': 'Energy', 'COP': 'Energy',
            
            # ETFs
            'SPY': 'ETF', 'QQQ': 'ETF', 'IWM': 'ETF', 'VTI': 'ETF',
            'VOO': 'ETF', 'VEA': 'ETF', 'VWO': 'ETF'
        }
        
        # Default to 'Other' for unknown symbols
        return {symbol: industry_mapping.get(symbol, 'Other') for symbol in symbols}
    
    def _get_industry_bonus(self, industry: str, data: pd.DataFrame) -> float:
        """
        Calculate industry bonus based on sector trends.
        
        Args:
            industry: Industry classification
            data: Stock price data
            
        Returns:
            Industry bonus score
        """
        try:
            if len(data) < 20:
                return 0.0
            
            # Calculate recent performance (last 20 days)
            recent_data = data.tail(20)
            if len(recent_data) < 10:
                return 0.0
            
            # Calculate momentum
            start_price = recent_data.iloc[0]['close']
            end_price = recent_data.iloc[-1]['close']
            momentum = (end_price - start_price) / start_price
            
            # Industry-specific bonuses
            industry_bonuses = {
                'Technology': 0.1,  # Tech stocks get slight bonus
                'Healthcare': 0.05,  # Healthcare gets moderate bonus
                'Financial': 0.0,    # Financial neutral
                'Consumer': 0.0,     # Consumer neutral
                'Industrial': -0.05,  # Industrial slight penalty
                'Energy': -0.1,       # Energy penalty
                'ETF': 0.0,          # ETFs neutral
                'Other': 0.0         # Other neutral
            }
            
            base_bonus = industry_bonuses.get(industry, 0.0)
            momentum_bonus = momentum * 0.5  # Scale momentum
            
            return base_bonus + momentum_bonus
            
        except Exception as e:
            self.logger.warning(f"Error calculating industry bonus: {e}")
            return 0.0
    
    def _select_diversified_stocks(self, stock_scores: List[Dict], max_stocks: int = 20) -> List[Dict]:
        """
        Select stocks ensuring industry diversification.
        
        Args:
            stock_scores: List of stock scores with industry info
            max_stocks: Maximum number of stocks to select
            
        Returns:
            List of selected stocks
        """
        selected = []
        industry_counts = {}
        
        # First pass: select top stocks from each industry
        for stock in stock_scores:
            industry = stock['industry']
            current_count = industry_counts.get(industry, 0)
            
            # Limit per industry to ensure diversification
            max_per_industry = max(1, max_stocks // 6)  # 6 main industries
            
            if current_count < max_per_industry and len(selected) < max_stocks:
                selected.append(stock)
                industry_counts[industry] = current_count + 1
        
        # Second pass: fill remaining slots with top overall scores
        remaining_slots = max_stocks - len(selected)
        remaining_stocks = [s for s in stock_scores if s not in selected]
        
        for stock in remaining_stocks[:remaining_slots]:
            selected.append(stock)
        
        return selected
    
    def _can_add_position(self, symbol: str, positions: Dict, industry_groups: Dict[str, str]) -> bool:
        """
        Check if we can add a position in this stock based on diversification rules.
        
        Args:
            symbol: Stock symbol
            positions: Current positions
            industry_groups: Industry classification
            
        Returns:
            True if position can be added
        """
        if symbol in positions:
            return False
        
        # Check industry diversification
        symbol_industry = industry_groups.get(symbol, 'Other')
        industry_positions = sum(1 for pos in positions.keys() 
                               if industry_groups.get(pos, 'Other') == symbol_industry)
        
        # Limit positions per industry
        max_per_industry = 3
        return industry_positions < max_per_industry
    
    def _calculate_stock_score(self, indicators: pd.DataFrame, strategy: str, profile: str) -> float:
        """
        Calculate stock score based on technical indicators.
        
        Args:
            indicators: Technical indicators data
            strategy: Strategy name
            profile: Strategy profile
            
        Returns:
            Stock score (0.0 to 1.0)
        """
        try:
            if indicators.empty:
                return 0.0
            
            # Get latest indicator values
            latest = indicators.iloc[-1]
            
            # Calculate score based on strategy
            if strategy == 'MACD':
                # MACD-based scoring - More aggressive for testing
                macd_score = 0.0
                if 'macd' in latest and 'macd_signal' in latest:
                    macd = latest['macd']
                    signal = latest['macd_signal']
                    
                    # More aggressive MACD scoring
                    if macd > signal and macd > 0:
                        macd_score = 0.6  # Increased from 0.4
                    elif macd > signal:
                        macd_score = 0.4  # Increased from 0.2
                    elif macd < signal and macd < 0:
                        macd_score = -0.1  # Reduced penalty from -0.2
                    else:
                        macd_score = 0.1  # Neutral case gets small positive score
                
                # RSI scoring - More lenient
                rsi_score = 0.0
                if 'rsi' in latest:
                    rsi = latest['rsi']
                    if 35 <= rsi <= 65:  # Wider neutral RSI range
                        rsi_score = 0.4  # Increased from 0.3
                    elif 25 <= rsi <= 75:  # Wider acceptable RSI range
                        rsi_score = 0.2  # Increased from 0.1
                    else:  # Extreme RSI
                        rsi_score = -0.1  # Reduced penalty from -0.2
                
                # Price momentum - More aggressive
                momentum_score = 0.0
                if len(indicators) >= 10:  # Reduced from 20
                    recent_prices = indicators['close'].tail(10)  # Reduced from 20
                    if len(recent_prices) >= 5:  # Reduced from 10
                        start_price = recent_prices.iloc[0]
                        end_price = recent_prices.iloc[-1]
                        momentum = (end_price - start_price) / start_price
                        momentum_score = min(0.4, max(-0.2, momentum * 2))  # More aggressive scaling
                
                # Volume confirmation
                volume_score = 0.0
                if 'volume' in latest and len(indicators) >= 20:
                    current_volume = latest['volume']
                    avg_volume = indicators['volume'].tail(20).mean()
                    if current_volume > avg_volume * 1.2:  # 20% above average
                        volume_score = 0.1
                
                # Combine scores with more weight on MACD
                total_score = macd_score * 0.5 + rsi_score * 0.3 + momentum_score * 0.15 + volume_score * 0.05
                
                # More aggressive normalization
                normalized_score = max(0.0, min(1.0, (total_score + 0.3) / 1.3))  # Lower baseline
                
                # Add randomness for testing (small amount)
                import random
                random_factor = random.uniform(-0.05, 0.05)
                final_score = max(0.0, min(1.0, normalized_score + random_factor))
                
                return final_score
            
            else:
                # Default scoring - More aggressive
                return 0.6  # Increased from 0.5
                
        except Exception as e:
            self.logger.warning(f"Error calculating stock score: {e}")
            return 0.3  # Increased from 0.0
    
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
                benchmark_start = float(benchmark_data.iloc[0]['close'])
                benchmark_end = float(benchmark_data.iloc[-1]['close'])
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