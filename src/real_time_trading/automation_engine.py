"""
Automation Engine for Real-time Trading

Handles automated trading decisions, position management, and execution
using the centralized trading system.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import pytz
from enum import Enum

from ..utils.config_loader import ConfigLoader
from ..utils.logger import get_logger
from ..data_engine.data_engine import DataEngine
from ..strategies.base_strategy import BaseStrategy
from ..strategies.macd_strategy import MACDStrategy
from ..strategies.macd_canonical_strategy import MACDCanonicalStrategy
from .paper_trading import PaperTradingBroker
from .position_manager import PositionManager
from ..trading_system import get_trading_system


class TradingMode(Enum):
    """Trading modes for automation."""
    PAPER_TRADING = "paper_trading"
    SEMI_AUTO = "semi_auto"
    FULL_AUTO = "full_auto"
    MANUAL = "manual"


class AutomationEngine:
    """
    Main automation engine for automated trading decisions.
    
    Uses the centralized trading system for consistent strategy management
    and position tracking across all components.
    """
    
    def __init__(self, config: ConfigLoader, mode: TradingMode = TradingMode.PAPER_TRADING):
        self.config = config
        self.mode = mode
        self.data_engine = DataEngine()
        self.broker = PaperTradingBroker()
        
        # Initialize logger
        self.logger = get_logger(__name__)
        
        # Get centralized trading system
        self.trading_system = get_trading_system()
        
        # Analysis cache
        self.analysis_cache = {}
        self.cache_duration = timedelta(minutes=5)
        
        # Trading state
        self.is_running = False
        self.last_cycle_time = None
        self.cycle_count = 0
        
        # Performance tracking
        self.daily_pnl = 0.0
        self.total_pnl = 0.0
        self.trade_count = 0
        
        self.logger.info(f"Automation Engine initialized in {mode.value} mode")
    
    def start_automation(self) -> Dict[str, Any]:
        """Start the automation engine."""
        if self.is_running:
            return {'status': 'already_running', 'message': 'Automation is already running'}
        
        try:
            self.is_running = True
            self.last_cycle_time = datetime.now()
            self.cycle_count = 0
            
            # Start automation loop in background
            import threading
            self.automation_thread = threading.Thread(target=self._run_automation_loop)
            self.automation_thread.daemon = True
            self.automation_thread.start()
            
            logger.info("Automation engine started successfully")
            return {'status': 'started', 'message': 'Automation engine started successfully'}
            
        except Exception as e:
            self.is_running = False
            logger.error(f"Error starting automation: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def stop_automation(self) -> Dict[str, Any]:
        """Stop the automation engine."""
        if not self.is_running:
            return {'status': 'not_running', 'message': 'Automation is not running'}
        
        try:
            self.is_running = False
            logger.info("Automation engine stopped")
            return {'status': 'stopped', 'message': 'Automation engine stopped successfully'}
            
        except Exception as e:
            logger.error(f"Error stopping automation: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def run_single_cycle(self) -> Dict[str, Any]:
        """Run a single automation cycle."""
        try:
            if not self._is_market_open():
                return {'status': 'market_closed', 'message': 'Market is currently closed'}
            
            # Get selected stocks using centralized system
            selected_stocks = self.trading_system.select_stocks(
                max_stocks=self.config.get('automation.max_positions', 10),
                min_score=self.config.get('automation.min_confidence', 0.4)  # Lowered from 0.6 to 0.4
            )
            
            if not selected_stocks:
                return {'status': 'no_stocks', 'message': 'No stocks selected for trading'}
            
            # Analyze each stock
            analysis_results = []
            for symbol in selected_stocks:
                try:
                    result = self._analyze_stock(symbol)
                    if result:
                        analysis_results.append(result)
                except Exception as e:
                    logger.warning(f"Error analyzing {symbol}: {e}")
                    continue
            
            # Execute trades based on analysis
            trades_executed = self._execute_trades(analysis_results)
            
            self.cycle_count += 1
            self.last_cycle_time = datetime.now()
            
            return {
                'status': 'success',
                'message': f'Cycle completed. Analyzed {len(analysis_results)} stocks, executed {trades_executed} trades',
                'cycle_count': self.cycle_count,
                'stocks_analyzed': len(analysis_results),
                'trades_executed': trades_executed
            }
            
        except Exception as e:
            logger.error(f"Error in automation cycle: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _run_automation_loop(self):
        """Main automation loop."""
        cycle_interval = self.config.get('automation.cycle_interval', 300)  # 5 minutes
        
        while self.is_running:
            try:
                # Run single cycle
                result = self.run_single_cycle()
                logger.info(f"Automation cycle result: {result}")
                
                # Wait for next cycle
                import time
                time.sleep(cycle_interval)
                
            except Exception as e:
                logger.error(f"Error in automation loop: {e}")
                time.sleep(60)  # Wait 1 minute on error
    
    def _analyze_stock(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Analyze a single stock for trading opportunities.
        
        Args:
            symbol: Stock symbol to analyze
            
        Returns:
            Analysis result dictionary or None if no opportunity
        """
        try:
            # Check cache first
            cache_key = f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M')}"
            if cache_key in self.analysis_cache:
                cached_result = self.analysis_cache[cache_key]
                if datetime.now() - cached_result['timestamp'] < self.cache_duration:
                    return cached_result['data']
            
            # Get recent data
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            # Use centralized system to prepare data
            data = self.trading_system.prepare_data(symbol, start_date, end_date)
            if data.empty:
                return None
            
            # Check current position
            positions = self.trading_system.get_positions('automation')
            current_position = positions.get(symbol)
            
            # Analyze with each strategy
            strategies = ['MACDStrategy', 'MACDCanonicalStrategy']
            best_signal = None
            best_score = 0
            
            for strategy_name in strategies:
                try:
                    # Use centralized system for signal generation
                    signal_generated, signal_details = self.trading_system.run_strategy_signal(
                        strategy_name, data, len(data) - 1
                    )
                    
                    if signal_generated:
                        # Calculate confidence score
                        confidence = self._calculate_confidence(signal_details, data)
                        
                        if confidence > best_score:
                            best_score = confidence
                            best_signal = {
                                'symbol': symbol,
                                'strategy': strategy_name,
                                'action': signal_details['action'],
                                'confidence': confidence,
                                'reason': signal_details.get('reason', {}),
                                'current_price': data['close'].iloc[-1],
                                'timestamp': datetime.now()
                            }
                
                except Exception as e:
                    logger.warning(f"Error analyzing {symbol} with {strategy_name}: {e}")
                    continue
            
            # Cache result
            if best_signal:
                self.analysis_cache[cache_key] = {
                    'timestamp': datetime.now(),
                    'data': best_signal
                }
            
            return best_signal
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return None
    
    def _calculate_confidence(self, signal_details: Dict[str, Any], data: pd.DataFrame) -> float:
        """Calculate confidence score for a trading signal."""
        try:
            # Base confidence from signal strength
            base_confidence = 0.5
            
            # Add confidence based on signal type
            if signal_details['action'] == 'BUY':
                # Check for strong bullish signals
                if data['macd_crossover_up'].iloc[-1].item():
                    base_confidence += 0.2
                if 40 <= data['rsi'].iloc[-1].item() <= 60:
                    base_confidence += 0.1
                if data['price_above_ema_short'].iloc[-1].item():
                    base_confidence += 0.1
                if data['price_above_ema_long'].iloc[-1].item():
                    base_confidence += 0.1
            
            elif signal_details['action'] == 'SELL':
                # Check for strong bearish signals
                if data['macd_crossover_down'].iloc[-1].item():
                    base_confidence += 0.2
                if data['rsi'].iloc[-1].item() > 70 or data['rsi'].iloc[-1].item() < 30:
                    base_confidence += 0.1
            
            return min(base_confidence, 1.0)
            
        except Exception as e:
            logger.warning(f"Error calculating confidence: {e}")
            return 0.5
    
    def _execute_trades(self, analysis_results: List[Dict[str, Any]]) -> int:
        """Execute trades based on analysis results."""
        trades_executed = 0
        
        for result in analysis_results:
            try:
                symbol = result['symbol']
                action = result['action']
                confidence = result['confidence']
                current_price = result['current_price']
                
                # Check if we should execute this trade
                if confidence < self.config.get('automation.min_confidence', 0.6):
                    continue
                
                # Check position limits
                positions = self.trading_system.get_positions('automation')
                if len(positions) >= self.config.get('automation.max_positions', 10):
                    logger.info(f"Maximum positions reached, skipping {symbol}")
                    continue
                
                # Execute trade
                if action == 'BUY' and symbol not in positions:
                    # Calculate position size
                    account_value = self.broker.get_account_value()
                    max_position_value = account_value * self.config.get('automation.max_position_size', 0.1)
                    shares = max_position_value / current_price
                    
                    # Execute buy order
                    order_result = self.broker.place_order(symbol, 'buy', shares, current_price)
                    
                    if order_result['success']:
                        # Record position in centralized system
                        self.trading_system.add_position(
                            'automation', symbol, shares, current_price,
                            datetime.now().strftime('%Y-%m-%d'), result['strategy']
                        )
                        
                        trades_executed += 1
                        logger.info(f"Executed BUY order for {symbol}: {shares:.2f} shares at ${current_price:.2f}")
                
                elif action == 'SELL' and symbol in positions:
                    position = positions[symbol]
                    shares = position['shares']
                    
                    # Execute sell order
                    order_result = self.broker.place_order(symbol, 'sell', shares, current_price)
                    
                    if order_result['success']:
                        # Calculate PnL
                        entry_price = position['entry_price']
                        pnl = (current_price - entry_price) * shares
                        
                        # Close position in centralized system
                        self.trading_system.close_position(
                            'automation', symbol, current_price,
                            datetime.now().strftime('%Y-%m-%d'), pnl
                        )
                        
                        trades_executed += 1
                        logger.info(f"Executed SELL order for {symbol}: {shares:.2f} shares at ${current_price:.2f}, PnL: ${pnl:.2f}")
            
            except Exception as e:
                logger.error(f"Error executing trade for {result.get('symbol', 'Unknown')}: {e}")
                continue
        
        return trades_executed
    
    def _is_market_open(self) -> bool:
        """Check if the market is currently open."""
        if not self.config.get('automation.market_hours_only', True):
            return True
        
        try:
            # Get market hours configuration
            timezone = pytz.timezone(self.config.get('trading_hours.timezone', 'America/New_York'))
            now = datetime.now(timezone)
            
            # Check if it's a weekday
            if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
                return False
            
            # Check trading hours
            market_open = datetime.strptime(self.config.get('trading_hours.market_open', '09:30'), '%H:%M').time()
            market_close = datetime.strptime(self.config.get('trading_hours.market_close', '16:00'), '%H:%M').time()
            
            current_time = now.time()
            return market_open <= current_time <= market_close
            
        except Exception as e:
            logger.error(f"Error checking market hours: {e}")
            return True  # Default to open if error
    
    def get_status(self) -> Dict[str, Any]:
        """Get current automation status."""
        return {
            'is_running': self.is_running,
            'mode': self.mode.value,
            'last_cycle_time': self.last_cycle_time.isoformat() if self.last_cycle_time else None,
            'cycle_count': self.cycle_count,
            'daily_pnl': self.daily_pnl,
            'total_pnl': self.total_pnl,
            'trade_count': self.trade_count,
            'market_open': self._is_market_open()
        }
    
    def get_positions(self) -> Dict[str, Any]:
        """Get current automation positions."""
        return self.trading_system.get_positions('automation')
    
    def get_performance(self) -> Dict[str, Any]:
        """Get automation performance metrics."""
        return self.trading_system.get_performance_summary('automation')


