#!/usr/bin/env python3
"""
Debug script to test strategy initialization and signal generation.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.strategies.macd_strategy import MACDStrategy
from src.data_engine import DataEngine
from src.indicators import TechnicalIndicators
import pandas as pd

def test_strategy():
    """Test strategy initialization and signal generation."""
    
    # Initialize components
    data_engine = DataEngine()
    indicators = TechnicalIndicators()
    
    # Fetch and prepare data
    print("Fetching data...")
    data = data_engine.fetch_data('AAPL', '2023-01-01', '2023-12-31')
    print(f"Raw data shape: {data.shape}")
    
    # Calculate indicators
    print("Calculating indicators...")
    data = indicators.calculate_all_indicators(data)
    print(f"Data with indicators shape: {data.shape}")
    
    # Check for required indicators
    required_indicators = [
        'macd_line', 'macd_signal', 'macd_crossover_up', 'macd_crossover_down',
        'rsi', 'ema_short', 'ema_long', 'price_above_ema_short', 'price_above_ema_long'
    ]
    
    print("\nChecking required indicators:")
    for indicator in required_indicators:
        if indicator in data.columns:
            print(f"✓ {indicator}: {data[indicator].sum()} True values")
        else:
            print(f"✗ {indicator}: MISSING")
    
    # Initialize strategy with working config
    print("\nInitializing strategy...")
    config_dict = {
        'entry_conditions': {
            'weights': {
                'macd_crossover_up': 0.5,
                'rsi_neutral': 0.3,
                'price_above_ema_short': 0.1,
                'price_above_ema_long': 0.1
            },
            'threshold': 0.3,
            'rsi_range': [40, 60]
        },
        'exit_conditions': {
            'take_profit_pct': 5.0,
            'stop_loss_pct': 3.0,
            'max_drawdown_pct': 5.0,
            'max_hold_days': 252
        }
    }
    
    strategy = MACDStrategy(config_dict)
    
    # Test entry signals
    print("\nTesting entry signals...")
    entry_signals = 0
    for i in range(1, min(50, len(data))):  # Test first 50 data points
        should_entry, reason = strategy.should_entry(data, i)
        if should_entry:
            entry_signals += 1
            print(f"Entry signal at index {i}: {reason}")
    
    print(f"Total entry signals in first 50 points: {entry_signals}")
    
    # Test a few specific points
    print("\nTesting specific data points:")
    for i in [10, 20, 30, 40]:
        if i < len(data):
            row = data.iloc[i]
            print(f"\nIndex {i}:")
            print(f"  Close: {row['close']}")
            print(f"  MACD crossover up: {row.get('macd_crossover_up', False)}")
            print(f"  RSI: {row.get('rsi', 0):.2f}")
            print(f"  Price above EMA short: {row.get('price_above_ema_short', False)}")
            print(f"  Price above EMA long: {row.get('price_above_ema_long', False)}")
            
            should_entry, reason = strategy.should_entry(data, i)
            print(f"  Should entry: {should_entry}")
            if should_entry:
                print(f"  Reason: {reason}")

if __name__ == "__main__":
    test_strategy() 