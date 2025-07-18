#!/usr/bin/env python3
"""
Test script to verify exit signal generation.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.strategies.macd_strategy import MACDStrategy
from src.data_engine.data_engine import DataEngine
from src.indicators.indicators import TechnicalIndicators

def test_exit_signals():
    """Test if the strategy can generate exit signals."""
    
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
    
    # Set configuration manually
    strategy.entry_conditions = {
        'weights': {'macd_crossover_up': 0.5, 'rsi_neutral': 0.3, 'price_above_ema_short': 0.1, 'price_above_ema_long': 0.1},
        'threshold': 0.3
    }
    strategy.exit_conditions = {
        'max_drawdown_pct': 7.0,
        'take_profit_pct': 20.0,
        'stop_loss_pct': 3.0
    }
    strategy.rsi_range = [40, 60]
    
    print(f"Strategy configured: entry_conditions={strategy.entry_conditions}")
    print(f"Strategy configured: exit_conditions={strategy.exit_conditions}")
    
    # Test exit signal generation for a few dates
    test_dates = ['2023-03-15', '2023-03-16', '2023-03-17', '2023-03-20', '2023-03-21']
    
    for date in test_dates:
        print(f"\nTesting exit signals for date: {date}")
        
        # Get data up to this date
        date_data = data_engine.fetch_data('AAPL', '2023-01-01', date)
        if date_data.empty:
            print(f"No data for {date}")
            continue
            
        # Calculate indicators
        date_data_with_indicators = indicators_calc.calculate_all_indicators(date_data)
        
        # Test exit signal with a hypothetical entry
        current_index = len(date_data_with_indicators) - 1
        entry_price = 150.0  # Hypothetical entry price
        entry_date = '2023-03-10'  # Hypothetical entry date
        
        should_exit, exit_reason = strategy.should_exit(
            date_data_with_indicators, current_index, 
            entry_price, entry_date
        )
        
        print(f"  should_exit: {should_exit}")
        print(f"  exit_reason: {exit_reason}")
        
        if should_exit:
            current_row = date_data_with_indicators.iloc[current_index]
            print(f"  Exit price: ${current_row['close']:.2f}")
            print(f"  Entry price: ${entry_price:.2f}")
            print(f"  PnL: {((current_row['close'] - entry_price) / entry_price * 100):.2f}%")
        else:
            print(f"  No exit signal")

if __name__ == "__main__":
    test_exit_signals() 