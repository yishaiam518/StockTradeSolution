#!/usr/bin/env python3
"""
Test script to verify that trade logging includes dates.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.backtesting.backtest_engine import BacktestEngine
from src.strategies.macd_strategy import MACDStrategy
from src.data_engine.data_engine import DataEngine

def test_trade_logging_with_dates():
    """Test that trade logging includes dates."""
    print("Testing trade logging with dates...")
    
    # Initialize components
    data_engine = DataEngine()
    backtest_engine = BacktestEngine()
    strategy = MACDStrategy()
    
    # Run a backtest
    results = backtest_engine.run_backtest(
        ticker="AAPL",
        strategy=strategy,
        start_date="2020-01-01",
        end_date="2025-07-15",
        initial_capital=10000
    )
    
    print(f"\nBacktest completed with {results.get('total_trades', 0)} trades")
    
    # Check if trades have dates
    trade_log = results.get('trade_log', [])
    if trade_log:
        print("\nTrade details:")
        for i, trade in enumerate(trade_log):
            entry_date = trade.get('entry_date', 'Unknown')
            exit_date = trade.get('exit_date', 'Unknown')
            entry_price = trade.get('entry_price', 0)
            exit_price = trade.get('exit_price', 0)
            shares = trade.get('shares', 0)
            pnl = trade.get('pnl', 0) * 100
            
            print(f"Trade {i+1}: BUY {shares:.2f} shares at ${entry_price:.2f} on {entry_date} → SELL at ${exit_price:.2f} on {exit_date} ({pnl:.2f}%)")
    else:
        print("No trades executed")
    
    return results

if __name__ == "__main__":
    test_trade_logging_with_dates() 