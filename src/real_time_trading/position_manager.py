"""
Position Manager for tracking and managing trading positions
"""

import logging
from typing import Dict, Optional, List, Any
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class Position:
    """Represents a trading position"""
    symbol: str
    shares: float
    entry_price: float
    entry_date: datetime
    current_price: float
    pnl: float
    pnl_pct: float
    status: str  # "OPEN", "CLOSED"

class PositionManager:
    """
    Manages trading positions and position sizing
    """
    
    def __init__(self):
        self.positions: Dict[str, Position] = {}
        self.max_positions = 10  # Maximum number of concurrent positions
        self.max_position_size = 0.1  # Maximum 10% of portfolio per position
        
        logger.info("Position Manager initialized")
    
    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get current position for a symbol
        """
        if symbol in self.positions:
            pos = self.positions[symbol]
            return {
                'symbol': pos.symbol,
                'shares': pos.shares,
                'entry_price': pos.entry_price,
                'entry_date': pos.entry_date,
                'current_price': pos.current_price,
                'pnl': pos.pnl,
                'pnl_pct': pos.pnl_pct,
                'status': pos.status
            }
        return None
    
    def get_all_positions(self) -> List[Dict[str, Any]]:
        """
        Get all current positions
        """
        return [self.get_position(symbol) for symbol in self.positions.keys()]
    
    def update_position(self, symbol: str, action: str, shares: float, price: float) -> None:
        """
        Update position based on trade action
        """
        try:
            if action == 'BUY':
                self._open_position(symbol, shares, price)
            elif action == 'SELL':
                self._close_position(symbol, shares, price)
                
        except Exception as e:
            logger.error(f"Error updating position for {symbol}: {e}")
    
    def _open_position(self, symbol: str, shares: float, price: float) -> None:
        """
        Open a new position
        """
        if symbol in self.positions:
            logger.warning(f"Position already exists for {symbol}")
            return
        
        if len(self.positions) >= self.max_positions:
            logger.warning(f"Maximum positions reached, cannot open position for {symbol}")
            return
        
        position = Position(
            symbol=symbol,
            shares=shares,
            entry_price=price,
            entry_date=datetime.now(),
            current_price=price,
            pnl=0.0,
            pnl_pct=0.0,
            status="OPEN"
        )
        
        self.positions[symbol] = position
        logger.info(f"Opened position: {shares} shares of {symbol} at ${price:.2f}")
    
    def _close_position(self, symbol: str, shares: float, price: float) -> None:
        """
        Close an existing position
        """
        if symbol not in self.positions:
            logger.warning(f"No position found for {symbol}")
            return
        
        position = self.positions[symbol]
        
        # Calculate P&L
        pnl = (price - position.entry_price) * shares
        pnl_pct = ((price - position.entry_price) / position.entry_price) * 100
        
        # Update position
        position.current_price = price
        position.pnl = pnl
        position.pnl_pct = pnl_pct
        position.status = "CLOSED"
        
        logger.info(f"Closed position: {shares} shares of {symbol} at ${price:.2f}, P&L: ${pnl:.2f} ({pnl_pct:.2f}%)")
        
        # Remove from active positions
        del self.positions[symbol]
    
    def update_prices(self, price_updates: Dict[str, float]) -> None:
        """
        Update current prices for all positions
        """
        for symbol, price in price_updates.items():
            if symbol in self.positions:
                position = self.positions[symbol]
                position.current_price = price
                position.pnl = (price - position.entry_price) * position.shares
                position.pnl_pct = ((price - position.entry_price) / position.entry_price) * 100
    
    def get_total_pnl(self) -> float:
        """
        Get total P&L for all open positions
        """
        total_pnl = 0.0
        for position in self.positions.values():
            total_pnl += position.pnl
        return total_pnl
    
    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """
        Calculate total portfolio value
        """
        portfolio_value = 0.0
        
        for symbol, position in self.positions.items():
            if symbol in current_prices:
                portfolio_value += position.shares * current_prices[symbol]
            else:
                portfolio_value += position.shares * position.current_price
        
        return portfolio_value
    
    def can_open_position(self, symbol: str, shares: float, price: float) -> bool:
        """
        Check if we can open a new position
        """
        # Check if we already have a position
        if symbol in self.positions:
            return False
        
        # Check if we have room for more positions
        if len(self.positions) >= self.max_positions:
            return False
        
        # Check position size limit
        position_value = shares * price
        # This would need total portfolio value to calculate percentage
        # For now, just check absolute limits
        
        return True
    
    def get_position_summary(self) -> Dict[str, Any]:
        """
        Get summary of all positions
        """
        total_positions = len(self.positions)
        total_pnl = self.get_total_pnl()
        
        # Calculate average P&L percentage
        if total_positions > 0:
            avg_pnl_pct = sum(pos.pnl_pct for pos in self.positions.values()) / total_positions
        else:
            avg_pnl_pct = 0.0
        
        return {
            'total_positions': total_positions,
            'total_pnl': total_pnl,
            'avg_pnl_pct': avg_pnl_pct,
            'positions': [self.get_position(symbol) for symbol in self.positions.keys()]
        }
    
    def add_position(self, symbol: str, shares: float, price: float) -> bool:
        """
        Add a new position
        """
        try:
            self._open_position(symbol, shares, price)
            return True
        except Exception as e:
            logger.error(f"Error adding position for {symbol}: {e}")
            return False
    
    def update_position_price(self, symbol: str, price: float) -> bool:
        """
        Update the current price of a position
        """
        try:
            if symbol in self.positions:
                position = self.positions[symbol]
                position.current_price = price
                position.pnl = (price - position.entry_price) * position.shares
                position.pnl_pct = ((price - position.entry_price) / position.entry_price) * 100
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating position price for {symbol}: {e}")
            return False
    
    def close_position(self, symbol: str, price: float) -> bool:
        """
        Close a position
        """
        try:
            if symbol in self.positions:
                position = self.positions[symbol]
                self._close_position(symbol, position.shares, price)
                return True
            return False
        except Exception as e:
            logger.error(f"Error closing position for {symbol}: {e}")
            return False
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        Get portfolio summary
        """
        return self.get_position_summary() 