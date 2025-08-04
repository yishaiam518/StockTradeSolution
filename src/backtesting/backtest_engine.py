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

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import uuid
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.trading_system import TradingSystem
from src.utils.logger import get_logger
from src.data_engine.data_cache import DataCache
from src.data_engine.data_engine import DataEngine
from src.utils.timezone_utils import (
    make_timezone_naive, normalize_dataframe_dates, 
    normalize_index_dates, safe_date_comparison,
    safe_date_range_filter, parse_date_string
)


class BacktestEngine:
    """
    Enhanced Backtest Engine with caching and transaction logging.
    
    Features:
    - Local data caching to avoid repeated API calls
    - Transaction logging for historical analysis
    - Performance optimization through intelligent caching
    """
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config_path = config_path
        self.logger = get_logger(__name__)
        
        # Initialize components
        self.trading_system = TradingSystem(config_path)
        self.data_cache = DataCache()
        self.data_engine = DataEngine()
        
        self.logger.info("Backtest Engine initialized with caching and transaction logging")
    
    def ensure_fresh_data(self):
        """Ensure we have fresh data before any trading operations."""
        self.logger.info("🔄 Ensuring fresh data before trading...")
        
        try:
            # Run daily data collection
            results = self.daily_collector.run_daily_job()
            
            if results['symbols_updated'] > 0:
                self.logger.info(f"✅ Fresh data collected: {results['symbols_updated']} symbols updated")
            else:
                self.logger.warning("⚠️  No symbols were updated during data collection")
                
        except Exception as e:
            self.logger.error(f"❌ Error during data collection: {str(e)}")
            # Continue with cached data if collection fails
    
    def run_backtest(self, symbol: str, strategy: str, profile: str, start_date: str, 
                    end_date: str, custom_parameters: Dict[str, Any] = None,
                    benchmark: str = None) -> Dict[str, Any]:
        """
        Run a single-symbol backtest with caching.
        """
        backtest_id = f"backtest_{uuid.uuid4().hex[:8]}"
        self.logger.info(f"Starting backtest {backtest_id} for {symbol}")
        
        try:
            # Check cache first
            cached_data = self.data_cache.get_cached_data(symbol, start_date, end_date)
            
            if cached_data is not None:
                self.logger.info(f"Using cached data for {symbol}")
                data = cached_data
            else:
                self.logger.info(f"Fetching fresh data for {symbol}")
                data = self.trading_system.prepare_data(symbol, start_date, end_date)
                
                # Cache the data
                self.data_cache.cache_data(symbol, data, start_date, end_date)
            
            # Run simulation
            results = self._run_simulation(data, strategy, profile, symbol=symbol)
            
            # Add metadata
            results.update({
                'backtest_id': backtest_id,
                'symbol': symbol,
                'strategy': strategy,
                'profile': profile,
                'start_date': start_date,
                'end_date': end_date,
                'benchmark': benchmark
            })
            
            # Log backtest results
            self.data_cache.log_backtest_result(backtest_id, results)
            
            self.current_backtest = results
            return results
            
        except Exception as e:
            self.logger.error(f"Error in backtest {backtest_id}: {e}")
            return {'error': str(e), 'backtest_id': backtest_id}
    
    def run_historical_backtest(self, strategy, profile, start_date, end_date, benchmark):
        """
        Run a historical backtest with enhanced data collection.
        
        For realistic simulation, we collect 1 year of data before the test period
        to meet minimum data requirements, then run the actual backtest.
        """
        try:
            # Store the strategy name for use in signal checking
            self.current_strategy = strategy
            
            # Convert dates to datetime objects
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Calculate the data collection period (1 year before test period)
            data_collection_start = start_dt - timedelta(days=365)
            data_collection_end = start_dt - timedelta(days=1)  # Day before test starts
            
            print(f"🔄 Historical Backtest Setup:")
            print(f"   📊 Test Period: {start_date} to {end_date}")
            print(f"   📈 Data Collection Period: {data_collection_start.strftime('%Y-%m-%d')} to {data_collection_end.strftime('%Y-%m-%d')}")
            print(f"   🎯 Strategy: {strategy} ({profile})")
            print(f"   📊 Benchmark: {benchmark}")
            
            # Step 1: Collect historical data for 1 year before test period
            print(f"\n📡 Step 1: Collecting historical data for minimum requirements...")
            
            # Get available symbols for data collection
            available_symbols = self._get_available_symbols_for_period(
                data_collection_start.strftime('%Y-%m-%d'),
                data_collection_end.strftime('%Y-%m-%d')
            )
            
            print(f"   ✅ Found {len(available_symbols)} symbols with sufficient historical data")
            
            # Step 2: Run the actual backtest with the collected data context
            print(f"\n🚀 Step 2: Running backtest with historical context...")
            
            # Get trading dates for the actual test period
            trading_dates = self._get_trading_dates(start_date, end_date)
            print(f"   📅 Trading days in test period: {len(trading_dates)}")
            
            # Initialize portfolio
            portfolio = {
                'cash': 100000.0,
                'positions': {},
                'trades': [],
                'daily_values': []
            }
            
            # Track portfolio value over time
            initial_value = portfolio['cash']
            
            # Process each trading day
            for i, current_date in enumerate(trading_dates):
                print(f"   🔄 Processing day {i+1}/{len(trading_dates)}: {current_date}")
                
                # Get available stocks for this day (using the historical data context)
                available_stocks = self._get_available_stocks_for_date(
                    current_date, 
                    available_symbols,
                    data_collection_start.strftime('%Y-%m-%d')  # Use extended data period
                )
                
                if not available_stocks:
                    print(f"      ⚠️ No stocks available for {current_date}")
                    continue
                
                # Process each available stock
                for symbol in available_stocks:
                    # Get stock data with extended historical context
                    data = self._get_stock_data_with_context(
                        symbol, 
                        data_collection_start.strftime('%Y-%m-%d'),
                        current_date
                    )
                    
                    if data is None or len(data) < 50:  # Keep original 50 data points requirement
                        continue
                    
                    # Calculate indicators
                    indicators = self._calculate_indicators(data)
                    
                    # Check for entry/exit signals
                    entry_signal = self._check_entry_signal(symbol, indicators, current_date)
                    exit_signal = self._check_exit_signal(symbol, indicators, current_date, portfolio)
                    
                    # Execute trades
                    if entry_signal and portfolio['cash'] > 1000:  # Minimum cash requirement
                        self._execute_buy_trade(symbol, data, current_date, portfolio, indicators)
                    elif exit_signal:
                        self._execute_sell_trade(symbol, data, current_date, portfolio, indicators)
                
                # Calculate daily portfolio value
                daily_value = self._calculate_portfolio_value(portfolio, current_date)
                portfolio['daily_values'].append({
                    'date': current_date,
                    'value': daily_value
                })
            
            # Calculate final metrics
            final_value = self._calculate_portfolio_value(portfolio, end_date)
            total_return = ((final_value - initial_value) / initial_value) * 100
            
            # Calculate benchmark return
            benchmark_return = self._calculate_benchmark_return(benchmark, start_date, end_date)
            alpha = total_return - benchmark_return
            
            # Prepare results
            results = {
                'trades': portfolio['trades'],
                'total_trades': len(portfolio['trades']),
                'final_portfolio_value': final_value,
                'total_return': total_return,
                'benchmark_return': benchmark_return,
                'alpha': alpha,
                'initial_value': initial_value,
                'daily_values': portfolio['daily_values']
            }
            
            print(f"\n✅ Historical Backtest Completed!")
            print(f"   📊 Total trades: {len(portfolio['trades'])}")
            print(f"   💰 Final portfolio value: ${final_value:,.2f}")
            print(f"   📈 Total return: {total_return:.2f}%")
            print(f"   📊 Benchmark return: {benchmark_return:.2f}%")
            print(f"   🎯 Alpha: {alpha:.2f}%")
            
            return results
            
        except Exception as e:
            print(f"❌ Error in historical backtest: {str(e)}")
            import traceback
            print(f"🔍 Traceback: {traceback.format_exc()}")
            return {'error': str(e)}
    
    def _get_cached_or_fetch_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Get data from cache or fetch if not available."""
        cached_data = self.data_cache.get_cached_data(symbol, start_date, end_date)
        
        if cached_data is not None:
            # Normalize dates to timezone-naive UTC
            return normalize_index_dates(cached_data)
        else:
            data = self.trading_system.prepare_data(symbol, start_date, end_date)
            self.data_cache.cache_data(symbol, data, start_date, end_date)
            # Normalize dates to timezone-naive UTC
            return normalize_index_dates(data)
    
    def _load_all_stock_data_cached(self, start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """Load all stock data with caching."""
        # Define stock symbols (you can expand this list)
        symbols = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'ADBE', 'CRM',
            'ORCL', 'INTC', 'AMD', 'QCOM', 'AVGO', 'TXN', 'MU', 'AMAT', 'KLAC', 'LRCX',
            'SPY', 'QQQ', 'VOO', 'VTI', 'IWM', 'VEA', 'VWO', 'BND', 'TLT', 'GLD',
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'USB', 'PNC', 'COF', 'AXP',
            'JNJ', 'PFE', 'UNH', 'ABBV', 'MRK', 'TMO', 'ABT', 'DHR', 'BMY', 'AMGN',
            'KO', 'PEP', 'WMT', 'HD', 'MCD', 'SBUX', 'NKE', 'DIS', 'CMCSA', 'VZ'
        ]
        
        stock_data = {}
        for symbol in symbols:
            try:
                data = self._get_cached_or_fetch_data(symbol, start_date, end_date)
                if not data.empty:
                    stock_data[symbol] = data
                    self.logger.debug(f"Loaded cached data for {symbol}: {len(data)} data points")
            except Exception as e:
                self.logger.warning(f"Could not load data for {symbol}: {e}")
                continue
        
        self.logger.info(f"Loaded data for {len(stock_data)} symbols")
        return stock_data
    
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
            self.trading_system.set_strategy_profile(strategy, profile)
            
            # Get strategy instance for direct access
            strategy_instance = self.trading_system.get_strategy(strategy)
            
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
                        
                        self.logger.info(f"SELL {shares} shares of {symbol} at ${current_price:.2f} (P&L: ${pnl:.2f}, {pnl_pct:.2f}%)")
                
                # Check for entry signals (if we don't have a position)
                if symbol not in positions:
                    # Check for entry signal
                    should_entry, entry_reason = strategy_instance.should_entry(data, i)
                    
                    if should_entry:
                        # Execute buy (allocate 10% of capital per position)
                        position_size = initial_capital * 0.1
                        if current_capital >= position_size:
                            # Calculate shares and round to whole number
                            shares = int(position_size / current_price)
                            
                            # Only trade if we can buy at least 1 share
                            if shares >= 1:
                                # Calculate actual position size based on whole shares
                                actual_position_size = shares * current_price
                                
                                positions[symbol] = {
                                    'shares': shares,
                                    'entry_price': float(current_price),
                                    'entry_date': str(current_date)
                                }
                                current_capital -= actual_position_size
                                
                                trades.append({
                                    'date': str(current_date),
                                    'symbol': symbol,
                                    'action': 'BUY',
                                    'shares': shares,
                                    'price': float(current_price),
                                    'value': float(actual_position_size),
                                    'strategy': f"{strategy}_{profile}",
                                    'reason': entry_reason.get('summary', 'Entry signal'),
                                    'pnl': 0.0,
                                    'pnl_percent': 0.0
                                })
                                
                                self.logger.info(f"BUY {shares} shares of {symbol} at ${current_price:.2f}")
                            else:
                                self.logger.info(f"⚠️  Skipping {symbol} - insufficient funds for minimum position")
                
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
                portfolio_values, trades, initial_capital, benchmark_data
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
    
    def _run_progressive_simulation(self, stock_data: Dict[str, pd.DataFrame], strategy: str, profile: str,
                                    benchmark_data: pd.DataFrame = None,
                                    start_date: str = None, end_date: str = None,
                                    backtest_id: str = None) -> Dict[str, Any]:
        """
        Run progressive historical backtest simulation with transaction logging.
        """
        self.logger.info(f"Starting progressive simulation for {strategy}_{profile}")
        
        # Get trading dates
        trading_dates = self._get_trading_dates(start_date, end_date)
        if not trading_dates:
            return {'error': 'No trading dates available'}
        
        # Initialize portfolio tracking
        initial_capital = 100000.0
        portfolio_value = initial_capital
        portfolio_values = []
        trades = []
        positions = {}
        industry_groups = {}
        
        self.logger.info(f"Processing {len(trading_dates)} trading days")
        
        # Progressive day-by-day simulation
        for i, current_date in enumerate(trading_dates):
            try:
                self.logger.info(f"🔄 Processing day {i+1}/{len(trading_dates)}: {current_date}")
                
                # Calculate daily stock scoring
                daily_scoring = self._calculate_daily_stock_scoring(
                    stock_data, current_date, strategy, profile, industry_groups
                )
                
                if not daily_scoring:
                    continue
                
                # Get strategy instance
                strategy_instance = self._get_strategy_instance(strategy, profile)
                
                # Process trading signals for each stock
                for symbol in daily_scoring:
                    try:
                        if symbol not in stock_data:
                            continue
                        
                        data = stock_data[symbol]
                        
                        # Ensure timezone-naive timestamps
                        if data.index.tz is not None:
                            data.index = data.index.tz_localize(None)
                        
                        # Find the correct index for the current date
                        current_date_dt = pd.to_datetime(current_date)
                        try:
                            # Find the index where the date matches current_date
                            current_index = data.index.get_loc(current_date_dt)
                        except KeyError:
                            # If exact date not found, find the closest date
                            current_index = data.index.get_indexer([current_date_dt], method='ffill')[0]
                            if current_index == -1:
                                # If no valid index found, skip this stock
                                continue
                        
                        # Check for entry signal
                        should_entry, entry_reason = strategy_instance.should_entry(data, current_index)
                        
                        # Only attempt BUY if we have sufficient portfolio value
                        if should_entry and portfolio_value > 1000:  # Minimum portfolio value to trade
                            # Calculate position size (2% of portfolio per trade, but with minimum)
                            current_price = data.iloc[current_index]['close']
                            position_size = max(portfolio_value * 0.02, 1000)  # Minimum $1000 per trade
                            
                            # Ensure we don't exceed available portfolio value
                            if position_size > portfolio_value:
                                position_size = portfolio_value * 0.95  # Use 95% of remaining value
                            
                            # Calculate shares and ensure whole shares only
                            shares = int(position_size / current_price)  # Convert to whole shares
                            if shares < 1:
                                shares = 1  # Minimum 1 share
                            
                            # Only trade if we can buy at least 1 share
                            if shares >= 1:
                                # Calculate actual position size based on whole shares
                                actual_position_size = shares * current_price
                                
                                # Record the trade
                                trade = {
                                    'date': current_date,
                                    'symbol': symbol,
                                    'action': 'BUY',
                                    'shares': shares,
                                    'price': current_price,
                                    'value': actual_position_size,
                                    'reason': entry_reason.get('summary', 'Strategy Entry'),
                                    'portfolio_value': portfolio_value,
                                    'strategy': strategy,
                                    'profile': profile,
                                    'pnl': 0.0,  # BUY trades have no P&L initially
                                    'pnl_percent': 0.0
                                }
                                trades.append(trade)
                                
                                # Store trade in database
                                trade_data = {
                                    'ticker': symbol,
                                    'strategy': strategy,
                                    'entry_date': current_date,
                                    'exit_date': None,
                                    'entry_price': current_price,
                                    'exit_price': None,
                                    'shares': shares,
                                    'pnl_pct': 0.0,
                                    'pnl_dollars': 0.0,
                                    'entry_reason': entry_reason.get('summary', 'Strategy Entry'),
                                    'exit_reason': None,
                                    'what_learned': '',
                                    'status': 'open'
                                }
                                trade_id = self.data_engine.store_trade(trade_data)
                                
                                # Enhanced transaction logging
                                self.logger.info(f"💾 Stored trade {trade_id} for {symbol}")
                                self.logger.info(f"   📊 Trade Details:")
                                self.logger.info(f"      - Date: {current_date}")
                                self.logger.info(f"      - Symbol: {symbol}")
                                self.logger.info(f"      - Action: BUY")
                                self.logger.info(f"      - Shares: {shares}")
                                self.logger.info(f"      - Price: ${current_price:.2f}")
                                self.logger.info(f"      - Value: ${actual_position_size:.2f}")
                                self.logger.info(f"      - Strategy: {strategy}")
                                self.logger.info(f"      - Profile: {profile}")
                                self.logger.info(f"      - Reason: {entry_reason.get('summary', 'Strategy Entry')}")
                                self.logger.info(f"      - Portfolio Value: ${portfolio_value:.2f}")
                                self.logger.info(f"      - Trade ID: {trade_id}")
                                
                                # Emit WebSocket event for real-time dashboard update
                                try:
                                    from flask_socketio import SocketIO
                                    socketio = SocketIO()
                                    socketio.emit('new_trade', {
                                        'trade_id': trade_id,
                                        'symbol': symbol,
                                        'action': 'BUY',
                                        'price': current_price,
                                        'shares': shares,
                                        'strategy': strategy
                                    })
                                except Exception as e:
                                    self.logger.warning(f"Could not emit WebSocket event: {e}")
                                
                                # Log transaction
                                if backtest_id:
                                    self.data_cache.log_transaction(backtest_id, trade)
                                
                                # Update portfolio value
                                portfolio_value -= actual_position_size
                                
                                # Track position for exit logic - accumulate shares for same symbol
                                if symbol in positions:
                                    # Add to existing position
                                    existing_position = positions[symbol]
                                    total_shares = existing_position['shares'] + shares
                                    total_cost = (existing_position['shares'] * existing_position['entry_price']) + (shares * current_price)
                                    avg_entry_price = total_cost / total_shares
                                    
                                    positions[symbol] = {
                                        'shares': total_shares,
                                        'entry_price': avg_entry_price,
                                        'entry_date': current_date  # Update to latest entry date
                                    }
                                else:
                                    # Create new position
                                    positions[symbol] = {
                                        'shares': shares,
                                        'entry_price': current_price,
                                        'entry_date': current_date
                                    }
                                
                                # Log the trade
                                if symbol in positions:
                                    # This was an addition to existing position
                                    self.logger.info(f"📈 BUY {shares} shares of {symbol} at ${current_price:.2f} (Total: {positions[symbol]['shares']} shares)")
                                    self.logger.info(f"   Reason: {entry_reason.get('summary', 'Strategy Entry')}")
                                    self.logger.info(f"   Portfolio value: ${portfolio_value:.2f}")
                                else:
                                    # This was a new position
                                    self.logger.info(f"📈 BUY {shares} shares of {symbol} at ${current_price:.2f}")
                                    self.logger.info(f"   Reason: {entry_reason.get('summary', 'Strategy Entry')}")
                                    self.logger.info(f"   Portfolio value: ${portfolio_value:.2f}")
                            else:
                                self.logger.info(f"⚠️  Skipping {symbol} - insufficient funds for minimum position (${position_size:.2f} needed)")
                        elif should_entry and portfolio_value <= 1000:
                            self.logger.info(f"⏸️  Skipping BUY for {symbol} - portfolio value too low (${portfolio_value:.2f})")
                        
                        # Check for exit signal (if we have a position) - ALWAYS check regardless of portfolio value
                        if symbol in positions:
                            position = positions[symbol]
                            
                            # Add minimum hold period to prevent immediate exit
                            from datetime import datetime, timedelta
                            try:
                                entry_dt = datetime.strptime(position['entry_date'], '%Y-%m-%d')
                                current_dt = datetime.strptime(current_date, '%Y-%m-%d')
                                days_held = (current_dt - entry_dt).days
                                
                                # Minimum hold period: 3 days to prevent immediate exits
                                min_hold_days = 3
                                if days_held < min_hold_days:
                                    self.logger.info(f"⏳ Holding {symbol} - minimum hold period not met ({days_held} < {min_hold_days} days)")
                                    continue
                                    
                            except Exception as e:
                                self.logger.warning(f"Error calculating hold period for {symbol}: {e}")
                                # Continue with exit check if date parsing fails
                            
                            should_exit, exit_reason = strategy_instance.should_exit(
                                data, current_index, 
                                position['entry_price'], position['entry_date']
                            )
                            

                            
                            if should_exit:
                                # Calculate exit details - sell ENTIRE position
                                current_price = data.iloc[current_index]['close']
                                total_shares = position['shares']  # Total accumulated shares
                                avg_entry_price = position['entry_price']  # Weighted average entry price
                                exit_value = total_shares * current_price
                                
                                # Calculate P&L for entire position
                                pnl = exit_value - (total_shares * avg_entry_price)
                                pnl_percent = (pnl / (total_shares * avg_entry_price)) * 100 if avg_entry_price > 0 else 0
                                
                                # Only execute if we have shares to sell
                                if total_shares > 0:
                                    # Record the exit trade - sell entire accumulated position
                                    trade = {
                                        'date': current_date,
                                        'symbol': symbol,
                                        'action': 'SELL',
                                        'shares': total_shares,  # Total accumulated shares
                                        'price': current_price,
                                        'value': exit_value,
                                        'reason': exit_reason.get('summary', 'Strategy Exit'),
                                        'portfolio_value': portfolio_value,
                                        'strategy': strategy,
                                        'profile': profile,
                                        'entry_price': avg_entry_price,  # Weighted average entry price
                                        'pnl': pnl,
                                        'pnl_percent': pnl_percent
                                    }
                                    trades.append(trade)
                                    
                                    # Store completed trade in database (update existing open trade)
                                    trade_data = {
                                        'ticker': symbol,
                                        'strategy': strategy,
                                        'entry_date': position['entry_date'],
                                        'exit_date': current_date,
                                        'entry_price': avg_entry_price,
                                        'exit_price': current_price,
                                        'shares': total_shares,
                                        'pnl_pct': pnl_percent,
                                        'pnl_dollars': pnl,
                                        'entry_reason': 'Strategy Entry',
                                        'exit_reason': exit_reason.get('summary', 'Strategy Exit'),
                                        'what_learned': '',
                                        'status': 'closed'
                                    }
                                    trade_id = self.data_engine.store_trade(trade_data)
                                    
                                    # Enhanced transaction logging for SELL trades
                                    self.logger.info(f"💾 Stored completed trade {trade_id} for {symbol}")
                                    self.logger.info(f"   📊 Trade Details:")
                                    self.logger.info(f"      - Entry Date: {position['entry_date']}")
                                    self.logger.info(f"      - Exit Date: {current_date}")
                                    self.logger.info(f"      - Symbol: {symbol}")
                                    self.logger.info(f"      - Action: SELL")
                                    self.logger.info(f"      - Shares: {total_shares}")
                                    self.logger.info(f"      - Entry Price: ${avg_entry_price:.2f}")
                                    self.logger.info(f"      - Exit Price: ${current_price:.2f}")
                                    self.logger.info(f"      - Exit Value: ${exit_value:.2f}")
                                    self.logger.info(f"      - P&L: ${pnl:.2f} ({pnl_percent:.2f}%)")
                                    self.logger.info(f"      - Strategy: {strategy}")
                                    self.logger.info(f"      - Profile: {profile}")
                                    self.logger.info(f"      - Exit Reason: {exit_reason.get('summary', 'Strategy Exit')}")
                                    self.logger.info(f"      - Portfolio Value: ${portfolio_value:.2f}")
                                    self.logger.info(f"      - Trade ID: {trade_id}")
                                    
                                    # Emit WebSocket event for real-time dashboard update
                                    try:
                                        from flask_socketio import SocketIO
                                        socketio = SocketIO()
                                        socketio.emit('trade_closed', {
                                            'trade_id': trade_id,
                                            'symbol': symbol,
                                            'action': 'SELL',
                                            'price': current_price,
                                            'shares': total_shares,
                                            'pnl': pnl,
                                            'pnl_percent': pnl_percent,
                                            'strategy': strategy
                                        })
                                    except Exception as e:
                                        self.logger.warning(f"Could not emit WebSocket event: {e}")
                                    
                                    # Log transaction
                                    if backtest_id:
                                        self.data_cache.log_transaction(backtest_id, trade)
                                    
                                    # Update portfolio value (this can recover from $0.00)
                                    portfolio_value += exit_value
                                    
                                    # Remove position
                                    del positions[symbol]
                                    
                                    self.logger.info(f"📉 SELL {total_shares} shares of {symbol} at ${current_price:.2f}")
                                    self.logger.info(f"   Average entry price: ${avg_entry_price:.2f}")
                                    self.logger.info(f"   Reason: {exit_reason.get('summary', 'Strategy Exit')}")
                                    self.logger.info(f"   P&L: ${pnl:.2f} ({pnl_percent:.2f}%)")
                                    self.logger.info(f"   Portfolio value: ${portfolio_value:.2f}")
                                    
                                    # If portfolio recovered, log it
                                    if portfolio_value > 1000:
                                        self.logger.info(f"🔄 Portfolio recovered to ${portfolio_value:.2f} - BUY trades can resume")
                                else:
                                    self.logger.warning(f"⚠️  Cannot sell {symbol} - no shares to sell")
                    
                    except Exception as e:
                        self.logger.error(f"Error processing {symbol} on {current_date}: {str(e)}")
                        continue
                
                # Record portfolio value for this day
                portfolio_values.append({
                    'date': current_date,
                    'value': portfolio_value,
                    'cash': portfolio_value,
                    'positions': len(positions)
                })
                
                # Log progress every 50 days
                if (i + 1) % 50 == 0:
                    self.logger.info(f"📊 Progress: {i+1}/{len(trading_dates)} days processed")
                    self.logger.info(f"   Portfolio value: ${portfolio_value:.2f}")
                    self.logger.info(f"   Total trades: {len(trades)}")
            
            except Exception as e:
                self.logger.error(f"Error processing day {current_date}: {str(e)}")
                continue
        
        # Calculate performance metrics
        performance = self._calculate_performance_metrics(
            portfolio_values, trades, initial_capital, "SPY"  # Use SPY as default benchmark
        )
        
        self.logger.info(f"Progressive simulation completed")
        self.logger.info(f"Total trades: {len(trades)}")
        self.logger.info(f"Final portfolio value: ${portfolio_value:.2f}")
        
        # Add comprehensive trade summary
        if trades:
            self.logger.info(f"📋 TRADE SUMMARY:")
            self.logger.info(f"   Total trades executed: {len(trades)}")
            
            # Group trades by symbol
            trades_by_symbol = {}
            for trade in trades:
                symbol = trade['symbol']
                if symbol not in trades_by_symbol:
                    trades_by_symbol[symbol] = []
                trades_by_symbol[symbol].append(trade)
            
            # Log summary by symbol
            for symbol, symbol_trades in trades_by_symbol.items():
                buy_trades = [t for t in symbol_trades if t['action'] == 'BUY']
                sell_trades = [t for t in symbol_trades if t['action'] == 'SELL']
                
                self.logger.info(f"   📈 {symbol}:")
                self.logger.info(f"      - BUY trades: {len(buy_trades)}")
                self.logger.info(f"      - SELL trades: {len(sell_trades)}")
                
                if sell_trades:
                    total_pnl = sum(t['pnl'] for t in sell_trades)
                    avg_pnl_pct = sum(t['pnl_percent'] for t in sell_trades) / len(sell_trades)
                    self.logger.info(f"      - Total P&L: ${total_pnl:.2f}")
                    self.logger.info(f"      - Avg P&L %: {avg_pnl_pct:.2f}%")
                
                # Log individual trades for this symbol
                for i, trade in enumerate(symbol_trades, 1):
                    if trade['action'] == 'BUY':
                        self.logger.info(f"      {i}. BUY {trade['shares']} @ ${trade['price']:.2f} on {trade['date']}")
                    else:
                        self.logger.info(f"      {i}. SELL {trade['shares']} @ ${trade['price']:.2f} on {trade['date']} (P&L: ${trade['pnl']:.2f})")
        
        # Verify trades in database
        try:
            from ..data_engine.data_engine import DataEngine
            data_engine = DataEngine()
            db_trades = data_engine.get_trades(limit=100)
            self.logger.info(f"💾 Database verification:")
            self.logger.info(f"   - Trades in database: {len(db_trades)}")
            if db_trades:
                latest_trade = db_trades[0]
                self.logger.info(f"   - Latest trade: {latest_trade['ticker']} on {latest_trade['entry_date']}")
        except Exception as e:
            self.logger.warning(f"Could not verify database trades: {e}")
        
        return {
            'success': True,
            'performance': performance,
            'trades': trades,
            'portfolio_values': portfolio_values,
            'strategy': strategy,
            'profile': profile,
            'start_date': start_date,
            'end_date': end_date,
            'initial_capital': initial_capital,
            'final_portfolio_value': portfolio_value,
            'total_trades': len(trades),
            'total_return': ((portfolio_value - initial_capital) / initial_capital) * 100,
            'max_drawdown': performance.get('max_drawdown', 0),
            'sharpe_ratio': performance.get('sharpe_ratio', 0)
        }
    
    def _calculate_daily_stock_scoring(self, stock_data: Dict[str, pd.DataFrame], current_date: str,
                                      strategy: str, profile: str, industry_groups: Dict) -> List[str]:
        """
        Calculate daily stock scoring based on data available up to current_date.
        This ensures no look-ahead bias.
        """
        self.logger.info(f"Calculating daily stock scoring for {current_date}")
        
        # Normalize current_date to timezone-naive UTC
        current_date_dt = parse_date_string(current_date)
        
        # Get all available stocks up to current_date
        available_stocks = []
        for symbol, data in stock_data.items():
            try:
                # Normalize data dates to timezone-naive UTC
                data = normalize_index_dates(data.copy())
                
                # Filter data up to current date
                filtered_data = data[data.index <= current_date_dt]
                
                if len(filtered_data) < 50:  # Reverted back to original 50 data points requirement
                    continue
                
                # Calculate technical indicators
                indicators = self.trading_system.calculate_indicators(filtered_data)
                
                # Calculate stock score
                score = self._calculate_stock_score(indicators, strategy, profile)
                
                # Add industry classification
                industry = self._get_stock_industry(symbol)
                
                stock_scores.append({
                    'symbol': symbol,
                    'score': score,
                    'industry': industry,
                    'data_points': len(filtered_data)
                })
                
            except Exception as e:
                self.logger.warning(f"Error processing {symbol}: {e}")
                continue
        
        if not available_stocks:
            self.logger.warning(f"No stocks with sufficient data for {current_date}")
            return []
        
        # Calculate scores for each stock
        stock_scores = []
        for symbol in available_stocks:
            try:
                # Get data up to current_date only
                data = stock_data[symbol]
                
                # Normalize data dates to timezone-naive UTC
                data = normalize_index_dates(data.copy())
                
                # Filter data up to current date
                filtered_data = data[data.index <= current_date_dt]
                
                if len(filtered_data) < 20:  # Reduced minimum data requirement from 50 to 20
                    continue
                
                # Calculate technical indicators
                indicators = self.trading_system.calculate_indicators(filtered_data)
                
                # Calculate stock score
                score = self._calculate_stock_score(indicators, strategy, profile)
                
                # Add industry classification
                industry = self._get_stock_industry(symbol)
                
                stock_scores.append({
                    'symbol': symbol,
                    'score': score,
                    'industry': industry,
                    'data_points': len(filtered_data)
                })
                
            except Exception as e:
                self.logger.error(f"Error calculating score for {symbol}: {e}")
                continue
        
        if not stock_scores:
            self.logger.warning(f"No valid stock scores for {current_date}")
            return []
        
        # Sort by score (highest first)
        stock_scores.sort(key=lambda x: x['score'], reverse=True)
        
        # Log top 5 scoring stocks
        self.logger.info(f"Top 5 scoring stocks for {current_date}:")
        for i, stock in enumerate(stock_scores[:5]):
            self.logger.info(f"   {i+1}. {stock['symbol']}: score={stock['score']:.3f}, industry={stock['industry']}")
        
        # Select diversified stocks
        selected_stocks = self._select_diversified_stocks(stock_scores, max_stocks=20)
        
        # Log selected stocks
        self.logger.info(f"Selected {len(selected_stocks)} stocks for trading on {current_date}")
        for stock in selected_stocks[:5]:
            self.logger.info(f"   - {stock['symbol']}: {stock['score']:.3f}")
        
        return [stock['symbol'] for stock in selected_stocks]
    
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
                if 'macd_line' in latest and 'macd_signal' in latest:
                    macd = latest['macd_line']
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
    
    def _load_all_stock_data(self, start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """Load data for all available stocks in the specified period."""
        try:
            # Get all available stocks
            all_stocks = self.trading_system.get_all_stocks()
            self.logger.info(f"Loading data for {len(all_stocks)} stocks")
            
            stock_data = {}
            for symbol in all_stocks:
                try:
                    data = self.trading_system.prepare_data(symbol, start_date, end_date)
                    self.logger.info(f"Raw data for {symbol}: shape={data.shape}, empty={data.empty}")
                    if not data.empty and len(data) >= 2:  # Reduced from 10 to 2 to allow more stocks
                        stock_data[symbol] = data
                        self.logger.info(f"Loaded data for {symbol}: {len(data)} data points")
                    else:
                        self.logger.info(f"Skipping {symbol}: empty={data.empty}, len={len(data)}")
                except Exception as e:
                    self.logger.warning(f"Error loading data for {symbol}: {str(e)}")
                    continue
            
            self.logger.info(f"Successfully loaded data for {len(stock_data)} stocks")
            return stock_data
            
        except Exception as e:
            self.logger.error(f"Error loading stock data: {str(e)}")
            return {}
    
    def _get_trading_dates(self, start_date: str, end_date: str) -> List[str]:
        """Get all trading dates in the specified period."""
        try:
            # Use SPY data to get trading dates
            spy_data = self.trading_system.prepare_data("SPY", start_date, end_date)
            if spy_data.empty:
                self.logger.warning("No SPY data available for trading dates")
                return []
            
            # Check if the index is integer-based (not proper dates)
            if spy_data.index.dtype == 'int64' or isinstance(spy_data.index[0], (int, np.integer)):
                self.logger.warning("SPY data has integer index, creating date range manually")
                # Create a proper date range for the trading period
                start_dt = pd.to_datetime(start_date)
                end_dt = pd.to_datetime(end_date)
                
                # Generate business days (trading days)
                trading_dates = pd.bdate_range(start=start_dt, end=end_dt, freq='B')
                trading_dates = [str(date.date()) for date in trading_dates]
                
                self.logger.info(f"Generated {len(trading_dates)} trading dates manually")
                return trading_dates
            
            # Convert index to list of dates - handle different index types
            trading_dates = []
            for date in spy_data.index:
                try:
                    if hasattr(date, 'date'):
                        # If it's a datetime object
                        trading_dates.append(str(date.date()))
                    elif hasattr(date, 'strftime'):
                        # If it's a datetime-like object
                        trading_dates.append(str(date))
                    else:
                        # If it's a string or other format
                        trading_dates.append(str(date))
                except Exception as e:
                    self.logger.warning(f"Error converting date {date}: {str(e)}")
                    continue
            
            self.logger.info(f"Found {len(trading_dates)} trading dates")
            return trading_dates
            
        except Exception as e:
            self.logger.error(f"Error getting trading dates: {str(e)}")
            return []
    
    def _get_stock_industry(self, symbol: str) -> str:
        """Get the industry/sector for a stock symbol."""
        # Simple industry mapping - in a real system, this would come from a database
        industry_mapping = {
            'AAPL': 'Technology',
            'MSFT': 'Technology', 
            'GOOGL': 'Technology',
            'AMZN': 'Consumer Discretionary',
            'TSLA': 'Consumer Discretionary',
            'META': 'Technology',
            'NVDA': 'Technology',
            'NFLX': 'Communication Services',
            'CRM': 'Technology',
            'ADBE': 'Technology',
            'ORCL': 'Technology',
            'ZM': 'Technology',
            'SPY': 'ETF',
            'QQQ': 'ETF',
            'IWM': 'ETF'
        }
        return industry_mapping.get(symbol, 'Unknown')
    
    def _can_add_position(self, symbol: str, positions: Dict, industry_groups: Dict) -> bool:
        """Check if we can add a position based on diversification rules."""
        industry = self._get_stock_industry(symbol)
        
        # Check if we already have too many positions in this industry
        current_industry_count = industry_groups.get(industry, 0)
        max_per_industry = 3  # Maximum 3 positions per industry
        
        if current_industry_count >= max_per_industry:
            return False
        
        # Check total positions limit
        max_total_positions = 20  # Maximum 20 total positions
        
        if len(positions) >= max_total_positions:
            return False
        
        return True
    
    def _get_strategy_instance(self, strategy: str, profile: str):
        """Get a strategy instance with the specified profile."""
        self.logger.info(f"DEBUG: _get_strategy_instance called with strategy={strategy}, profile={profile}")
        
        if strategy == 'MACD':
            from src.strategies.macd_strategy import MACDStrategy
            strategy_instance = MACDStrategy(profile=profile)
            self.logger.info(f"DEBUG: Created MACDStrategy instance: {strategy_instance}")
            return strategy_instance
        elif strategy == 'MACD_ENHANCED':
            from src.strategies.macd_enhanced_strategy import MACDEnhancedStrategy
            strategy_instance = MACDEnhancedStrategy(profile=profile)
            self.logger.info(f"DEBUG: Created MACDEnhancedStrategy instance: {strategy_instance}")
            return strategy_instance
        else:
            # Default to MACD strategy
            from src.strategies.macd_strategy import MACDStrategy
            strategy_instance = MACDStrategy(profile=profile)
            self.logger.info(f"DEBUG: Created default MACDStrategy instance: {strategy_instance}")
            return strategy_instance
    
    def _calculate_performance_metrics(self, portfolio_values: List[Dict], trades: List[Dict], 
                                     initial_capital: float, benchmark: str) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics."""
        try:
            if not portfolio_values:
                return {
                    'total_trades': 0,
                    'strategy_return': 0.0,
                    'benchmark_return': 0.0,
                    'sharpe_ratio': 0.0,
                    'max_drawdown': 0.0,
                    'win_rate': 0.0,
                    'alpha': 0.0,
                    'final_value': initial_capital,
                    'volatility': 0.0,
                    'winning_trades': 0,
                    'average_trade_return': 0.0
                }
            
            # Calculate strategy return
            final_value = portfolio_values[-1]['value']
            strategy_return = ((final_value - initial_capital) / initial_capital) * 100
            
            # Calculate benchmark return
            benchmark_return = 0.0
            if benchmark and portfolio_values:
                try:
                    benchmark_data = self.trading_system.prepare_data(
                        benchmark, portfolio_values[0]['date'], portfolio_values[-1]['date']
                    )
                    if benchmark_data is not None and not benchmark_data.empty:
                        benchmark_start = benchmark_data.iloc[0]['close']
                        benchmark_end = benchmark_data.iloc[-1]['close']
                        benchmark_return = ((benchmark_end - benchmark_start) / benchmark_start) * 100
                except Exception as e:
                    self.logger.warning(f"Error calculating benchmark return: {str(e)}")
            
            # Calculate trade statistics
            total_trades = len(trades)
            winning_trades = len([t for t in trades if t.get('pnl', 0) > 0])
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
            
            # Calculate average trade return
            trade_returns = [t.get('pnl_percent', 0) for t in trades]
            average_trade_return = sum(trade_returns) / len(trade_returns) if trade_returns else 0.0
            
            # Calculate volatility (simplified)
            daily_returns = []
            for i in range(1, len(portfolio_values)):
                prev_value = portfolio_values[i-1]['value']
                curr_value = portfolio_values[i]['value']
                daily_return = ((curr_value - prev_value) / prev_value) * 100
                daily_returns.append(daily_return)
            
            volatility = np.std(daily_returns) if daily_returns else 0.0
            
            # Calculate Sharpe ratio (simplified)
            sharpe_ratio = (strategy_return / volatility) if volatility > 0 else 0.0
            
            # Calculate max drawdown
            max_drawdown = 0.0
            peak_value = initial_capital
            for pv in portfolio_values:
                current_value = pv['value']
                if current_value > peak_value:
                    peak_value = current_value
                drawdown = ((peak_value - current_value) / peak_value) * 100
                max_drawdown = max(max_drawdown, drawdown)
            
            # Calculate alpha
            alpha = strategy_return - benchmark_return
            
            return {
                'total_trades': total_trades,
                'strategy_return': round(strategy_return, 2),
                'benchmark_return': round(benchmark_return, 2),
                'sharpe_ratio': round(sharpe_ratio, 2),
                'max_drawdown': round(max_drawdown, 2),
                'win_rate': round(win_rate, 2),
                'alpha': round(alpha, 2),
                'final_value': round(final_value, 2),
                'volatility': round(volatility, 2),
                'winning_trades': winning_trades,
                'average_trade_return': round(average_trade_return, 2)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating performance metrics: {str(e)}")
            return {
                'total_trades': 0,
                'strategy_return': 0.0,
                'benchmark_return': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'win_rate': 0.0,
                'alpha': 0.0,
                'final_value': initial_capital,
                'volatility': 0.0,
                'winning_trades': 0,
                'average_trade_return': 0.0
            }
    
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

    def _get_available_symbols_for_period(self, start_date, end_date):
        """Get symbols that have sufficient data for the given period."""
        try:
            # Get all symbols from the data source
            symbols = self._get_all_symbols()
            available_symbols = []
            
            for symbol in symbols:
                try:
                    data = self._get_cached_or_fetch_data(symbol, start_date, end_date)
                    if data is not None and len(data) >= 50:  # 50 data points requirement
                        available_symbols.append(symbol)
                except Exception as e:
                    continue
            
            return available_symbols
        except Exception as e:
            print(f"❌ Error getting available symbols: {e}")
            return []
    
    def _get_available_stocks_for_date(self, current_date, available_symbols, data_start_date):
        """Get stocks available for trading on a specific date."""
        try:
            # For now, return all available symbols
            # In a more sophisticated implementation, you could filter based on
            # market conditions, volatility, etc.
            return available_symbols
        except Exception as e:
            print(f"❌ Error getting available stocks for {current_date}: {e}")
            return []
    
    def _get_stock_data_with_context(self, symbol, data_start_date, current_date):
        """Get stock data with extended historical context."""
        try:
            # Fetch data from data_start_date to current_date
            data = self._get_cached_or_fetch_data(symbol, data_start_date, current_date)
            return data
        except Exception as e:
            print(f"❌ Error getting data for {symbol}: {e}")
            return None
    
    def _calculate_indicators(self, data):
        """Calculate technical indicators for the given data."""
        try:
            return self.trading_system.calculate_indicators(data)
        except Exception as e:
            print(f"❌ Error calculating indicators: {e}")
            return {}
    
    def _check_entry_signal(self, symbol, indicators, current_date):
        """Check if we should enter a position."""
        try:
            # Use the trading system's strategy to check for entry signals
            # Get the current data index
            data_index = len(indicators) - 1  # Use the last row
            
            # Run the strategy signal check - use the strategy passed to the backtest
            signal_generated, signal_details = self.trading_system.run_strategy_signal(
                strategy_name=self.current_strategy,  # Use the strategy from backtest
                data=indicators,
                index=data_index
            )
            
            return signal_generated and signal_details.get('action') == 'BUY'
        except Exception as e:
            print(f"❌ Error checking entry signal for {symbol}: {e}")
            return False
    
    def _check_exit_signal(self, symbol, indicators, current_date, portfolio):
        """Check if we should exit a position."""
        try:
            # For now, use a simple exit condition
            # In a real implementation, you would check for exit signals from the strategy
            
            # Check if we have a position in this symbol
            if symbol not in portfolio['positions'] or portfolio['positions'][symbol]['shares'] == 0:
                return False
            
            # Simple exit condition: if price drops more than 5% from entry
            current_price = indicators.iloc[-1]['close']
            avg_entry_price = portfolio['positions'][symbol]['avg_price']
            
            if avg_entry_price > 0:
                price_change_pct = ((current_price - avg_entry_price) / avg_entry_price) * 100
                
                # Exit if loss is more than 5% or profit is more than 10%
                if price_change_pct <= -5 or price_change_pct >= 10:
                    return True
            
            return False
        except Exception as e:
            print(f"❌ Error checking exit signal for {symbol}: {e}")
            return False
    
    def _execute_buy_trade(self, symbol, data, current_date, portfolio, indicators):
        """Execute a buy trade."""
        try:
            current_price = data.iloc[-1]['close']
            shares = int(portfolio['cash'] * 0.1 / current_price)  # Use 10% of cash
            
            if shares > 0:
                cost = shares * current_price
                portfolio['cash'] -= cost
                
                if symbol not in portfolio['positions']:
                    portfolio['positions'][symbol] = {'shares': 0, 'avg_price': 0}
                
                # Update position
                total_shares = portfolio['positions'][symbol]['shares'] + shares
                total_cost = portfolio['positions'][symbol]['avg_price'] * portfolio['positions'][symbol]['shares'] + cost
                portfolio['positions'][symbol]['avg_price'] = total_cost / total_shares
                portfolio['positions'][symbol]['shares'] = total_shares
                
                # Record trade
                trade = {
                    'symbol': symbol,
                    'action': 'BUY',
                    'shares': shares,
                    'price': current_price,
                    'date': current_date,
                    'value': cost,
                    'reason': 'Strategy Entry'
                }
                portfolio['trades'].append(trade)
                
                print(f"      📈 BUY {shares} shares of {symbol} at ${current_price:.2f}")
        except Exception as e:
            print(f"❌ Error executing buy trade for {symbol}: {e}")
    
    def _execute_sell_trade(self, symbol, data, current_date, portfolio, indicators):
        """Execute a sell trade."""
        try:
            if symbol not in portfolio['positions'] or portfolio['positions'][symbol]['shares'] == 0:
                return
            
            current_price = data.iloc[-1]['close']
            shares = portfolio['positions'][symbol]['shares']
            avg_price = portfolio['positions'][symbol]['avg_price']
            
            proceeds = shares * current_price
            pnl = proceeds - (shares * avg_price)
            pnl_pct = (pnl / (shares * avg_price)) * 100
            
            portfolio['cash'] += proceeds
            portfolio['positions'][symbol]['shares'] = 0
            
            # Record trade
            trade = {
                'symbol': symbol,
                'action': 'SELL',
                'shares': shares,
                'price': current_price,
                'date': current_date,
                'value': proceeds,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'reason': 'Strategy Exit'
            }
            portfolio['trades'].append(trade)
            
            print(f"      📉 SELL {shares} shares of {symbol} at ${current_price:.2f} (P&L: ${pnl:.2f}, {pnl_pct:.2f}%)")
        except Exception as e:
            print(f"❌ Error executing sell trade for {symbol}: {e}")
    
    def _calculate_portfolio_value(self, portfolio, current_date):
        """Calculate current portfolio value."""
        try:
            total_value = portfolio['cash']
            
            for symbol, position in portfolio['positions'].items():
                if position['shares'] > 0:
                    # Get current price for the symbol
                    data = self._get_cached_or_fetch_data(symbol, current_date, current_date)
                    if data is not None and len(data) > 0:
                        current_price = data.iloc[-1]['close']
                        position_value = position['shares'] * current_price
                        total_value += position_value
            
            return total_value
        except Exception as e:
            print(f"❌ Error calculating portfolio value: {e}")
            return portfolio['cash']
    
    def _calculate_benchmark_return(self, benchmark, start_date, end_date):
        """Calculate benchmark return for the period."""
        try:
            benchmark_data = self._get_cached_or_fetch_data(benchmark, start_date, end_date)
            if benchmark_data is not None and len(benchmark_data) > 0:
                start_price = benchmark_data.iloc[0]['close']
                end_price = benchmark_data.iloc[-1]['close']
                return ((end_price - start_price) / start_price) * 100
            return 0
        except Exception as e:
            print(f"❌ Error calculating benchmark return: {e}")
            return 0
    
    def _get_all_symbols(self):
        """Get all available symbols."""
        try:
            # Return a list of symbols to test with
            return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMD', 'INTC']
        except Exception as e:
            print(f"❌ Error getting symbols: {e}")
            return [] 