#!/usr/bin/env python3
"""
Test script to verify portfolio manager is working correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.portfolio_management.portfolio_manager import PortfolioManager
from src.real_time_trading.automation_engine import HistoricalBacktestEngine
from src.utils.config_loader import config

def test_portfolio_manager():
    """Test the portfolio manager functionality."""
    
    print("Testing portfolio manager...")
    
    # Create portfolio manager
    portfolio_manager = PortfolioManager()
    
    # Add a position
    symbol = "AAPL"
    shares = 10
    price = 150.0
    date = "2023-03-15"
    
    print(f"Adding position: {shares} shares of {symbol} at ${price}")
    portfolio_manager.add_position(symbol, shares, price, date)
    
    # Check if position exists
    position = portfolio_manager.portfolio.get(symbol)
    print(f"Position: {position}")
    
    # Check portfolio value
    portfolio_value = portfolio_manager.get_portfolio_value({symbol: price})
    print(f"Portfolio value: ${portfolio_value:.2f}")
    
    # Test with HistoricalBacktestEngine
    print("\nTesting with HistoricalBacktestEngine...")
    
    config_dict = config.config
    engine = HistoricalBacktestEngine(config_dict, '2023-01-01', '2023-02-28', 'SPY')
    
    # Check if portfolio manager is accessible
    print(f"Engine portfolio manager: {engine.portfolio_manager}")
    print(f"Engine portfolio: {engine.portfolio_manager.portfolio}")
    
    # Test adding a position through the engine
    engine.portfolio_manager.add_position("MSFT", 5, 300.0, "2023-03-16")
    print(f"After adding MSFT: {engine.portfolio_manager.portfolio}")

if __name__ == "__main__":
    test_portfolio_manager() 