#!/usr/bin/env python3
"""
Comprehensive test to verify historical backtest functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.real_time_trading.automation_engine import HistoricalBacktestEngine
from src.utils.config_loader import config

def test_comprehensive_backtest():
    """Test the historical backtest comprehensively."""
    
    print("=== COMPREHENSIVE HISTORICAL BACKTEST TEST ===")
    
    # Get config
    config_dict = config.config
    print(f"Config loaded: {list(config_dict.keys())}")
    
    # Test with a shorter period and more volatile stocks
    start_date = "2023-01-01"
    end_date = "2023-02-28"
    benchmark = "SPY"
    
    print(f"Testing period: {start_date} to {end_date}")
    
    # Create engine
    engine = HistoricalBacktestEngine(config_dict, start_date, end_date, benchmark)
    
    # Run backtest
    print("Running backtest...")
    results = engine.run_backtest()
    
    # Analyze results
    print(f"\n=== RESULTS ===")
    print(f"Total trades: {results.get('total_trades', 0)}")
    print(f"Winning trades: {results.get('winning_trades', 0)}")
    print(f"Losing trades: {results.get('losing_trades', 0)}")
    print(f"Total return: {results.get('total_return', 0):.2f}%")
    print(f"Final value: ${results.get('final_value', 0):.2f}")
    
    # Check trades
    trades = results.get('trades', [])
    buy_trades = [t for t in trades if t.get('action') == 'BUY']
    sell_trades = [t for t in trades if t.get('action') == 'SELL']
    
    print(f"\n=== TRADE ANALYSIS ===")
    print(f"BUY trades: {len(buy_trades)}")
    print(f"SELL trades: {len(sell_trades)}")
    
    if buy_trades:
        print(f"First BUY trade: {buy_trades[0]}")
    
    if sell_trades:
        print(f"First SELL trade: {sell_trades[0]}")
    
    # Check portfolio
    print(f"\n=== PORTFOLIO ANALYSIS ===")
    print(f"Portfolio manager: {engine.portfolio_manager}")
    print(f"Portfolio contents: {engine.portfolio_manager.portfolio}")
    
    # Check if positions were added
    if engine.portfolio_manager.portfolio:
        for symbol, position in engine.portfolio_manager.portfolio.items():
            print(f"Position in {symbol}: {position}")
    
    # Check cash
    print(f"Cash remaining: ${engine.cash:.2f}")
    
    # Check if trades were recorded
    print(f"\n=== TRADE RECORDING ===")
    print(f"Engine trades: {len(engine.trades)}")
    if engine.trades:
        print(f"First engine trade: {engine.trades[0]}")

if __name__ == "__main__":
    test_comprehensive_backtest() 