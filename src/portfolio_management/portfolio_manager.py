"""
Portfolio Manager

Main portfolio management class that coordinates allocation, rebalancing,
and risk management operations.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json

from ..utils.config_loader import ConfigLoader
from ..utils.logger import get_logger
from ..data_engine.data_engine import DataEngine
from .allocation_engine import AllocationEngine
from .rebalancing_engine import RebalancingEngine
from .risk_optimizer import RiskOptimizer


class PortfolioManager:
    """Main portfolio management class."""
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        """Initialize the portfolio manager."""
        self.config = ConfigLoader(config_path)
        self.logger = get_logger(__name__)
        self.data_engine = DataEngine()
        
        # Initialize components
        self.allocation_engine = AllocationEngine()
        self.rebalancing_engine = RebalancingEngine()
        self.risk_optimizer = RiskOptimizer()
        
        # Portfolio state
        self.portfolio = {}
        self.target_allocation = {}
        self.current_allocation = {}
        self.performance_history = []
        
        # Configuration
        self.rebalancing_frequency = self.config.get('portfolio_management.rebalancing.frequency')
        self.rebalancing_threshold = self.config.get('portfolio_management.rebalancing.threshold')
        self.max_positions = self.config.get('portfolio_management.allocation.max_positions')
        self.min_positions = self.config.get('portfolio_management.allocation.min_positions')
        self.max_single_position = self.config.get('portfolio_management.allocation.max_single_position')
        
        # Sector limits
        self.sector_limits = self.config.get('portfolio_management.allocation.sector_limits')
        
        self.logger.info("Portfolio Manager initialized")
    
    def add_position(self, symbol: str, quantity: int, price: float, sector: str = "unknown"):
        """Add a position to the portfolio."""
        if symbol not in self.portfolio:
            self.portfolio[symbol] = {
                'quantity': 0,
                'avg_cost': 0.0,
                'total_cost': 0.0,
                'sector': sector,
                'added_at': datetime.now(),
                'last_updated': datetime.now()
            }
        
        position = self.portfolio[symbol]
        
        # Update position
        total_quantity = position['quantity'] + quantity
        total_cost = position['total_cost'] + (quantity * price)
        
        position['quantity'] = total_quantity
        position['total_cost'] = total_cost
        position['avg_cost'] = total_cost / total_quantity if total_quantity > 0 else 0
        position['last_updated'] = datetime.now()
        
        self.logger.info(f"Added position: {quantity} {symbol} at ${price:.2f}")
        self._update_allocation()
    
    def remove_position(self, symbol: str, quantity: int, price: float):
        """Remove a position from the portfolio."""
        if symbol not in self.portfolio:
            self.logger.warning(f"Position {symbol} not found in portfolio")
            return
        
        position = self.portfolio[symbol]
        
        if position['quantity'] < quantity:
            self.logger.warning(f"Insufficient quantity in {symbol}")
            return
        
        # Calculate P&L
        pnl = (price - position['avg_cost']) * quantity
        
        # Update position
        position['quantity'] -= quantity
        position['total_cost'] = position['avg_cost'] * position['quantity']
        position['last_updated'] = datetime.now()
        
        # Remove if quantity becomes zero
        if position['quantity'] == 0:
            del self.portfolio[symbol]
        
        self.logger.info(f"Removed position: {quantity} {symbol} at ${price:.2f}, P&L: ${pnl:.2f}")
        self._update_allocation()
    
    def update_position_prices(self, current_prices: Dict[str, float]):
        """Update current prices for all positions."""
        for symbol, position in self.portfolio.items():
            if symbol in current_prices:
                position['current_price'] = current_prices[symbol]
                position['last_updated'] = datetime.now()
    
    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """Calculate total portfolio value."""
        total_value = 0.0
        
        for symbol, position in self.portfolio.items():
            if symbol in current_prices:
                current_price = current_prices[symbol]
                position_value = position['quantity'] * current_price
                total_value += position_value
        
        return total_value
    
    def get_portfolio_summary(self, current_prices: Dict[str, float]) -> Dict:
        """Get comprehensive portfolio summary."""
        total_value = self.get_portfolio_value(current_prices)
        total_cost = sum(pos['total_cost'] for pos in self.portfolio.values())
        unrealized_pnl = total_value - total_cost
        
        # Calculate sector allocation
        sector_allocation = {}
        for symbol, position in self.portfolio.items():
            if symbol in current_prices:
                sector = position['sector']
                position_value = position['quantity'] * current_prices[symbol]
                
                if sector not in sector_allocation:
                    sector_allocation[sector] = 0.0
                sector_allocation[sector] += position_value
        
        # Convert to percentages
        for sector in sector_allocation:
            sector_allocation[sector] = (sector_allocation[sector] / total_value * 100) if total_value > 0 else 0
        
        return {
            'total_value': total_value,
            'total_cost': total_cost,
            'unrealized_pnl': unrealized_pnl,
            'unrealized_pnl_pct': (unrealized_pnl / total_cost * 100) if total_cost > 0 else 0,
            'num_positions': len(self.portfolio),
            'sector_allocation': sector_allocation,
            'positions': self._get_position_details(current_prices)
        }
    
    def _get_position_details(self, current_prices: Dict[str, float]) -> Dict:
        """Get detailed position information."""
        position_details = {}
        
        for symbol, position in self.portfolio.items():
            if symbol in current_prices:
                current_price = current_prices[symbol]
                current_value = position['quantity'] * current_price
                unrealized_pnl = current_value - position['total_cost']
                
                position_details[symbol] = {
                    'quantity': position['quantity'],
                    'avg_cost': position['avg_cost'],
                    'current_price': current_price,
                    'current_value': current_value,
                    'unrealized_pnl': unrealized_pnl,
                    'unrealized_pnl_pct': (unrealized_pnl / position['total_cost'] * 100) if position['total_cost'] > 0 else 0,
                    'sector': position['sector'],
                    'weight': (current_value / self.get_portfolio_value(current_prices) * 100) if self.get_portfolio_value(current_prices) > 0 else 0
                }
        
        return position_details
    
    def check_rebalancing_needed(self, current_prices: Dict[str, float]) -> bool:
        """Check if portfolio rebalancing is needed."""
        if not self.target_allocation:
            return False
        
        current_allocation = self._calculate_current_allocation(current_prices)
        
        for symbol, target_weight in self.target_allocation.items():
            current_weight = current_allocation.get(symbol, 0)
            deviation = abs(current_weight - target_weight)
            
            if deviation > self.rebalancing_threshold:
                self.logger.info(f"Rebalancing needed: {symbol} deviation {deviation:.2f}%")
                return True
        
        return False
    
    def rebalance_portfolio(self, current_prices: Dict[str, float]) -> Dict:
        """Rebalance the portfolio according to target allocation."""
        if not self.target_allocation:
            self.logger.warning("No target allocation set")
            return {}
        
        total_value = self.get_portfolio_value(current_prices)
        if total_value == 0:
            self.logger.warning("Portfolio has no value")
            return {}
        
        rebalancing_orders = {}
        current_allocation = self._calculate_current_allocation(current_prices)
        
        for symbol, target_weight in self.target_allocation.items():
            target_value = total_value * (target_weight / 100)
            current_value = current_allocation.get(symbol, 0) * total_value / 100
            
            if symbol in current_prices:
                current_price = current_prices[symbol]
                target_quantity = int(target_value / current_price)
                current_quantity = self.portfolio.get(symbol, {}).get('quantity', 0)
                
                quantity_diff = target_quantity - current_quantity
                
                if abs(quantity_diff) > 0:
                    rebalancing_orders[symbol] = {
                        'action': 'buy' if quantity_diff > 0 else 'sell',
                        'quantity': abs(quantity_diff),
                        'price': current_price,
                        'value': abs(quantity_diff) * current_price
                    }
        
        self.logger.info(f"Rebalancing orders generated: {len(rebalancing_orders)} orders")
        return rebalancing_orders
    
    def _calculate_current_allocation(self, current_prices: Dict[str, float]) -> Dict[str, float]:
        """Calculate current portfolio allocation."""
        total_value = self.get_portfolio_value(current_prices)
        if total_value == 0:
            return {}
        
        allocation = {}
        for symbol, position in self.portfolio.items():
            if symbol in current_prices:
                current_value = position['quantity'] * current_prices[symbol]
                allocation[symbol] = (current_value / total_value) * 100
        
        return allocation
    
    def _update_allocation(self):
        """Update current allocation after position changes."""
        # This would typically involve getting current prices
        # For now, we'll just log the update
        self.logger.debug("Portfolio allocation updated")
    
    def set_target_allocation(self, allocation: Dict[str, float]):
        """Set target portfolio allocation."""
        # Validate allocation
        total_weight = sum(allocation.values())
        if abs(total_weight - 100) > 1:  # Allow small rounding errors
            self.logger.warning(f"Target allocation weights sum to {total_weight}%, not 100%")
        
        self.target_allocation = allocation
        self.logger.info(f"Target allocation set: {allocation}")
    
    def optimize_portfolio(self, current_prices: Dict[str, float], 
                          available_symbols: List[str]) -> Dict[str, float]:
        """Optimize portfolio allocation using risk optimization."""
        return self.risk_optimizer.optimize(
            current_prices=current_prices,
            available_symbols=available_symbols,
            current_portfolio=self.portfolio,
            constraints=self._get_optimization_constraints()
        )
    
    def _get_optimization_constraints(self) -> Dict:
        """Get optimization constraints from configuration."""
        return {
            'max_single_position': self.max_single_position,
            'min_positions': self.min_positions,
            'max_positions': self.max_positions,
            'sector_limits': self.sector_limits
        }
    
    def get_performance_metrics(self, start_date: Optional[datetime] = None) -> Dict:
        """Calculate portfolio performance metrics."""
        if not self.performance_history:
            return {
                'total_return': 0.0,
                'total_return_pct': 0.0,
                'volatility': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0
            }
        
        # Filter by date range
        history = self.performance_history
        if start_date:
            history = [record for record in history if record['date'] >= start_date]
        
        if not history:
            return {
                'total_return': 0.0,
                'total_return_pct': 0.0,
                'volatility': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0
            }
        
        # Calculate metrics
        values = [record['value'] for record in history]
        returns = []
        
        for i in range(1, len(values)):
            if values[i-1] > 0:
                returns.append((values[i] - values[i-1]) / values[i-1])
        
        if not returns:
            return {
                'total_return': 0.0,
                'total_return_pct': 0.0,
                'volatility': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0
            }
        
        total_return = values[-1] - values[0]
        total_return_pct = (values[-1] / values[0] - 1) * 100 if values[0] > 0 else 0
        volatility = np.std(returns) * np.sqrt(252)  # Annualized
        sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
        
        # Calculate max drawdown
        peak = values[0]
        max_drawdown = 0.0
        
        for value in values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak if peak > 0 else 0
            max_drawdown = max(max_drawdown, drawdown)
        
        return {
            'total_return': total_return,
            'total_return_pct': total_return_pct,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown * 100
        }
    
    def record_performance(self, value: float, date: Optional[datetime] = None):
        """Record portfolio value for performance tracking."""
        if date is None:
            date = datetime.now()
        
        self.performance_history.append({
            'date': date,
            'value': value
        })
    
    def export_portfolio(self, filepath: str):
        """Export portfolio to JSON file."""
        export_data = {
            'portfolio': self.portfolio,
            'target_allocation': self.target_allocation,
            'performance_history': self.performance_history,
            'export_date': datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        self.logger.info(f"Portfolio exported to {filepath}")
    
    def import_portfolio(self, filepath: str):
        """Import portfolio from JSON file."""
        try:
            with open(filepath, 'r') as f:
                import_data = json.load(f)
            
            self.portfolio = import_data.get('portfolio', {})
            self.target_allocation = import_data.get('target_allocation', {})
            self.performance_history = import_data.get('performance_history', [])
            
            self.logger.info(f"Portfolio imported from {filepath}")
            
        except Exception as e:
            self.logger.error(f"Error importing portfolio: {e}") 