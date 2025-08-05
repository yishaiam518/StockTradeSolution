"""
Enhanced Backtesting Engine with Performance Analytics and Risk Management
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import logging
from dataclasses import dataclass
from datetime import datetime
import time

from .performance_analytics import PerformanceAnalytics, PerformanceMetrics
from .risk_management import RiskManager, RiskParameters, PositionSizingMethod, StopLossType

@dataclass
class PositionType:
    """Position type enumeration"""
    LONG = "long"
    SHORT = "short"

@dataclass
class OrderType:
    """Order type enumeration"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"

@dataclass
class Trade:
    """Trade information"""
    symbol: str
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    position_type: str
    shares: float
    pnl: float
    pnl_percentage: float
    stop_loss: float
    take_profit: float
    exit_reason: str

@dataclass
class Position:
    """Position information"""
    symbol: str
    position_type: str
    shares: float
    entry_price: float
    entry_time: datetime
    current_price: float
    unrealized_pnl: float
    stop_loss: float
    take_profit: float

class Strategy:
    """Abstract base class for trading strategies"""
    
    def __init__(self, name: str, parameters: Dict[str, Any]):
        self.name = name
        self.parameters = parameters
        self.logger = logging.getLogger(__name__)
    
    def should_enter_long(self, data: pd.DataFrame, index: int) -> bool:
        """Check if should enter long position"""
        raise NotImplementedError
    
    def should_exit_long(self, data: pd.DataFrame, index: int) -> bool:
        """Check if should exit long position"""
        raise NotImplementedError
    
    def should_enter_short(self, data: pd.DataFrame, index: int) -> bool:
        """Check if should enter short position"""
        raise NotImplementedError
    
    def should_exit_short(self, data: pd.DataFrame, index: int) -> bool:
        """Check if should exit short position"""
        raise NotImplementedError
    
    def get_position_size(self, data: pd.DataFrame, index: int, capital: float) -> float:
        """Calculate position size"""
        return capital * self.parameters.get('position_size', 0.1)

