#!/usr/bin/env python3
"""
Debug script to check what columns are being created by indicators.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data_engine.data_engine import DataEngine
from src.indicators.indicators import TechnicalIndicators

def debug_columns():
    """Debug what columns are being created."""
    print("=== DEBUGGING COLUMNS ===")
    
    # Initialize components
    data_engine = DataEngine()
    indicators = TechnicalIndicators()
    
    # Fetch data
    data = data_engine.fetch_data("AAPL", "2023-01-01", "2023-12-31", force_refresh=True)
    print(f"Raw data columns: {list(data.columns)}")
    
    # Calculate indicators
    data_with_indicators = indicators.calculate_all_indicators(data)
    print(f"Data with indicators columns: {list(data_with_indicators.columns)}")
    
    # Check for MACD-related columns
    macd_columns = [col for col in data_with_indicators.columns if 'macd' in col.lower()]
    print(f"MACD-related columns: {macd_columns}")
    
    # Check for RSI-related columns
    rsi_columns = [col for col in data_with_indicators.columns if 'rsi' in col.lower()]
    print(f"RSI-related columns: {rsi_columns}")
    
    # Check for EMA-related columns
    ema_columns = [col for col in data_with_indicators.columns if 'ema' in col.lower()]
    print(f"EMA-related columns: {ema_columns}")
    
    # Show first few rows to see the data
    print(f"\nFirst 5 rows of data with indicators:")
    print(data_with_indicators.head())
    
    # Check if specific columns exist
    required_columns = [
        'macd_line', 'macd_signal', 'macd_crossover_up', 'macd_crossover_down',
        'rsi', 'ema_short', 'ema_long', 'price_above_ema_short', 'price_above_ema_long'
    ]
    
    print(f"\nChecking required columns:")
    for col in required_columns:
        exists = col in data_with_indicators.columns
        print(f"  {col}: {'✓' if exists else '❌'}")

if __name__ == "__main__":
    debug_columns() 