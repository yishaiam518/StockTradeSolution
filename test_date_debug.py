#!/usr/bin/env python3
"""
Test Date Debug

Simple test to debug the date parsing issue in MACD strategy.
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.strategies.macd_strategy import MACDStrategy

def test_date_parsing():
    """Test the date parsing logic."""
    print("Testing date parsing logic...")
    
    # Create a sample strategy
    strategy = MACDStrategy(profile="moderate")
    
    # Create sample data
    dates = pd.date_range('2023-04-12', '2023-04-15', freq='D')
    data = pd.DataFrame({
        'close': [191.13, 191.13, 191.13, 191.13],
        'open': [190.0, 190.0, 190.0, 190.0],
        'high': [192.0, 192.0, 192.0, 192.0],
        'low': [189.0, 189.0, 189.0, 189.0],
        'volume': [1000000, 1000000, 1000000, 1000000]
    }, index=dates)
    
    print(f"Data index: {data.index}")
    print(f"Data index type: {type(data.index)}")
    print(f"First date: {data.index[0]}, type: {type(data.index[0])}")
    
    # Test the should_exit method
    entry_date = '2023-04-12'
    entry_price = 191.13
    
    print(f"\nTesting should_exit with entry_date={entry_date}, entry_price={entry_price}")
    
    for i in range(len(data)):
        current_date = data.index[i]
        print(f"\nDay {i}: {current_date}")
        
        should_exit, reason = strategy.should_exit(data, i, entry_price, entry_date)
        print(f"  Should exit: {should_exit}")
        print(f"  Reason: {reason}")

if __name__ == "__main__":
    test_date_parsing() 