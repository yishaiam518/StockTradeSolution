#!/usr/bin/env python3
"""
Test script to verify exit logic is working correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.strategies.macd_strategy import MACDStrategy
from src.utils.config_loader import config
import pandas as pd

def test_exit_logic():
    """Test the exit logic with a simple scenario."""
    
    print("Testing exit logic...")
    
    # Get config
    config_dict = config.config
    strategy_config = config_dict.get('strategies', {}).get('MACDStrategy', {})
    
    # Create strategy with config
    strategy = MACDStrategy(config_dict=strategy_config)
    
    print(f"Strategy config: {strategy_config}")
    print(f"Strategy entry conditions: {strategy.entry_conditions}")
    print(f"Strategy exit conditions: {strategy.exit_conditions}")
    
    # Create sample data with a position that should trigger exit
    data = pd.DataFrame({
        'close': [100, 95, 90, 85, 80],  # Declining prices
        'date': ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05'],
        'macd_crossover_down': [False, False, True, False, False],
        'price_below_ema_short': [False, False, True, True, True],
        'rsi': [50, 45, 40, 35, 30]
    })
    
    # Test exit logic
    entry_price = 100.0
    entry_date = '2023-01-01'
    current_index = 4  # Last row
    
    should_exit, exit_reason = strategy.should_exit(data, current_index, entry_price, entry_date)
    
    print(f"Should exit: {should_exit}")
    print(f"Exit reason: {exit_reason}")
    
    # Test with a position that has gained
    data_gain = pd.DataFrame({
        'close': [100, 105, 110, 115, 120],  # Rising prices
        'date': ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05'],
        'macd_crossover_down': [False, False, False, False, True],
        'price_below_ema_short': [False, False, False, False, True],
        'rsi': [50, 55, 60, 65, 70]
    })
    
    should_exit_gain, exit_reason_gain = strategy.should_exit(data_gain, current_index, entry_price, entry_date)
    
    print(f"Should exit (gain): {should_exit_gain}")
    print(f"Exit reason (gain): {exit_reason_gain}")

if __name__ == "__main__":
    test_exit_logic() 