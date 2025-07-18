#!/usr/bin/env python3
"""
Test script to force an exit scenario.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.strategies.macd_strategy import MACDStrategy
from src.data_engine.data_engine import DataEngine
from src.indicators.indicators import TechnicalIndicators

def test_forced_exit():
    """Test exit logic with a scenario that should definitely trigger an exit."""
    
    # Initialize components
    data_engine = DataEngine()
    indicators_calc = TechnicalIndicators()
    
    # Get data for AAPL for 2023
    print("Fetching AAPL data for 2023...")
    data = data_engine.fetch_data('AAPL', '2023-01-01', '2023-12-31')
    print(f"Got {len(data)} data points")
    
    # Calculate indicators
    print("Calculating indicators...")
    data_with_indicators = indicators_calc.calculate_all_indicators(data)
    print(f"Data shape after indicators: {data_with_indicators.shape}")
    
    # Initialize strategy with proper configuration
    print("Initializing MACDStrategy...")
    strategy = MACDStrategy()
    
    # Set configuration manually with lower thresholds
    strategy.entry_conditions = {
        'weights': {'macd_crossover_up': 0.5, 'rsi_neutral': 0.3, 'price_above_ema_short': 0.1, 'price_above_ema_long': 0.1},
        'threshold': 0.3
    }
    strategy.exit_conditions = {
        'max_drawdown_pct': 7.0,
        'take_profit_pct': 5.0,  # Lower threshold to 5%
        'stop_loss_pct': 3.0
    }
    strategy.rsi_range = [40, 60]
    
    print(f"Strategy configured: exit_conditions={strategy.exit_conditions}")
    
    # Test exit signal with a scenario that should trigger take profit
    entry_price = 150.0
    entry_date = '2023-03-10'
    test_date = '2023-04-15'
    
    print(f"\n=== Testing forced exit scenario ===")
    print(f"Entry price: ${entry_price:.2f}")
    print(f"Entry date: {entry_date}")
    print(f"Test date: {test_date}")
    print(f"Take profit threshold: 5%")
    
    # Get data up to test date
    date_data = data_engine.fetch_data('AAPL', '2023-01-01', test_date)
    if date_data.empty:
        print(f"No data for {test_date}")
        return
        
    # Calculate indicators
    date_data_with_indicators = indicators_calc.calculate_all_indicators(date_data)
    
    # Test exit signal
    current_index = len(date_data_with_indicators) - 1
    current_row = date_data_with_indicators.iloc[current_index]
    current_price = current_row['close']
    
    print(f"Current price: ${current_price:.2f}")
    print(f"PnL: {((current_price - entry_price) / entry_price * 100):.2f}%")
    
    should_exit, exit_reason = strategy.should_exit(
        date_data_with_indicators, current_index, 
        entry_price, entry_date
    )
    
    print(f"\n=== Final result ===")
    print(f"should_exit: {should_exit}")
    print(f"exit_reason: {exit_reason}")

if __name__ == "__main__":
    test_forced_exit() 