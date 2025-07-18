#!/usr/bin/env python3
"""
Debug script to test the data pipeline and identify issues with trade generation.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data_engine.data_engine import DataEngine
from src.backtesting.backtest_engine import BacktestEngine
from src.strategies.macd_strategy import MACDStrategy
from src.utils.logger import logger
import pandas as pd
from datetime import datetime, timedelta

def debug_data_pipeline():
    """Debug the data pipeline and identify issues."""
    print("=== DEBUGGING DATA PIPELINE ===")
    
    # 1. Initialize components
    print("\n1. Initializing components...")
    data_engine = DataEngine()
    backtest_engine = BacktestEngine()
    
    # 2. Clear cache to force fresh data
    print("\n2. Clearing data cache...")
    data_engine.clear_cache()
    print("   ✓ Cache cleared")
    
    # 3. Test data fetching for AAPL
    print("\n3. Testing data fetching for AAPL...")
    start_date = "2023-01-01"
    end_date = "2023-12-31"
    
    try:
        data = data_engine.fetch_data("AAPL", start_date, end_date, force_refresh=True)
        print(f"   ✓ Fetched {len(data)} records for AAPL")
        print(f"   Date range: {data['date'].min()} to {data['date'].max()}")
        print(f"   Price range: ${data['close'].min():.2f} to ${data['close'].max():.2f}")
        
        # Check for any anomalies
        print(f"   Missing values: {data.isnull().sum().sum()}")
        print(f"   Zero prices: {(data['close'] == 0).sum()}")
        
    except Exception as e:
        print(f"   ❌ Error fetching AAPL data: {e}")
        return
    
    # 4. Test strategy with the data
    print("\n4. Testing MACD strategy with the data...")
    strategy = MACDStrategy()
    
    # Prepare data with indicators
    try:
        prepared_data = backtest_engine._prepare_data("AAPL", start_date, end_date)
        print(f"   ✓ Prepared {len(prepared_data)} data points with indicators")
        
        # Check indicators
        print(f"   MACD values: {prepared_data['macd_line'].notna().sum()} non-null")
        print(f"   Signal values: {prepared_data['macd_signal'].notna().sum()} non-null")
        print(f"   RSI values: {prepared_data['rsi'].notna().sum()} non-null")
        
        # Check for crossovers
        macd_crossovers = ((prepared_data['macd_line'] > prepared_data['macd_signal']) & 
                          (prepared_data['macd_line'].shift(1) <= prepared_data['macd_signal'].shift(1))).sum()
        print(f"   MACD crossovers (up): {macd_crossovers}")
        
        macd_crossovers_down = ((prepared_data['macd_line'] < prepared_data['macd_signal']) & 
                               (prepared_data['macd_line'].shift(1) >= prepared_data['macd_signal'].shift(1))).sum()
        print(f"   MACD crossovers (down): {macd_crossovers_down}")
        
    except Exception as e:
        print(f"   ❌ Error preparing data: {e}")
        return
    
    # 5. Test strategy entry/exit signals
    print("\n5. Testing strategy signals...")
    try:
        # Test a few data points
        test_points = prepared_data.tail(10)
        
        for i, (idx, row) in enumerate(test_points.iterrows()):
            should_entry, entry_reason = strategy.should_entry(prepared_data, i)
            should_exit, exit_reason = strategy.should_exit(prepared_data, i, 100.0, "2023-01-01")  # dummy values
            
            print(f"   Point {i}: Entry={should_entry}, Exit={should_exit}")
            
    except Exception as e:
        print(f"   ❌ Error testing strategy signals: {e}")
    
    # 6. Run a mini backtest
    print("\n6. Running mini backtest...")
    try:
        results = backtest_engine.run_backtest(
            symbol="AAPL",
            strategy_name="MACDStrategy",
            start_date=start_date,
            end_date=end_date
        )
        
        print(f"   ✓ Backtest completed")
        print(f"   Total trades: {results.get('total_trades', 0)}")
        print(f"   Final return: {results.get('final_return', 0):.2f}%")
        print(f"   Max drawdown: {results.get('max_drawdown', 0):.2f}%")
        
        # Check trade details
        trades = results.get('trades', [])
        if trades:
            print(f"   Trade details:")
            for i, trade in enumerate(trades[:5]):  # Show first 5 trades
                print(f"     Trade {i+1}: {trade.get('entry_date', 'N/A')} - {trade.get('exit_date', 'N/A')}")
                print(f"       Entry: ${trade.get('entry_price', 0):.2f}, Exit: ${trade.get('exit_price', 0):.2f}")
                print(f"       PnL: {trade.get('pnl', 0):.2f}%")
        
    except Exception as e:
        print(f"   ❌ Error running backtest: {e}")
    
    # 7. Test with different date ranges
    print("\n7. Testing with different date ranges...")
    test_ranges = [
        ("2022-01-01", "2022-12-31"),
        ("2021-01-01", "2021-12-31"),
        ("2020-01-01", "2020-12-31")
    ]
    
    for start, end in test_ranges:
        try:
            data = data_engine.fetch_data("AAPL", start, end, force_refresh=True)
            results = backtest_engine.run_backtest(
                symbol="AAPL",
                strategy_name="MACDStrategy",
                start_date=start,
                end_date=end
            )
            
            trades = results.get('total_trades', 0)
            print(f"   {start} to {end}: {trades} trades")
            
        except Exception as e:
            print(f"   {start} to {end}: Error - {e}")
    
    print("\n=== DEBUG COMPLETE ===")

if __name__ == "__main__":
    debug_data_pipeline() 