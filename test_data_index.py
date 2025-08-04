#!/usr/bin/env python3
"""
Test Data Index

Test to see what the actual data index looks like.
"""

import sys
import os
import pandas as pd

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.backtesting.backtest_engine import BacktestEngine

def test_data_index():
    """Test the data index format."""
    print("Testing data index format...")
    
    # Initialize backtest engine
    engine = BacktestEngine()
    
    # Get AAPL data
    aapl_data = engine._get_cached_or_fetch_data('AAPL', '2023-01-01', '2023-12-31')
    
    print(f"Data shape: {aapl_data.shape}")
    print(f"Data index type: {type(aapl_data.index)}")
    print(f"First 5 index values: {list(aapl_data.index[:5])}")
    print(f"Index dtype: {aapl_data.index.dtype}")
    
    # Check if index is numeric
    if aapl_data.index.dtype in ['int64', 'int32', 'float64']:
        print("❌ ISSUE: Index is numeric, not datetime!")
        print("This is why date parsing is failing.")
    else:
        print("✅ Index appears to be datetime")

if __name__ == "__main__":
    test_data_index() 