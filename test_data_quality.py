#!/usr/bin/env python3
"""
Test Data Quality

Check if the AAPL data has realistic price movements.
"""

import sys
import os
import pandas as pd

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.backtesting.backtest_engine import BacktestEngine

def test_data_quality():
    """Test the quality of AAPL data."""
    print("Testing AAPL data quality...")
    
    # Initialize backtest engine
    engine = BacktestEngine()
    
    # Get AAPL data
    aapl_data = engine._get_cached_or_fetch_data('AAPL', '2023-01-01', '2023-12-31')
    
    print(f"Data shape: {aapl_data.shape}")
    print(f"Date range: {aapl_data.index.min()} to {aapl_data.index.max()}")
    
    # Check price statistics
    print(f"\nPrice Statistics:")
    print(f"  Close price min: ${aapl_data['close'].min():.2f}")
    print(f"  Close price max: ${aapl_data['close'].max():.2f}")
    print(f"  Close price mean: ${aapl_data['close'].mean():.2f}")
    print(f"  Close price std: ${aapl_data['close'].std():.2f}")
    
    # Check for price variation
    unique_prices = aapl_data['close'].nunique()
    print(f"  Unique prices: {unique_prices}")
    
    if unique_prices == 1:
        print("❌ CRITICAL: All prices are the same! This is unrealistic data.")
        print(f"  All prices: ${aapl_data['close'].iloc[0]:.2f}")
    else:
        print(f"✅ Price variation detected: {unique_prices} different prices")
    
    # Show sample of prices
    print(f"\nSample prices (first 10):")
    for i, (date, row) in enumerate(aapl_data.head(10).iterrows()):
        print(f"  {date.strftime('%Y-%m-%d')}: ${row['close']:.2f}")
    
    # Check for price changes
    price_changes = aapl_data['close'].diff()
    print(f"\nPrice change statistics:")
    print(f"  Max daily gain: ${price_changes.max():.2f}")
    print(f"  Max daily loss: ${price_changes.min():.2f}")
    print(f"  Days with price changes: {(price_changes != 0).sum()}")
    print(f"  Days with no change: {(price_changes == 0).sum()}")

if __name__ == "__main__":
    test_data_quality() 