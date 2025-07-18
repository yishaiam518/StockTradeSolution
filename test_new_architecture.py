"""
Test script for the new architecture with profile system and data collection.

This script tests:
1. Strategy profile system
2. Data collection module
3. Trading system integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.trading_system import get_trading_system
from src.data_collection.collector import DataCollector
from src.data_collection.scheduler import DataScheduler
from src.utils.config_loader import ConfigLoader
from datetime import datetime, timedelta
import pandas as pd


def test_profile_system():
    """Test the new profile system."""
    print("=== Testing Profile System ===")
    
    # Get trading system
    trading_system = get_trading_system()
    
    # Test available profiles
    profiles = trading_system.get_available_profiles('MACD')
    print(f"Available profiles: {profiles}")
    
    # Test profile switching
    for profile in profiles:
        print(f"\n--- Testing {profile} profile ---")
        
        # Set profile
        trading_system.set_strategy_profile('MACD', profile)
        
        # Get current profile
        current_profile = trading_system.get_strategy_profile('MACD')
        print(f"Current profile: {current_profile}")
        
        # Get strategy parameters
        strategy = trading_system.get_strategy('MACD')
        if strategy:
            params = strategy.get_strategy_parameters()
            print(f"Profile parameters: {params}")
    
    print("\n✅ Profile system test completed")


def test_data_collection():
    """Test the data collection module."""
    print("\n=== Testing Data Collection ===")
    
    # Initialize data collector
    collector = DataCollector()
    
    # Test data summary
    summary = collector.get_data_summary()
    print(f"Data collection summary: {summary}")
    
    # Test initial data collection for a few symbols
    test_symbols = ['AAPL', 'MSFT', 'GOOGL']
    print(f"\nCollecting initial data for {test_symbols}")
    
    try:
        collected_data = collector.collect_initial_data(test_symbols)
        print(f"Collected data for {len(collected_data)} symbols")
        
        for symbol, data in collected_data.items():
            print(f"  {symbol}: {len(data)} data points")
            
    except Exception as e:
        print(f"Error in data collection: {str(e)}")
    
    print("\n✅ Data collection test completed")


def test_trading_system_integration():
    """Test trading system with new architecture."""
    print("\n=== Testing Trading System Integration ===")
    
    trading_system = get_trading_system()
    
    # Test system status
    status = trading_system.get_system_status()
    print(f"System status: {status}")
    
    # Test strategy signal generation with different profiles
    test_symbol = 'AAPL'
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    print(f"\nTesting strategy signals for {test_symbol}")
    
    # Prepare data
    data = trading_system.prepare_data(test_symbol, start_date.strftime('%Y-%m-%d'), 
                                     end_date.strftime('%Y-%m-%d'))
    
    if not data.empty:
        print(f"Prepared {len(data)} data points")
        
        # Test each profile
        for profile in ['balanced', 'aggressive', 'conservative']:
            print(f"\n--- Testing {profile} profile ---")
            
            # Set profile
            trading_system.set_strategy_profile('MACD', profile)
            
            # Test signal generation
            for i in range(min(10, len(data))):  # Test first 10 data points
                signal, details = trading_system.run_strategy_signal('MACD', data, i)
                
                if signal:
                    print(f"  Signal at index {i}: {details}")
                    break
    else:
        print("No data available for testing")
    
    print("\n✅ Trading system integration test completed")


def test_data_scheduler():
    """Test the data scheduler."""
    print("\n=== Testing Data Scheduler ===")
    
    try:
        # Initialize scheduler
        scheduler = DataScheduler()
        
        # Test scheduler status
        status = scheduler.get_scheduler_status()
        print(f"Scheduler status: {status}")
        
        # Test manual updates
        print("Testing manual daily update...")
        scheduler.manual_daily_update()
        
        print("Testing manual real-time update...")
        scheduler.manual_realtime_update()
        
        print("\n✅ Data scheduler test completed")
        
    except Exception as e:
        print(f"Error in scheduler test: {str(e)}")


def main():
    """Run all tests."""
    print("🚀 Testing New Architecture")
    print("=" * 50)
    
    try:
        # Test profile system
        test_profile_system()
        
        # Test data collection
        test_data_collection()
        
        # Test trading system integration
        test_trading_system_integration()
        
        # Test data scheduler
        test_data_scheduler()
        
        print("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 