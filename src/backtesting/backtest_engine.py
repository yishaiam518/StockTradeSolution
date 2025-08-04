"""
Backtesting Engine - Core backtesting functionality
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging

from ..data_collection.data_manager import DataCollectionManager
from ..indicators import indicator_manager

logger = logging.getLogger(__name__)

class PositionType(Enum):
    """Position types"""
    LONG = "long"
    SHORT = "short"

class OrderType(Enum):
    """Order types"""
    BUY = "buy"
    SELL = "sell"

@dataclass
class Trade:
    """Represents a single trade"""
    symbol: str
    entry_date: datetime
    exit_date: Optional[datetime]
    entry_price: float
    exit_price: Optional[float]
    quantity: float
    position_type: PositionType
    pnl: Optional[float] = None
    pnl_percent: Optional[float] = None
    
    def __post_init__(self):
        if self.exit_price and self.entry_price:
            if self.position_type == PositionType.LONG:
                self.pnl = (self.exit_price - self.entry_price) * self.quantity
                self.pnl_percent = ((self.exit_price - self.entry_price) / self.entry_price) * 100
            else:  # SHORT
                self.pnl = (self.entry_price - self.exit_price) * self.quantity
                self.pnl_percent = ((self.entry_price - self.exit_price) / self.entry_price) * 100

@dataclass
class Position:
    """Represents an open position"""
    symbol: str
    entry_date: datetime
    entry_price: float
    quantity: float
    position_type: PositionType
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    unrealized_pnl_percent: float = 0.0
    
    def update_price(self, price: float):
        """Update position with current price"""
        self.current_price = price
        if self.position_type == PositionType.LONG:
            self.unrealized_pnl = (price - self.entry_price) * self.quantity
            self.unrealized_pnl_percent = ((price - self.entry_price) / self.entry_price) * 100
        else:  # SHORT
            self.unrealized_pnl = (self.entry_price - price) * self.quantity
            self.unrealized_pnl_percent = ((self.entry_price - price) / self.entry_price) * 100

class Strategy:
    """Abstract base class for trading strategies"""
    
    def __init__(self, name: str, parameters: Dict[str, Any] = None):
        self.name = name
        self.parameters = parameters or {}
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
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
        return capital * 0.1  # Default to 10% of capital

class BacktestEngine:
    """Main backtesting engine"""
    
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.equity_curve: List[float] = []
        self.data_manager = DataCollectionManager()
        self.logger = logging.getLogger(__name__)
        
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
            if not all(col in data.columns for col in required_columns):
                self.logger.error(f"Missing required columns. Available: {data.columns}")
                return pd.DataFrame()
            
            # Convert Date to datetime if needed
            if 'Date' in data.columns:
                data['Date'] = pd.to_datetime(data['Date'])
                data = data.sort_values('Date').reset_index(drop=True)
            
            self.logger.info(f"Loaded {len(data)} data points for {symbol}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error loading data for {symbol}: {e}")
            return pd.DataFrame()
    
    def run_backtest(self, strategy: Strategy, collection_id: str, symbol: str, 
                    start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Run backtest for a strategy"""
        self.logger.info(f"Starting backtest for {strategy.name} on {symbol}")
        
        # Reset state
        self.capital = self.initial_capital
        self.positions = {}
        self.trades = []
        self.equity_curve = []
        
        # Load data
        data = self.load_data(collection_id, symbol)
        if data.empty:
            return {"error": "No data available"}
        
        # Filter by date range if specified
        if start_date:
            data = data[data['Date'] >= pd.to_datetime(start_date)]
        if end_date:
            data = data[data['Date'] <= pd.to_datetime(end_date)]
        
        if data.empty:
            return {"error": "No data in specified date range"}
        
        self.logger.info(f"Running backtest on {len(data)} data points")
        
        # Run backtest
        for i in range(len(data)):
            current_data = data.iloc[:i+1]  # Data up to current point
            current_row = data.iloc[i]
            
            # Update equity curve
            self._update_equity_curve(current_row)
            
            # Check for exit signals first
            self._check_exit_signals(strategy, current_data, i, current_row)
            
            # Check for entry signals
            self._check_entry_signals(strategy, current_data, i, current_row)
        
        # Close any remaining positions
        self._close_all_positions(data.iloc[-1])
        
        # Calculate performance metrics
        performance = self._calculate_performance()
        
        return {
            "success": True,
            "strategy": strategy.name,
            "symbol": symbol,
            "initial_capital": self.initial_capital,
            "final_capital": self.capital,
            "total_return": ((self.capital - self.initial_capital) / self.initial_capital) * 100,
            "trades": len(self.trades),
            "performance": performance,
            "equity_curve": self.equity_curve
        }
    
    def _check_entry_signals(self, strategy: Strategy, data: pd.DataFrame, index: int, current_row: pd.Series):
        """Check for entry signals"""
        symbol = current_row.get('symbol', 'UNKNOWN')
        
        # Check for long entry
        if strategy.should_enter_long(data, index):
            if symbol not in self.positions:
                position_size = strategy.get_position_size(data, index, self.capital)
                quantity = position_size / current_row['close']
                
                position = Position(
                    symbol=symbol,
                    entry_date=current_row['Date'],
                    entry_price=current_row['close'],
                    quantity=quantity,
                    position_type=PositionType.LONG
                )
                position.update_price(current_row['close'])
                
                self.positions[symbol] = position
                self.capital -= position_size
                self.logger.info(f"Entered LONG position: {quantity:.2f} shares at ${current_row['close']:.2f}")
        
        # Check for short entry
        elif strategy.should_enter_short(data, index):
            if symbol not in self.positions:
                position_size = strategy.get_position_size(data, index, self.capital)
                quantity = position_size / current_row['close']
                
                position = Position(
                    symbol=symbol,
                    entry_date=current_row['Date'],
                    entry_price=current_row['close'],
                    quantity=quantity,
                    position_type=PositionType.SHORT
                )
                position.update_price(current_row['close'])
                
                self.positions[symbol] = position
                self.capital -= position_size
                self.logger.info(f"Entered SHORT position: {quantity:.2f} shares at ${current_row['close']:.2f}")
    
    def _check_exit_signals(self, strategy: Strategy, data: pd.DataFrame, index: int, current_row: pd.Series):
        """Check for exit signals"""
        symbol = current_row.get('symbol', 'UNKNOWN')
        
        if symbol in self.positions:
            position = self.positions[symbol]
            should_exit = False
            
            if position.position_type == PositionType.LONG and strategy.should_exit_long(data, index):
                should_exit = True
            elif position.position_type == PositionType.SHORT and strategy.should_exit_short(data, index):
                should_exit = True
            
            if should_exit:
                self._close_position(position, current_row)
    
    def _close_position(self, position: Position, current_row: pd.Series):
        """Close a position"""
        # Create trade record
        trade = Trade(
            symbol=position.symbol,
            entry_date=position.entry_date,
            exit_date=current_row['Date'],
            entry_price=position.entry_price,
            exit_price=current_row['close'],
            quantity=position.quantity,
            position_type=position.position_type
        )
        
        self.trades.append(trade)
        
        # Update capital
        if position.position_type == PositionType.LONG:
            self.capital += position.quantity * current_row['close']
        else:  # SHORT
            self.capital += (position.entry_price - current_row['close']) * position.quantity
        
        # Remove position
        del self.positions[position.symbol]
        
        self.logger.info(f"Closed {position.position_type.value} position: P&L = ${trade.pnl:.2f} ({trade.pnl_percent:.2f}%)")
    
    def _close_all_positions(self, last_row: pd.Series):
        """Close all remaining positions"""
        for symbol, position in list(self.positions.items()):
            position.update_price(last_row['close'])
            self._close_position(position, last_row)
    
    def _update_equity_curve(self, current_row: pd.Series):
        """Update equity curve"""
        total_value = self.capital
        
        # Add unrealized P&L from open positions
        for position in self.positions.values():
            position.update_price(current_row['close'])
            total_value += position.unrealized_pnl
        
        self.equity_curve.append(total_value)
    
    def _calculate_performance(self) -> Dict[str, float]:
        """Calculate performance metrics"""
        if not self.trades:
            return {
                "total_return": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0
            }
        
        # Basic metrics
        total_return = ((self.capital - self.initial_capital) / self.initial_capital) * 100
        winning_trades = [t for t in self.trades if t.pnl and t.pnl > 0]
        losing_trades = [t for t in self.trades if t.pnl and t.pnl < 0]
        
        win_rate = len(winning_trades) / len(self.trades) * 100 if self.trades else 0
        
        # Profit factor
        total_profit = sum(t.pnl for t in winning_trades) if winning_trades else 0
        total_loss = abs(sum(t.pnl for t in losing_trades)) if losing_trades else 0
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        # Sharpe ratio (simplified)
        returns = [t.pnl_percent for t in self.trades if t.pnl_percent is not None]
        sharpe_ratio = np.mean(returns) / np.std(returns) if len(returns) > 1 and np.std(returns) > 0 else 0
        
        # Max drawdown
        max_drawdown = 0
        peak = self.initial_capital
        for value in self.equity_curve:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak * 100
            max_drawdown = max(max_drawdown, drawdown)
        
        return {
            "total_return": total_return,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "total_trades": len(self.trades),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades)
        } 