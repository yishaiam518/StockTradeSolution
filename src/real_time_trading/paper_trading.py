"""
Paper Trading Broker

Simulates trading without using real money. Useful for testing
strategies and learning trading concepts.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, Optional
import pandas as pd

from ..utils.logger import get_logger


class PaperTradingBroker:
    """Paper trading broker for simulating trades."""
    
    def __init__(self, initial_balance: float = 100000.0, 
                 commission: float = 0.005, slippage: float = 0.001):
        """Initialize the paper trading broker."""
        self.logger = get_logger(__name__)
        
        # Account state
        self.balance = initial_balance
        self.initial_balance = initial_balance
        self.commission = commission
        self.slippage = slippage
        
        # Trading state
        self.positions = {}  # symbol -> quantity
        self.orders = {}  # order_id -> order_details
        self.trade_history = []
        
        self.logger.info(f"Paper trading broker initialized with ${initial_balance:,.2f}")
    
    def get_balance(self) -> float:
        """Get current account balance."""
        return self.balance
    
    def get_positions(self) -> Dict[str, int]:
        """Get current positions."""
        return self.positions.copy()
    
    def get_position(self, symbol: str) -> int:
        """Get current position for a symbol."""
        return self.positions.get(symbol, 0)
    
    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """Calculate total portfolio value."""
        portfolio_value = self.balance
        
        for symbol, quantity in self.positions.items():
            if symbol in current_prices:
                portfolio_value += quantity * current_prices[symbol]
        
        return portfolio_value
    
    async def place_order(self, symbol: str, quantity: int, side: str, 
                         order_type: str = 'market', price: Optional[float] = None) -> Dict:
        """Place a trading order."""
        order_id = str(uuid.uuid4())
        
        # Validate order
        if quantity <= 0:
            return {
                'order_id': order_id,
                'status': 'rejected',
                'reason': 'Invalid quantity'
            }
        
        if side not in ['buy', 'sell']:
            return {
                'order_id': order_id,
                'status': 'rejected',
                'reason': 'Invalid side'
            }
        
        # Simulate order execution
        execution_price = await self._simulate_execution(symbol, side, order_type, price)
        
        if execution_price is None:
            return {
                'order_id': order_id,
                'status': 'rejected',
                'reason': 'Unable to execute order'
            }
        
        # Calculate costs
        total_cost = quantity * execution_price
        commission_cost = total_cost * self.commission
        total_with_commission = total_cost + commission_cost
        
        # Check if we have enough balance for buy orders
        if side == 'buy':
            if total_with_commission > self.balance:
                return {
                    'order_id': order_id,
                    'status': 'rejected',
                    'reason': 'Insufficient balance'
                }
        
        # Execute the order
        if side == 'buy':
            self.balance -= total_with_commission
            self.positions[symbol] = self.positions.get(symbol, 0) + quantity
        else:  # sell
            current_position = self.positions.get(symbol, 0)
            if quantity > current_position:
                return {
                    'order_id': order_id,
                    'status': 'rejected',
                    'reason': 'Insufficient shares to sell'
                }
            
            self.balance += total_cost - commission_cost
            self.positions[symbol] = current_position - quantity
            
            # Remove position if zero
            if self.positions[symbol] == 0:
                del self.positions[symbol]
        
        # Record the trade
        trade_record = {
            'order_id': order_id,
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': execution_price,
            'commission': commission_cost,
            'total_cost': total_with_commission,
            'timestamp': datetime.now(),
            'order_type': order_type
        }
        
        self.trade_history.append(trade_record)
        
        # Store order details
        self.orders[order_id] = {
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': execution_price,
            'status': 'filled',
            'timestamp': datetime.now()
        }
        
        self.logger.info(f"Order executed: {side.upper()} {quantity} {symbol} at ${execution_price:.2f}")
        
        return {
            'order_id': order_id,
            'status': 'filled',
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': execution_price,
            'commission': commission_cost,
            'timestamp': datetime.now()
        }
    
    async def _simulate_execution(self, symbol: str, side: str, 
                                 order_type: str, price: Optional[float]) -> Optional[float]:
        """Simulate order execution with slippage."""
        # In a real implementation, this would get the current market price
        # For now, we'll simulate with a base price
        base_price = 100.0  # This should come from market data
        
        if order_type == 'market':
            # Apply slippage based on order side
            if side == 'buy':
                execution_price = base_price * (1 + self.slippage)
            else:  # sell
                execution_price = base_price * (1 - self.slippage)
        elif order_type == 'limit':
            if price is None:
                return None
            execution_price = price
        else:
            return None
        
        return execution_price
    
    def get_order_status(self, order_id: str) -> Optional[Dict]:
        """Get the status of a specific order."""
        return self.orders.get(order_id)
    
    def get_trade_history(self, symbol: Optional[str] = None) -> list:
        """Get trade history, optionally filtered by symbol."""
        if symbol is None:
            return self.trade_history.copy()
        
        return [trade for trade in self.trade_history if trade['symbol'] == symbol]
    
    def get_account_summary(self) -> Dict:
        """Get account summary."""
        total_trades = len(self.trade_history)
        total_commission = sum(trade['commission'] for trade in self.trade_history)
        
        return {
            'balance': self.balance,
            'initial_balance': self.initial_balance,
            'total_return': self.balance - self.initial_balance,
            'total_return_pct': ((self.balance / self.initial_balance) - 1) * 100,
            'positions': self.positions,
            'total_trades': total_trades,
            'total_commission': total_commission
        }
    
    def reset_account(self, new_balance: Optional[float] = None):
        """Reset the account to initial state."""
        if new_balance is not None:
            self.initial_balance = new_balance
        
        self.balance = self.initial_balance
        self.positions = {}
        self.orders = {}
        self.trade_history = []
        
        self.logger.info(f"Account reset to ${self.initial_balance:,.2f}")
    
    def get_performance_metrics(self) -> Dict:
        """Calculate performance metrics."""
        if not self.trade_history:
            return {
                'total_return': 0.0,
                'total_return_pct': 0.0,
                'win_rate': 0.0,
                'avg_trade': 0.0,
                'max_drawdown': 0.0
            }
        
        # Calculate returns
        total_return = self.balance - self.initial_balance
        total_return_pct = ((self.balance / self.initial_balance) - 1) * 100
        
        # Calculate win rate
        profitable_trades = sum(1 for trade in self.trade_history 
                              if trade['side'] == 'sell' and 
                              trade['price'] > trade.get('avg_cost', 0))
        total_sell_trades = sum(1 for trade in self.trade_history 
                               if trade['side'] == 'sell')
        
        win_rate = (profitable_trades / total_sell_trades * 100) if total_sell_trades > 0 else 0
        
        # Calculate average trade
        avg_trade = total_return / len(self.trade_history) if self.trade_history else 0
        
        return {
            'total_return': total_return,
            'total_return_pct': total_return_pct,
            'win_rate': win_rate,
            'avg_trade': avg_trade,
            'total_trades': len(self.trade_history)
        } 