class HistoricalBacktestEngine:
    """
    Engine for running automation strategies on historical data.
    Uses the centralized trading system for consistent behavior.
    """
    
    def __init__(self, config: dict, start_date: str, end_date: str, benchmark: str = "SPY"):
        self.config = config
        self.start_date = start_date
        self.end_date = end_date
        self.benchmark = benchmark
        self.logger = logging.getLogger(__name__)
        
        # Get centralized trading system
        self.trading_system = get_trading_system()
        
        # Results tracking
        self.trades = []
        self.portfolio_values = []
        self.benchmark_values = []
        
        # Debug: print initialization
        print(f"HistoricalBacktestEngine initialized: {start_date} to {end_date}, benchmark: {benchmark}")
    
    def run_backtest(self) -> Dict[str, Any]:
        """Run historical backtest using centralized trading system."""
        try:
            # Reset all strategies
            for strategy_name in self.trading_system.strategies.keys():
                self.trading_system.reset_strategy(strategy_name)
            
            # Get selected stocks for the period
            selected_stocks = self.trading_system.select_stocks(
                max_stocks=self.config.get('automation.max_positions', 10),
                min_score=self.config.get('automation.min_confidence', 0.4)  # Lowered from 0.6 to 0.4
            )
            
            if not selected_stocks:
                return {'error': 'No stocks selected for backtest'}
            
            # Prepare data for all selected stocks
            stock_data = {}
            for symbol in selected_stocks:
                data = self.trading_system.prepare_data(symbol, self.start_date, self.end_date)
                if not data.empty:
                    stock_data[symbol] = data
            
            if not stock_data:
                return {'error': 'No data available for selected stocks'}
            
            # Get benchmark data
            benchmark_data = None
            if self.benchmark:
                benchmark_data = self.trading_system.prepare_data(self.benchmark, self.start_date, self.end_date)
            
            # Run simulation
            results = self._run_simulation(stock_data, benchmark_data)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in historical backtest: {e}")
            return {'error': str(e)}
    
    def _run_simulation(self, stock_data: Dict[str, pd.DataFrame], 
                       benchmark_data: pd.DataFrame = None) -> Dict[str, Any]:
        """Run the historical simulation."""
        # Initialize tracking
        capital = self.config.get('automation.paper_trading.initial_capital', 100000)
        positions = {}
        trades = []
        portfolio_values = []
        benchmark_values = []
        
        # Get all dates from the data
        all_dates = set()
        for data in stock_data.values():
            all_dates.update(data.index)
        all_dates = sorted(all_dates)
        
        # Track benchmark
        benchmark_shares = 0
        if benchmark_data is not None:
            # Use lowercase column names
            close_col = 'close'
            benchmark_shares = capital / benchmark_data[close_col].iloc[0]
        
        # Simulate trading day by day
        for date in all_dates:
            # Update portfolio value
            portfolio_value = capital
            for symbol, position in positions.items():
                if symbol in stock_data and date in stock_data[symbol].index:
                    # Use lowercase column names
                    close_col = 'close'
                    current_price = stock_data[symbol].loc[date, close_col]
                    portfolio_value += position['shares'] * current_price
            
            portfolio_values.append({
                'date': str(date),  # Convert to string for JSON serialization
                'value': float(portfolio_value)  # Ensure float type
            })
            
            # Update benchmark value
            if benchmark_data is not None and date in benchmark_data.index:
                # Use lowercase column names
                close_col = 'close'
                benchmark_price = benchmark_data.loc[date, close_col]
                benchmark_value = benchmark_shares * benchmark_price
                benchmark_values.append({
                    'date': str(date),  # Convert to string for JSON serialization
                    'value': float(benchmark_value)  # Ensure float type
                })
            
            # Check for trading signals for each stock
            for symbol, data in stock_data.items():
                if date not in data.index:
                    continue
                
                current_index = data.index.get_loc(date)
                
                # Check if we have a position in this stock
                has_position = symbol in positions
                
                # Get signal from centralized system
                signal_generated, signal_details = self.trading_system.run_strategy_signal(
                    'MACDStrategy', data, current_index
                )
                
                if signal_generated:
                    if signal_details['action'] == 'BUY' and not has_position:
                        # Check position limits
                        if len(positions) >= self.config.get('automation.max_positions', 10):
                            continue
                        
                        # Calculate position size
                        # Use lowercase column names
                        close_col = 'close'
                        current_price = data.loc[date, close_col]
                        max_position_value = capital * self.config.get('automation.max_position_size', 0.1)
                        shares = max_position_value / current_price
                        
                        # Record position
                        positions[symbol] = {
                            'shares': float(shares),  # Ensure float type
                            'entry_price': float(current_price),  # Ensure float type
                            'entry_date': str(date),  # Convert to string
                            'strategy': 'MACDStrategy'
                        }
                        
                        trades.append({
                            'date': str(date),  # Convert to string for JSON serialization
                            'symbol': symbol,
                            'action': 'BUY',
                            'shares': float(shares),  # Ensure float type
                            'price': float(current_price),  # Ensure float type
                            'value': float(shares * current_price),  # Ensure float type
                            'reason': str(signal_details.get('reason', {}).get('summary', 'Strategy Entry'))  # Ensure string
                        })
                        
                        # Enhanced logging with date
                        date_str = str(date)
                        self.logger.info(f"BUY [{date_str}]: {shares:.6f} shares of {symbol} at ${current_price:.2f} - {signal_details.get('reason', {}).get('summary', 'Strategy Entry')}")
                    
                    elif signal_details['action'] == 'SELL' and has_position:
                        # Close position
                        position = positions[symbol]
                        # Use lowercase column names
                        close_col = 'close'
                        current_price = data.loc[date, close_col]
                        
                        # Calculate PnL
                        entry_value = position['shares'] * position['entry_price']
                        exit_value = position['shares'] * current_price
                        pnl = exit_value - entry_value
                        pnl_pct = (pnl / entry_value) * 100
                        
                        trades.append({
                            'date': str(date),  # Convert to string for JSON serialization
                            'symbol': symbol,
                            'action': 'SELL',
                            'shares': float(position['shares']),  # Ensure float type
                            'price': float(current_price),  # Ensure float type
                            'value': float(exit_value),  # Ensure float type
                            'pnl': float(pnl),  # Ensure float type
                            'pnl_pct': float(pnl_pct),  # Ensure float type
                            'reason': str(signal_details.get('reason', {}).get('summary', 'Strategy Exit'))  # Ensure string
                        })
                        
                        # Enhanced logging with date
                        date_str = str(date)
                        self.logger.info(f"SELL [{date_str}]: {position['shares']:.6f} shares of {symbol} at ${current_price:.2f} - PnL: {pnl_pct:.2f}% - {signal_details.get('reason', {}).get('summary', 'Strategy Exit')}")
                        
                        # Remove position
                        del positions[symbol]
        
        # Calculate final portfolio value
        final_value = portfolio_values[-1]['value'] if portfolio_values else capital
        total_return = ((final_value - capital) / capital) * 100
        
        # Calculate benchmark return
        benchmark_return = 0
        if benchmark_values:
            benchmark_final_value = benchmark_values[-1]['value']
            benchmark_return = ((benchmark_final_value - capital) / capital) * 100
        
        # Calculate additional metrics
        winning_trades = len([t for t in trades if t['action'] == 'SELL' and t.get('pnl_pct', 0) > 0])
        losing_trades = len([t for t in trades if t['action'] == 'SELL' and t.get('pnl_pct', 0) <= 0])
        
        return {
            'trades': trades,
            'portfolio_values': portfolio_values,
            'benchmark_values': benchmark_values,
            'total_return': float(total_return),  # Ensure float type
            'benchmark_return': float(benchmark_return),  # Ensure float type
            'total_trades': int(len(trades)),  # Ensure int type
            'winning_trades': int(winning_trades),  # Ensure int type
            'losing_trades': int(losing_trades),  # Ensure int type
            'initial_capital': float(capital),  # Ensure float type
            'final_value': float(final_value)  # Ensure float type
        } 