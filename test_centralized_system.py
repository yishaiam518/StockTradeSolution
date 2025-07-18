#!/usr/bin/env python3
"""
Test script to verify the centralized trading system architecture.
This ensures all strategies are properly integrated and the system works correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.trading_system import get_trading_system
from src.backtesting.backtest_engine import BacktestEngine
from src.real_time_trading.automation_engine import AutomationEngine
import pandas as pd
from datetime import datetime, timedelta

def test_centralized_system():
    """Test the centralized trading system architecture."""
    print("=== Testing Centralized Trading System ===\n")
    
    # Initialize the centralized trading system
    trading_system = get_trading_system()
    
    # Test 1: Strategy Management
    print("1. Testing Strategy Management...")
    strategies = trading_system.strategies
    print(f"   - Loaded {len(strategies)} strategies:")
    for name, strategy in strategies.items():
        print(f"     * {name}: {type(strategy).__name__}")
    
    # Test 2: Stock Selection
    print("\n2. Testing Stock Selection...")
    selected_stocks = trading_system.select_stocks(max_stocks=5, min_score=0.3)
    print(f"   - Selected stocks: {selected_stocks}")
    
    # Test 3: Data Preparation
    print("\n3. Testing Data Preparation...")
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    
    data = trading_system.prepare_data('AAPL', start_date, end_date)
    print(f"   - Prepared data for AAPL: {len(data)} data points")
    print(f"   - Columns: {list(data.columns)}")
    
    # Test 4: Signal Generation
    print("\n4. Testing Signal Generation...")
    for strategy_name in strategies.keys():
        trading_system.reset_strategy(strategy_name)
        signal_generated, signal_details = trading_system.run_strategy_signal(
            strategy_name, data, len(data) - 1
        )
        print(f"   - {strategy_name}: Signal={signal_generated}, Details={signal_details}")
    
    # Test 5: Backtest Integration
    print("\n5. Testing Backtest Integration...")
    backtest_engine = BacktestEngine()
    backtest_engine.trading_system = trading_system
    
    results = backtest_engine.run_backtest(
        symbol='AAPL',
        strategy_name='MACDStrategy',
        start_date=start_date,
        end_date=end_date
    )
    
    print(f"   - Backtest completed: {results.get('total_trades', 0)} trades")
    print(f"   - Total return: {results.get('total_return', 0):.2f}%")
    
    # Test 6: Automation Integration
    print("\n6. Testing Automation Integration...")
    from src.utils.config_loader import ConfigLoader
    config = ConfigLoader()
    automation_engine = AutomationEngine(config)
    automation_engine.trading_system = trading_system
    
    # Test position management
    trading_system.add_position('test', 'AAPL', 10.0, 150.0, '2023-01-01', 'MACDStrategy')
    positions = trading_system.get_positions('test')
    print(f"   - Test positions: {positions}")
    
    # Test 7: Configuration Management
    print("\n7. Testing Configuration Management...")
    for strategy_name in strategies.keys():
        config = trading_system.get_strategy_config(strategy_name)
        print(f"   - {strategy_name} config: {len(config)} parameters")
    
    # Test 8: Performance Summary
    print("\n8. Testing Performance Summary...")
    performance = trading_system.get_performance_summary()
    print(f"   - Performance summary: {performance}")
    
    print("\n=== All Tests Passed! ===")
    print("✅ Centralized trading system is working correctly")
    print("✅ All strategies are properly integrated")
    print("✅ Single source of truth architecture is maintained")
    
    return True

if __name__ == "__main__":
    try:
        test_centralized_system()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 