class BacktestEngine:
    """Enhanced backtesting engine with performance analytics and risk management"""
    
    def __init__(self, initial_capital: float = 100000.0, risk_params: Optional[RiskParameters] = None):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.equity_curve: List[float] = []
        self.timestamps: List[datetime] = []
        
        # Performance analytics
        self.performance_analytics = PerformanceAnalytics()
        
        # Risk management
        if risk_params is None:
            risk_params = RiskParameters(
                position_sizing_method=PositionSizingMethod.FIXED_PERCENTAGE,
                stop_loss_type=StopLossType.FIXED_PERCENTAGE
            )
        self.risk_manager = RiskManager(risk_params)
        
        # Data management
        from ..data_collection.data_manager import DataCollectionManager
        self.data_manager = DataCollectionManager()
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Enhanced Backtest Engine initialized with performance analytics and risk management")
    
    def load_data(self, collection_id: str, symbol: str) -> pd.DataFrame:
        """Load historical data with indicators"""
        try:
            # Get base data
            data = self.data_manager.get_symbol_data(collection_id, symbol)
            if data is None or data.empty:
                self.logger.error(f"No data found for {symbol} in collection {collection_id}")
                return pd.DataFrame()
            
            # Get indicators data
            indicators_data = self.data_manager.get_symbol_indicators(collection_id, symbol)
            if indicators_data is not None and not indicators_data.empty:
                # Merge indicators with base data
                data = data.merge(indicators_data, on='Date', how='left')
                self.logger.info(f"Loaded {len(data)} data points with indicators for {symbol}")
            else:
                self.logger.warning(f"No indicators found for {symbol}, using base data only")
            
            # Ensure we have required columns
            required_columns = ['Date', 'close']
            for col in required_columns:
                if col not in data.columns:
                    self.logger.error(f"Missing required column: {col}")
                    return pd.DataFrame()
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error loading data: {e}")
            return pd.DataFrame()
    
    def run_backtest(self, 
                    strategy: Strategy,
                    collection_id: str,
                    symbol: str,
                    start_date: Optional[str] = None,
                    end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Run backtest with enhanced performance analytics and risk management
        
        Args:
            strategy: Trading strategy to test
            collection_id: Data collection ID
            symbol: Symbol to trade
            start_date: Start date for backtest
            end_date: End date for backtest
            
        Returns:
            Dictionary with backtest results and performance metrics
        """
        try:
            # Load data
            data = self.load_data(collection_id, symbol)
            if data.empty:
                return {"error": "No data available for backtest"}
            
            # Filter by date range
            if start_date:
                data = data[data['Date'] >= start_date]
            if end_date:
                data = data[data['Date'] <= end_date]
            
            if data.empty:
                return {"error": "No data in specified date range"}
            
            self.logger.info(f"Running backtest on {len(data)} data points")
            
            # Reset state
            self.capital = self.initial_capital
            self.positions = {}
            self.trades = []
            self.equity_curve = [self.initial_capital]
            self.timestamps = [data.iloc[0]['Date']]
            
            # Run simulation
            for i in range(len(data)):
                current_row = data.iloc[i]
                current_time = current_row['Date']
                current_price = current_row['close']
                
                # Update equity curve
                self._update_equity_curve(current_price, current_time)
                
                # Check for exit signals (risk management)
                self._check_exit_signals(strategy, data, i, current_row)
                
                # Check for entry signals
                self._check_entry_signals(strategy, data, i, current_row)
                
                # Update position values
                self._update_positions(current_price, current_time)
            
            # Close any remaining positions
            self._close_all_positions(data.iloc[-1]['close'], data.iloc[-1]['Date'])
            
            # Calculate performance metrics
            equity_series = pd.Series(self.equity_curve, index=self.timestamps)
            performance_metrics = self.performance_analytics.calculate_performance_metrics(
                equity_series, self.trades
            )
            
            # Generate results
            results = {
                "strategy": strategy.name,
                "symbol": symbol,
                "initial_capital": self.initial_capital,
                "final_capital": self.capital,
                "total_return": performance_metrics.total_return,
                "trades": len(self.trades),
                "performance": {
                    "sharpe_ratio": performance_metrics.sharpe_ratio,
                    "sortino_ratio": performance_metrics.sortino_ratio,
                    "calmar_ratio": performance_metrics.calmar_ratio,
                    "max_drawdown": performance_metrics.max_drawdown,
                    "win_rate": performance_metrics.win_rate,
                    "profit_factor": performance_metrics.profit_factor,
                    "volatility": performance_metrics.volatility,
                    "information_ratio": performance_metrics.information_ratio,
                    "omega_ratio": performance_metrics.omega_ratio,
                    "treynor_ratio": performance_metrics.treynor_ratio,
                    "var_95": performance_metrics.var_95,
                    "cvar_95": performance_metrics.cvar_95,
                    "winning_trades": performance_metrics.winning_trades,
                    "losing_trades": performance_metrics.losing_trades,
                    "average_win": performance_metrics.average_win,
                    "average_loss": performance_metrics.average_loss,
                    "largest_win": performance_metrics.largest_win,
                    "largest_loss": performance_metrics.largest_loss,
                    "best_month": performance_metrics.best_month,
                    "worst_month": performance_metrics.worst_month,
                    "positive_months": performance_metrics.positive_months,
                    "negative_months": performance_metrics.negative_months
                },
                "equity_curve": self.equity_curve,
                "trades": self.trades,
                "risk_summary": self.risk_manager.get_risk_summary()
            }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in backtest: {e}")
            return {"error": str(e)}
    
    def _check_entry_signals(self, strategy: Strategy, data: pd.DataFrame, index: int, current_row: pd.Series):
        """Check for entry signals with risk management"""
        symbol = current_row.get('symbol', 'UNKNOWN')
        current_price = current_row['close']
        current_time = current_row['Date']
        
        # Check if we can enter new positions (risk limits)
        portfolio_ok, reason = self.risk_manager.check_portfolio_limits(
            self.capital, self.positions
        )
        
        if not portfolio_ok:
            self.logger.info(f"Portfolio limits exceeded: {reason}")
            return
        
        # Check for long entry
        if symbol not in self.positions and strategy.should_enter_long(data, index):
            # Calculate position size with risk management
            position_size = self.risk_manager.calculate_position_size(
                self.capital, current_price
            )
            
            if position_size > 0:
                shares = position_size / current_price
                stop_loss = self.risk_manager.calculate_stop_loss(
                    current_price, 'long'
                )
                take_profit = self.risk_manager.calculate_take_profit(
                    current_price, 'long'
                )
                
                self._enter_position(symbol, 'long', shares, current_price, 
                                  current_time, stop_loss, take_profit)
        
        # Check for short entry
        elif symbol not in self.positions and strategy.should_enter_short(data, index):
            position_size = self.risk_manager.calculate_position_size(
                self.capital, current_price
            )
            
            if position_size > 0:
                shares = position_size / current_price
                stop_loss = self.risk_manager.calculate_stop_loss(
                    current_price, 'short'
                )
                take_profit = self.risk_manager.calculate_take_profit(
                    current_price, 'short'
                )
                
                self._enter_position(symbol, 'short', shares, current_price, 
                                  current_time, stop_loss, take_profit)
    
    def _check_exit_signals(self, strategy: Strategy, data: pd.DataFrame, index: int, current_row: pd.Series):
        """Check for exit signals including risk management"""
        symbol = current_row.get('symbol', 'UNKNOWN')
        current_price = current_row['close']
        current_time = current_row['Date']
        
        if symbol in self.positions:
            position = self.positions[symbol]
            
            # Check risk management exits
            should_close, reason = self.risk_manager.should_close_position(
                {
                    'entry_price': position.entry_price,
                    'type': position.position_type,
                    'stop_loss': position.stop_loss,
                    'take_profit': position.take_profit,
                    'entry_time': position.entry_time
                },
                current_price, current_time
            )
            
            if should_close:
                self._close_position(symbol, current_price, current_time, reason)
                return
            
            # Check strategy exit signals
            if (position.position_type == 'long' and strategy.should_exit_long(data, index)) or \
               (position.position_type == 'short' and strategy.should_exit_short(data, index)):
                self._close_position(symbol, current_price, current_time, "Strategy exit")
    
    def _enter_position(self, symbol: str, position_type: str, shares: float, 
                       price: float, time: datetime, stop_loss: float, take_profit: float):
        """Enter a new position"""
        position = Position(
            symbol=symbol,
            position_type=position_type,
            shares=shares,
            entry_price=price,
            entry_time=time,
            current_price=price,
            unrealized_pnl=0,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        self.positions[symbol] = position
        self.capital -= shares * price
        
        self.logger.info(f"Entered {position_type.upper()} position: {shares:.2f} shares at ${price:.2f}")
    
    def _close_position(self, symbol: str, price: float, time: datetime, reason: str):
        """Close an existing position"""
        if symbol not in self.positions:
            return
        
        position = self.positions[symbol]
        
        # Calculate P&L
        if position.position_type == 'long':
            pnl = (price - position.entry_price) * position.shares
        else:  # short
            pnl = (position.entry_price - price) * position.shares
        
        pnl_percentage = pnl / (position.entry_price * position.shares)
        
        # Update capital
        self.capital += position.shares * price + pnl
        
        # Record trade
        trade = Trade(
            symbol=symbol,
            entry_time=position.entry_time,
            exit_time=time,
            entry_price=position.entry_price,
            exit_price=price,
            position_type=position.position_type,
            shares=position.shares,
            pnl=pnl,
            pnl_percentage=pnl_percentage,
            stop_loss=position.stop_loss,
            take_profit=position.take_profit,
            exit_reason=reason
        )
        
        self.trades.append(trade)
        del self.positions[symbol]
        
        self.logger.info(f"Closed {position.position_type} position: P&L = ${pnl:.2f} ({pnl_percentage:.2%})")
    
    def _close_all_positions(self, price: float, time: datetime):
        """Close all remaining positions"""
        for symbol in list(self.positions.keys()):
            self._close_position(symbol, price, time, "End of backtest")
    
    def _update_positions(self, price: float, time: datetime):
        """Update position values and trailing stops"""
        for symbol, position in self.positions.items():
            position.current_price = price
            
            # Update trailing stops
            if position.position_type == 'long':
                position.stop_loss = self.risk_manager.update_trailing_stop(
                    position.stop_loss, price, 'long'
                )
                position.take_profit = self.risk_manager.update_trailing_profit(
                    position.take_profit, price, 'long'
                )
            else:  # short
                position.stop_loss = self.risk_manager.update_trailing_stop(
                    position.stop_loss, price, 'short'
                )
                position.take_profit = self.risk_manager.update_trailing_profit(
                    position.take_profit, price, 'short'
                )
            
            # Calculate unrealized P&L
            if position.position_type == 'long':
                position.unrealized_pnl = (price - position.entry_price) * position.shares
            else:  # short
                position.unrealized_pnl = (position.entry_price - price) * position.shares
    
    def _update_equity_curve(self, price: float, time: datetime):
        """Update equity curve"""
        # Calculate current portfolio value
        portfolio_value = self.capital
        
        for position in self.positions.values():
            portfolio_value += position.shares * price
        
        self.equity_curve.append(portfolio_value)
        self.timestamps.append(time)
    
    def get_performance_report(self, results: Dict[str, Any]) -> str:
        """Generate comprehensive performance report"""
        if "error" in results:
            return f"Backtest Error: {results['error']}"
        
        metrics = results['performance']
        report = f"""
ENHANCED BACKTEST RESULTS
{'=' * 50}

STRATEGY: {results['strategy']}
SYMBOL: {results['symbol']}
PERIOD: {self.timestamps[0]} to {self.timestamps[-1]}

CAPITAL METRICS:
Initial Capital: ${results['initial_capital']:,.2f}
Final Capital: ${results['final_capital']:,.2f}
Total Return: {results['total_return']:.2%}

RISK-ADJUSTED METRICS:
Sharpe Ratio: {metrics['sharpe_ratio']:.2f}
Sortino Ratio: {metrics['sortino_ratio']:.2f}
Calmar Ratio: {metrics['calmar_ratio']:.2f}
Information Ratio: {metrics['information_ratio']:.2f}
Omega Ratio: {metrics['omega_ratio']:.2f}
Treynor Ratio: {metrics['treynor_ratio']:.2f}

RISK METRICS:
Maximum Drawdown: {metrics['max_drawdown']:.2%}
Volatility: {metrics['volatility']:.2%}
Value at Risk (95%): {metrics['var_95']:.2%}
Conditional VaR (95%): {metrics['cvar_95']:.2%}

TRADE METRICS:
Total Trades: {results['trades']}
Winning Trades: {metrics['winning_trades']}
Losing Trades: {metrics['losing_trades']}
Win Rate: {metrics['win_rate']:.2%}
Profit Factor: {metrics['profit_factor']:.2f}
Average Win: ${metrics['average_win']:.2f}
Average Loss: ${metrics['average_loss']:.2f}
Largest Win: ${metrics['largest_win']:.2f}
Largest Loss: ${metrics['largest_loss']:.2f}

MONTHLY METRICS:
Best Month: {metrics['best_month']:.2%}
Worst Month: {metrics['worst_month']:.2%}
Positive Months: {metrics['positive_months']}
Negative Months: {metrics['negative_months']}

RISK MANAGEMENT SUMMARY:
{self.risk_manager.get_risk_summary()}
"""
        return report 