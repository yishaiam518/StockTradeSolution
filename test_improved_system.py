#!/usr/bin/env python3
"""
Test script to verify the improved trading system with more aggressive settings.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.real_time_trading.automation_engine import HistoricalBacktestEngine
from src.utils.config_loader import config
from src.trading_system import get_trading_system

def test_improved_system():
    """Test the improved trading system with more aggressive settings."""
    
    print("=== TESTING IMPROVED TRADING SYSTEM ===")
    
    # Get config
    config_dict = config.config
    print(f"Config loaded: {list(config_dict.keys())}")
    
    # Test stock selection
    print("\n--- Testing Improved Stock Selection ---")
    trading_system = get_trading_system()
    
    # Test with different thresholds
    stocks_high_score = trading_system.select_stocks(max_stocks=5, min_score=0.7)
    stocks_medium_score = trading_system.select_stocks(max_stocks=5, min_score=0.4)
    stocks_low_score = trading_system.select_stocks(max_stocks=5, min_score=0.2)
    
    print(f"High score stocks (min_score=0.7): {len(stocks_high_score)} stocks - {stocks_high_score}")
    print(f"Medium score stocks (min_score=0.4): {len(stocks_medium_score)} stocks - {stocks_medium_score}")
    print(f"Low score stocks (min_score=0.2): {len(stocks_low_score)} stocks - {stocks_low_score}")
    
    # Test historical backtest with improved settings
    print("\n--- Testing Historical Backtest with Improved Settings ---")
    
    # Test with a shorter period and more volatile stocks
    start_date = "2023-01-01"
    end_date = "2023-03-31"  # 3 months for more frequent trading
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
    
    # Test strategy configuration
    print(f"\n=== STRATEGY CONFIGURATION ===")
    macd_strategy = trading_system.get_strategy('MACDStrategy')
    if macd_strategy:
        print(f"MACD Strategy exit conditions: {macd_strategy.exit_conditions}")
        print(f"MACD Strategy entry conditions: {macd_strategy.entry_conditions}")
    
    # Test with different time periods
    print(f"\n=== TESTING DIFFERENT PERIODS ===")
    
    periods = [
        ("2023-01-01", "2023-02-28"),  # 2 months
        ("2023-03-01", "2023-04-30"),  # 2 months
        ("2023-05-01", "2023-06-30"),  # 2 months
    ]
    
    for start, end in periods:
        print(f"\nTesting period: {start} to {end}")
        engine = HistoricalBacktestEngine(config_dict, start, end, benchmark)
        results = engine.run_backtest()
        
        print(f"  Total trades: {results.get('total_trades', 0)}")
        print(f"  Total return: {results.get('total_return', 0):.2f}%")
        print(f"  Winning trades: {results.get('winning_trades', 0)}")
        print(f"  Losing trades: {results.get('losing_trades', 0)}")
    
    print("\n=== IMPROVED SYSTEM TEST COMPLETED ===")
    return True

if __name__ == "__main__":
    test_improved_system() 