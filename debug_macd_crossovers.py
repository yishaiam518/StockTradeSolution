#!/usr/bin/env python3
"""
Debug script to check MACD crossovers and strategy behavior.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data_engine.data_engine import DataEngine
from src.indicators.indicators import TechnicalIndicators
from src.strategies.macd_strategy import MACDStrategy
from src.utils.config_loader import config
from src.utils.logger import logger
import pandas as pd

def debug_macd_crossovers():
    """Debug MACD crossovers and strategy behavior."""
    print("=== DEBUGGING MACD CROSSOVERS ===")
    
    # Initialize components
    data_engine = DataEngine()
    indicators = TechnicalIndicators()
    
    # Get strategy configuration
    strategies_config = config.get_strategies_config()
    available_strategies = strategies_config.get('available', [])
    
    # Find MACDStrategy configuration
    strategy_config = None
    for strat in available_strategies:
        if strat.get('name') == 'MACDStrategy':
            strategy_config = strat
            break
    
    if not strategy_config:
        print("❌ MACDStrategy configuration not found!")
        return
    
    print(f"✅ Found MACDStrategy configuration: {strategy_config['name']}")
    
    # Create strategy with configuration
    strategy = MACDStrategy(config_dict=strategy_config)
    
    # Test with different symbols and time periods
    test_cases = [
        ("AAPL", "2023-01-01", "2023-12-31"),
        ("MSFT", "2023-01-01", "2023-12-31"),
        ("TSLA", "2023-01-01", "2023-12-31"),
    ]
    
    for symbol, start_date, end_date in test_cases:
        print(f"\n--- Testing {symbol} from {start_date} to {end_date} ---")
        
        try:
            # Fetch data
            data = data_engine.fetch_data(symbol, start_date, end_date, force_refresh=True)
            print(f"   Raw data shape: {data.shape}")
            print(f"   Date range: {data.index.min()} to {data.index.max()}")
            
            # Calculate indicators
            data_with_indicators = indicators.calculate_all_indicators(data)
            print(f"   Data with indicators shape: {data_with_indicators.shape}")
            
            # Check MACD crossovers
            macd_crossovers_up = data_with_indicators['macd_crossover_up'].sum()
            macd_crossovers_down = data_with_indicators['macd_crossover_down'].sum()
            print(f"   MACD crossovers up: {macd_crossovers_up}")
            print(f"   MACD crossovers down: {macd_crossovers_down}")
            
            # Test strategy entry signals
            entry_signals = 0
            exit_signals = 0
            
            for i in range(len(data_with_indicators)):
                should_entry, entry_reason = strategy.should_entry(data_with_indicators, i)
                if should_entry:
                    entry_signals += 1
                    print(f"   Entry signal at index {i}: {entry_reason.get('summary', 'No reason')}")
                
                # Test exit if we have a position
                if strategy.current_position:
                    should_exit, exit_reason = strategy.should_exit(
                        data_with_indicators, i, 
                        strategy.current_position['entry_price'],
                        strategy.current_position['entry_date']
                    )
                    if should_exit:
                        exit_signals += 1
                        print(f"   Exit signal at index {i}: {exit_reason.get('summary', 'No reason')}")
            
            print(f"   Total entry signals: {entry_signals}")
            print(f"   Total exit signals: {exit_signals}")
            
            # Reset strategy for next test
            strategy.reset()
            
        except Exception as e:
            print(f"   ❌ Error testing {symbol}: {e}")
    
    print("\n=== DEBUG COMPLETE ===")

if __name__ == "__main__":
    debug_macd_crossovers() 