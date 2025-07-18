#!/usr/bin/env python3
"""
Test script to verify exit signal generation with extreme scenarios.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.strategies.macd_strategy import MACDStrategy
from src.data_engine.data_engine import DataEngine
from src.indicators.indicators import TechnicalIndicators

def test_extreme_exit_scenarios():
    """Test exit signals with extreme scenarios."""
    
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
    
    print(f"Strategy configured: exit_conditions={strategy.exit_conditions}")
    
    # Test with different scenarios
    scenarios = [
        {'entry_price': 150.0, 'entry_date': '2023-03-10', 'test_date': '2023-03-15', 'description': 'Normal scenario'},
        {'entry_price': 150.0, 'entry_date': '2023-03-10', 'test_date': '2023-03-20', 'description': 'Take profit scenario (20% gain)'},
        {'entry_price': 150.0, 'entry_date': '2023-03-10', 'test_date': '2023-03-25', 'description': 'Stop loss scenario (3% loss)'},
        {'entry_price': 150.0, 'entry_date': '2023-03-10', 'test_date': '2023-04-15', 'description': 'Long hold scenario'},
    ]
    
    for scenario in scenarios:
        print(f"\n=== Testing: {scenario['description']} ===")
        
        # Get data up to test date
        date_data = data_engine.fetch_data('AAPL', '2023-01-01', scenario['test_date'])
        if date_data.empty:
            print(f"No data for {scenario['test_date']}")
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
        print(f"  exit_reason: {exit_reason}")

if __name__ == "__main__":
    test_extreme_exit_scenarios() 