#!/usr/bin/env python3
"""
Test script to verify the exit logic fix and 5% thresholds.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.strategies.macd_strategy import MACDStrategy
from src.data_engine.data_engine import DataEngine
from src.indicators.indicators import TechnicalIndicators
from src.utils.config_loader import config

def test_exit_fix():
    """Test the exit logic fix with 5% thresholds."""
    
    print("=== TESTING EXIT LOGIC FIX ===")
    
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
    
    # Initialize strategy with 5% thresholds
    print("Initializing MACDStrategy with 5% thresholds...")
    strategy = MACDStrategy()
    
    # Set configuration with 5% thresholds
    strategy.entry_conditions = {
        'weights': {'macd_crossover_up': 0.5, 'rsi_neutral': 0.3, 'price_above_ema_short': 0.1, 'price_above_ema_long': 0.1},
        'threshold': 0.3
    }
    strategy.exit_conditions = {
        'max_drawdown_pct': 5.0,  # 5% drawdown
        'take_profit_pct': 5.0,   # 5% take profit
        'stop_loss_pct': 3.0,     # 3% stop loss
        'max_hold_days': 30       # 30 days max hold
    }
    strategy.rsi_range = [40, 60]
    
    print(f"Strategy configured: exit_conditions={strategy.exit_conditions}")
    
    # Test exit signal generation
    print("\n--- Testing Exit Signal Generation ---")
    
    # Test with a scenario that should trigger take profit
    entry_price = 150.0
    entry_date = '2023-03-10'
    test_date = '2023-04-15'
    
    print(f"Testing scenario:")
    print(f"  Entry price: ${entry_price:.2f}")
    print(f"  Entry date: {entry_date}")
    print(f"  Test date: {test_date}")
    print(f"  Take profit threshold: 5%")
    
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
    
    print(f"\n=== Exit Signal Test Result ===")
    print(f"should_exit: {should_exit}")
    print(f"exit_reason: {exit_reason}")
    
    # Test JSON serialization
    print(f"\n=== JSON Serialization Test ===")
    try:
        import json
        # Test that the exit reason can be serialized
        json_str = json.dumps(exit_reason)
        print(f"✅ JSON serialization successful: {json_str}")
    except Exception as e:
        print(f"❌ JSON serialization failed: {e}")
    
    # Test multiple scenarios
    print(f"\n--- Testing Multiple Scenarios ---")
    
    scenarios = [
        {'entry_price': 150.0, 'entry_date': '2023-03-10', 'test_date': '2023-03-15', 'description': 'Normal scenario'},
        {'entry_price': 150.0, 'entry_date': '2023-03-10', 'test_date': '2023-03-20', 'description': 'Take profit scenario (5% gain)'},
        {'entry_price': 150.0, 'entry_date': '2023-03-10', 'test_date': '2023-03-25', 'description': 'Stop loss scenario (3% loss)'},
        {'entry_price': 150.0, 'entry_date': '2023-03-10', 'test_date': '2023-04-15', 'description': 'Long hold scenario'},
    ]
    
    for scenario in scenarios:
        print(f"\nTesting: {scenario['description']}")
        
        # Get data up to test date
        date_data = data_engine.fetch_data('AAPL', '2023-01-01', scenario['test_date'])
        if date_data.empty:
            print(f"  No data for {scenario['test_date']}")
            continue
            
        # Calculate indicators
        date_data_with_indicators = indicators_calc.calculate_all_indicators(date_data)
        
        # Test exit signal
        current_index = len(date_data_with_indicators) - 1
        current_row = date_data_with_indicators.iloc[current_index]
        current_price = current_row['close']
        
        print(f"  Entry price: ${scenario['entry_price']:.2f}")
        print(f"  Current price: ${current_price:.2f}")
        print(f"  PnL: {((current_price - scenario['entry_price']) / scenario['entry_price'] * 100):.2f}%")
        
        should_exit, exit_reason = strategy.should_exit(
            date_data_with_indicators, current_index, 
            scenario['entry_price'], scenario['entry_date']
        )
        
        print(f"  should_exit: {should_exit}")
        print(f"  exit_reason: {exit_reason.get('summary', 'Unknown')}")
        
        if should_exit:
            print(f"  ✅ EXIT SIGNAL GENERATED")
        else:
            print(f"  ❌ No exit signal")
    
    print(f"\n=== TEST COMPLETED ===")

if __name__ == "__main__":
    test_exit_fix() 