#!/usr/bin/env python3
"""
Test script to debug historical backtest signal generation.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.real_time_trading.automation_engine import HistoricalBacktestEngine
from src.utils.config_loader import config
from src.strategies.macd_strategy import MACDStrategy
from src.data_engine.data_engine import DataEngine
from src.indicators.indicators import TechnicalIndicators

def test_strategy_signals():
    """Test if the strategy can generate signals with historical data."""
    
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
    
    # Initialize strategy
    print("Initializing MACDStrategy...")
    strategy = MACDStrategy()
    print(f"Strategy initialized: {strategy}")
    print(f"Strategy entry weights: {strategy.entry_weights}")
    print(f"Strategy entry threshold: {strategy.entry_threshold}")
    
    # Test signal generation for a few dates
    test_dates = ['2023-01-03', '2023-01-04', '2023-01-05', '2023-01-06', '2023-01-09']
    
    for date in test_dates:
        print(f"\nTesting date: {date}")
        
        # Get data up to this date
        date_data = data_engine.fetch_data('AAPL', '2023-01-01', date)
        if date_data.empty:
            print(f"No data for {date}")
            continue
            
        # Calculate indicators
        date_data_with_indicators = indicators_calc.calculate_all_indicators(date_data)
        
        # Reset strategy
        strategy.current_position = None
        
        # Test entry signal
        current_index = len(date_data_with_indicators) - 1
        should_entry, entry_reason = strategy.should_entry(date_data_with_indicators, current_index)
        
        print(f"  should_entry: {should_entry}")
        print(f"  entry_reason: {entry_reason}")
        
        if should_entry:
            current_row = date_data_with_indicators.iloc[current_index]
            print(f"  Entry price: ${current_row['close']:.2f}")
        else:
            print(f"  No entry signal")

def test_historical_backtest_engine():
    """Test the HistoricalBacktestEngine directly."""
    
    print("\n" + "="*50)
    print("Testing HistoricalBacktestEngine")
    print("="*50)
    
    # Get config
    config_dict = config.config
    print(f"Config keys: {list(config_dict.keys())}")
    
    # Create engine
    engine = HistoricalBacktestEngine(config_dict, '2023-01-01', '2023-12-31', 'SPY')
    
    # Run backtest
    results = engine.run_backtest()
    
    print(f"Results keys: {list(results.keys())}")
    print(f"Total trades: {results.get('total_trades', 0)}")
    print(f"Trades: {len(results.get('trades', []))}")

if __name__ == "__main__":
    test_strategy_signals()
    test_historical_backtest_engine() 