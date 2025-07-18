#!/usr/bin/env python3
"""
Debug script to test exit logic with detailed logging.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.strategies.macd_strategy import MACDStrategy
from src.data_engine.data_engine import DataEngine
from src.indicators.indicators import TechnicalIndicators

def debug_exit_logic():
    """Debug the exit logic with detailed logging."""
    
    # Initialize components
    data_engine = DataEngine()
    indicators_calc = TechnicalIndicators()
    
    # Get data for AAPL for 2023
    print("Fetching AAPL data for 2023...")
    data = data_engine.fetch_data('AAPL', '2023-01-01', '2023-04-15')
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
        'take_profit_pct': 10.0,  # Changed to 10% to match default
        'stop_loss_pct': 3.0
    }
    strategy.rsi_range = [40, 60]
    
    print(f"Strategy configured: exit_conditions={strategy.exit_conditions}")
    
    # Test exit signal with detailed logging
    entry_price = 150.0
    entry_date = '2023-03-10'
    test_date = '2023-04-15'
    
    print(f"\n=== Testing exit logic ===")
    print(f"Entry price: ${entry_price:.2f}")
    print(f"Entry date: {entry_date}")
    print(f"Test date: {test_date}")
    
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
    
    # Debug the exit logic step by step
    print(f"\n=== Debugging exit logic ===")
    
    # Check if we have enough data
    if current_index < 1:
        print("Not enough data")
        return
    
    # Calculate drawdown from entry
    drawdown_from_entry = (current_price - entry_price) / entry_price
    print(f"Drawdown from entry: {drawdown_from_entry*100:.2f}%")
    
    # Find the highest price since entry
    if 'date' in date_data_with_indicators.columns:
        print(f"Data has 'date' column")
        # Find the first row where the date matches entry_date
        entry_index = date_data_with_indicators.index[date_data_with_indicators['date'] == entry_date]
        print(f"Entry index search result: {entry_index}")
        if len(entry_index) > 0:
            entry_index = entry_index[0]
            print(f"Found entry index: {entry_index}")
        else:
            entry_index = current_index
            print(f"Entry date not found, using current_index: {entry_index}")
    else:
        entry_index = current_index
        print(f"No 'date' column, using current_index: {entry_index}")
    
    price_since_entry = date_data_with_indicators.iloc[entry_index:current_index + 1]['close']
    highest_price = price_since_entry.max()
    drawdown_from_peak = (current_price - highest_price) / highest_price
    
    print(f"Price since entry range: {entry_index} to {current_index}")
    print(f"Highest price since entry: ${highest_price:.2f}")
    print(f"Drawdown from peak: {drawdown_from_peak*100:.2f}%")
    
    # Check thresholds
    max_drawdown = strategy.exit_conditions.get('max_drawdown_pct', 5.0) / 100
    take_profit_pct = strategy.exit_conditions.get('take_profit_pct', 10.0) / 100
    stop_loss_pct = strategy.exit_conditions.get('stop_loss_pct', 3.0) / 100
    
    print(f"Thresholds:")
    print(f"  Max drawdown: {max_drawdown*100:.2f}%")
    print(f"  Take profit: {take_profit_pct*100:.2f}%")
    print(f"  Stop loss: {stop_loss_pct*100:.2f}%")
    
    # Check each exit condition
    print(f"\n=== Checking exit conditions ===")
    
    # 1. Drawdown protection
    if drawdown_from_peak < -max_drawdown:
        print(f"✓ Drawdown protection triggered: {drawdown_from_peak*100:.2f}% < -{max_drawdown*100:.2f}%")
    else:
        print(f"✗ Drawdown protection not triggered: {drawdown_from_peak*100:.2f}% >= -{max_drawdown*100:.2f}%")
    
    # 2. Take profit
    if drawdown_from_entry > take_profit_pct:
        print(f"✓ Take profit triggered: {drawdown_from_entry*100:.2f}% > {take_profit_pct*100:.2f}%")
    else:
        print(f"✗ Take profit not triggered: {drawdown_from_entry*100:.2f}% <= {take_profit_pct*100:.2f}%")
    
    # 3. Stop loss
    if drawdown_from_entry < -stop_loss_pct:
        print(f"✓ Stop loss triggered: {drawdown_from_entry*100:.2f}% < -{stop_loss_pct*100:.2f}%")
    else:
        print(f"✗ Stop loss not triggered: {drawdown_from_entry*100:.2f}% >= -{stop_loss_pct*100:.2f}%")
    
    # Now test the actual should_exit method
    should_exit, exit_reason = strategy.should_exit(
        date_data_with_indicators, current_index, 
        entry_price, entry_date
    )
    
    print(f"\n=== Final result ===")
    print(f"should_exit: {should_exit}")
    print(f"exit_reason: {exit_reason}")

if __name__ == "__main__":
    debug_exit_logic() 