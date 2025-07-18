"""
Order Manager

Handles order lifecycle, tracking, and management for real-time trading.
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum

from ..utils.logger import get_logger


class OrderStatus(Enum):
    """Order status enumeration."""
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class OrderType(Enum):
    """Order type enumeration."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderSide(Enum):
    """Order side enumeration."""
    BUY = "buy"
    SELL = "sell"


class OrderManager:
    """Manages order lifecycle and tracking."""
    
    def __init__(self):
        """Initialize the order manager."""
        self.logger = get_logger(__name__)
        
        # Order storage
        self.orders = {}  # order_id -> order_details
        self.pending_orders = {}  # symbol -> list of pending orders
        self.order_history = []
        
        # Order tracking
        self.next_order_id = 1
        
    def create_order(self, symbol: str, quantity: int, side: OrderSide,
                    order_type: OrderType, price: Optional[float] = None,
                    stop_price: Optional[float] = None) -> str:
        """Create a new order."""
        order_id = str(uuid.uuid4())
        
        order = {
            'order_id': order_id,
            'symbol': symbol,
            'quantity': quantity,
            'filled_quantity': 0,
            'side': side.value,
            'order_type': order_type.value,
            'price': price,
            'stop_price': stop_price,
            'status': OrderStatus.PENDING.value,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'fills': []
        }
        
        self.orders[order_id] = order
        
        # Add to pending orders
        if symbol not in self.pending_orders:
            self.pending_orders[symbol] = []
        self.pending_orders[symbol].append(order_id)
        
        self.logger.info(f"Created order {order_id}: {side.value} {quantity} {symbol}")
        
        return order_id
    
    def get_order(self, order_id: str) -> Optional[Dict]:
        """Get order details by ID."""
        return self.orders.get(order_id)
    
    def get_pending_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get pending orders, optionally filtered by symbol."""
        if symbol is None:
            return [order for order in self.orders.values() 
                   if order['status'] == OrderStatus.PENDING.value]
        
        pending_ids = self.pending_orders.get(symbol, [])
        return [self.orders[order_id] for order_id in pending_ids 
                if self.orders[order_id]['status'] == OrderStatus.PENDING.value]
    
    def update_order_status(self, order_id: str, status: OrderStatus, 
                           fill_price: Optional[float] = None, 
                           fill_quantity: Optional[int] = None):
        """Update order status and handle fills."""
        if order_id not in self.orders:
            self.logger.warning(f"Order {order_id} not found")
            return
        
        order = self.orders[order_id]
        order['status'] = status.value
        order['updated_at'] = datetime.now()
        
        # Handle fill
        if fill_price is not None and fill_quantity is not None:
            fill = {
                'price': fill_price,
                'quantity': fill_quantity,
                'timestamp': datetime.now()
            }
            order['fills'].append(fill)
            order['filled_quantity'] += fill_quantity
            
            self.logger.info(f"Order {order_id} filled: {fill_quantity} shares at ${fill_price:.2f}")
        
        # Update status based on fills
        if order['filled_quantity'] >= order['quantity']:
            order['status'] = OrderStatus.FILLED.value
        elif order['filled_quantity'] > 0:
            order['status'] = OrderStatus.PARTIALLY_FILLED.value
        
        # Remove from pending if no longer pending
        if status != OrderStatus.PENDING:
            symbol = order['symbol']
            if symbol in self.pending_orders and order_id in self.pending_orders[symbol]:
                self.pending_orders[symbol].remove(order_id)
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order."""
        if order_id not in self.orders:
            self.logger.warning(f"Order {order_id} not found")
            return False
        
        order = self.orders[order_id]
        if order['status'] != OrderStatus.PENDING.value:
            self.logger.warning(f"Cannot cancel order {order_id} with status {order['status']}")
            return False
        
        order['status'] = OrderStatus.CANCELLED.value
        order['updated_at'] = datetime.now()
        
        # Remove from pending orders
        symbol = order['symbol']
        if symbol in self.pending_orders and order_id in self.pending_orders[symbol]:
            self.pending_orders[symbol].remove(order_id)
        
        self.logger.info(f"Cancelled order {order_id}")
        return True
    
    def reject_order(self, order_id: str, reason: str):
        """Reject an order."""
        if order_id not in self.orders:
            self.logger.warning(f"Order {order_id} not found")
            return
        
        order = self.orders[order_id]
        order['status'] = OrderStatus.REJECTED.value
        order['rejection_reason'] = reason
        order['updated_at'] = datetime.now()
        
        # Remove from pending orders
        symbol = order['symbol']
        if symbol in self.pending_orders and order_id in self.pending_orders[symbol]:
            self.pending_orders[symbol].remove(order_id)
        
        self.logger.warning(f"Rejected order {order_id}: {reason}")
    
    def get_order_history(self, symbol: Optional[str] = None, 
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None) -> List[Dict]:
        """Get order history with optional filtering."""
        orders = list(self.orders.values())
        
        # Filter by symbol
        if symbol is not None:
            orders = [order for order in orders if order['symbol'] == symbol]
        
        # Filter by date range
        if start_date is not None:
            orders = [order for order in orders if order['created_at'] >= start_date]
        
        if end_date is not None:
            orders = [order for order in orders if order['created_at'] <= end_date]
        
        # Sort by creation date (newest first)
        orders.sort(key=lambda x: x['created_at'], reverse=True)
        
        return orders
    
    def get_order_statistics(self) -> Dict:
        """Get order statistics."""
        total_orders = len(self.orders)
        pending_orders = len([order for order in self.orders.values() 
                            if order['status'] == OrderStatus.PENDING.value])
        filled_orders = len([order for order in self.orders.values() 
                           if order['status'] == OrderStatus.FILLED.value])
        cancelled_orders = len([order for order in self.orders.values() 
                              if order['status'] == OrderStatus.CANCELLED.value])
        rejected_orders = len([order for order in self.orders.values() 
                             if order['status'] == OrderStatus.REJECTED.value])
        
        return {
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'filled_orders': filled_orders,
            'cancelled_orders': cancelled_orders,
            'rejected_orders': rejected_orders,
            'fill_rate': (filled_orders / total_orders * 100) if total_orders > 0 else 0
        }
    
    def cleanup_old_orders(self, days_to_keep: int = 30):
        """Clean up old orders from memory."""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        orders_to_remove = []
        for order_id, order in self.orders.items():
            if order['created_at'] < cutoff_date:
                orders_to_remove.append(order_id)
        
        for order_id in orders_to_remove:
            del self.orders[order_id]
        
        self.logger.info(f"Cleaned up {len(orders_to_remove)} old orders")
    
    def get_active_orders_by_symbol(self) -> Dict[str, List[Dict]]:
        """Get active orders grouped by symbol."""
        active_orders = {}
        
        for order in self.orders.values():
            if order['status'] in [OrderStatus.PENDING.value, OrderStatus.PARTIALLY_FILLED.value]:
                symbol = order['symbol']
                if symbol not in active_orders:
                    active_orders[symbol] = []
                active_orders[symbol].append(order)
        
        return active_orders 