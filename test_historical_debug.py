#!/usr/bin/env python3
"""
Debug script to test the HistoricalBacktestEngine directly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.real_time_trading.automation_engine import HistoricalBacktestEngine
from src.utils.config_loader import config

def test_historical_backtest():
    """Test the HistoricalBacktestEngine directly."""
    
    print("Testing HistoricalBacktestEngine...")
    
    # Get config
    config_dict = config.config
    print(f"Config keys: {list(config_dict.keys())}")
    
    # Create engine
    print("Creating HistoricalBacktestEngine...")
    engine = HistoricalBacktestEngine(config_dict, '2023-01-01', '2023-02-28', 'SPY')
    
    # Run backtest
    print("Running backtest...")
    results = engine.run_backtest()
    
    print(f"Results keys: {list(results.keys())}")
    print(f"Total trades: {results.get('total_trades', 0)}")
    print(f"Trades: {len(results.get('trades', []))}")
    
    if results.get('trades'):
        print("Sample trades:")
        for i, trade in enumerate(results['trades'][:3]):
            print(f"  {i+1}. {trade}")

if __name__ == "__main__":
    test_historical_backtest() 