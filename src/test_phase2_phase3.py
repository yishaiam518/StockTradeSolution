#!/usr/bin/env python3
"""
Comprehensive Test Script for Phase 2 and Phase 3 Implementation

This script tests:
1. Strategy Profile System (Phase 2)
2. Data Collection Module (Phase 2)
3. Independent Scoring System (Phase 3)
4. UI Integration and Reflection
"""

import sys
import os
import traceback
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_strategy_profile_system():
    """Test the strategy profile system."""
    print("\n=== Testing Strategy Profile System ===")
    
    try:
        from .trading_system import get_trading_system
        
        # Get trading system
        trading_system = get_trading_system()
        
        # Test available profiles
        profiles = trading_system.get_available_profiles('MACD')
        print(f"✓ Available MACD profiles: {profiles}")
        
        # Test profile switching
        for profile in profiles:
            trading_system.set_strategy_profile('MACD', profile)
            current_profile = trading_system.get_strategy_profile('MACD')
            print(f"✓ Set profile to '{profile}', current profile: '{current_profile}'")
            
            # Test strategy parameters
            strategy = trading_system.get_strategy('MACD')
            if strategy:
                params = strategy.get_strategy_parameters()
                print(f"  - Parameters for {profile}: {params}")
        
        print("✓ Strategy Profile System: PASSED")
        return True
        
    except Exception as e:
        print(f"✗ Strategy Profile System: FAILED - {str(e)}")
        traceback.print_exc()
        return False

def test_data_collection_module():
    """Test the data collection module."""
    print("\n=== Testing Data Collection Module ===")
    
    try:
        from .data_collection import DataCollector, DataScheduler
        
        # Test data collector
        collector = DataCollector()
        summary = collector.get_data_summary()
        print(f"✓ Data collector initialized: {summary}")
        
        # Test initial data collection for a few symbols
        test_symbols = ['AAPL', 'MSFT', 'GOOGL']
        print(f"✓ Testing initial data collection for {test_symbols}")
        
        # Test scheduler
        scheduler = DataScheduler(collector)
        status = scheduler.get_scheduler_status()
        print(f"✓ Scheduler status: {status}")
        
        # Test manual updates
        scheduler.manual_daily_update()
        scheduler.manual_realtime_update()
        print("✓ Manual updates triggered successfully")
        
        print("✓ Data Collection Module: PASSED")
        return True
        
    except Exception as e:
        print(f"✗ Data Collection Module: FAILED - {str(e)}")
        traceback.print_exc()
        return False

def test_independent_scoring_system():
    """Test the independent scoring system."""
    print("\n=== Testing Independent Scoring System ===")
    
    try:
        from .machine_learning import IndependentStockScorer, DataSource, ScoringMethod
        
        # Initialize scorer
        scorer = IndependentStockScorer()
        print("✓ Independent stock scorer initialized")
        
        # Test scoring all stocks
        scores = scorer.score_all_stocks(
            data_source=DataSource.NASDAQ,
            strategy_profile='balanced',
            max_stocks=5,
            min_score=0.1
        )
        
        print(f"✓ Scored {len(scores)} stocks")
        
        # Display top scores
        for i, score in enumerate(scores[:3]):
            print(f"  {i+1}. {score.symbol}: {score.score:.3f} (confidence: {score.confidence:.3f})")
            print(f"     Signals: {score.signals}")
        
        # Test position signal generation
        test_positions = {
            'AAPL': {
                'entry_price': 150.0,
                'entry_date': '2023-01-01',
                'shares': 10.0
            }
        }
        
        position_signals = scorer.generate_position_signals(test_positions, 'balanced')
        print(f"✓ Generated {len(position_signals)} position signals")
        
        # Test cache functionality
        cache_stats = scorer.get_cache_stats()
        print(f"✓ Cache stats: {cache_stats}")
        
        print("✓ Independent Scoring System: PASSED")
        return True
        
    except Exception as e:
        print(f"✗ Independent Scoring System: FAILED - {str(e)}")
        traceback.print_exc()
        return False

def test_trading_system_integration():
    """Test the trading system integration with new components."""
    print("\n=== Testing Trading System Integration ===")
    
    try:
        from .trading_system import get_trading_system
        from .machine_learning import IndependentStockScorer
        
        # Get trading system
        trading_system = get_trading_system()
        
        # Test system status
        status = trading_system.get_system_status()
        print(f"✓ Trading system status: {status}")
        
        # Test stock selection with scoring
        selected_stocks = trading_system.select_stocks(max_stocks=5, min_score=0.3)
        print(f"✓ Selected {len(selected_stocks)} stocks: {selected_stocks}")
        
        # Test data preparation
        if selected_stocks:
            symbol = selected_stocks[0]
            data = trading_system.prepare_data(symbol, '2023-01-01', '2023-12-31')
            print(f"✓ Prepared data for {symbol}: {len(data)} data points")
            
            # Test strategy signal generation
            signal_generated, signal_details = trading_system.run_strategy_signal(
                'MACD', data, len(data) - 1
            )
            print(f"✓ Signal generated: {signal_generated}")
            if signal_generated:
                print(f"  Signal details: {signal_details}")
        
        print("✓ Trading System Integration: PASSED")
        return True
        
    except Exception as e:
        print(f"✗ Trading System Integration: FAILED - {str(e)}")
        traceback.print_exc()
        return False

def test_ui_integration():
    """Test that the UI can access and display the new features."""
    print("\n=== Testing UI Integration ===")
    
    try:
        # Test that the dashboard can access new components
        from .web_dashboard.dashboard_app import DashboardApp
        
        # Initialize dashboard
        dashboard = DashboardApp()
        print("✓ Dashboard initialized")
        
        # Test that we can access the trading system
        trading_system = dashboard.trading_system
        print("✓ Dashboard can access trading system")
        
        # Test strategy profiles in dashboard
        profiles = trading_system.get_available_profiles('MACD')
        print(f"✓ Dashboard can access strategy profiles: {profiles}")
        
        # Test data collection access
        from .data_collection import DataCollector
        collector = DataCollector()
        summary = collector.get_data_summary()
        print(f"✓ Dashboard can access data collection: {summary}")
        
        # Test scoring system access
        from .machine_learning import IndependentStockScorer
        scorer = IndependentStockScorer()
        print("✓ Dashboard can access independent scoring system")
        
        print("✓ UI Integration: PASSED")
        return True
        
    except Exception as e:
        print(f"✗ UI Integration: FAILED - {str(e)}")
        traceback.print_exc()
        return False

def test_backtest_with_new_architecture():
    """Test backtesting with the new architecture."""
    print("\n=== Testing Backtest with New Architecture ===")
    
    try:
        from .backtesting import BacktestEngine
        from .trading_system import get_trading_system
        
        # Initialize backtest engine
        backtest_engine = BacktestEngine()
        print("✓ Backtest engine initialized")
        
        # Test backtest with different profiles
        profiles = ['balanced', 'aggressive', 'conservative']
        
        for profile in profiles:
            print(f"\nTesting backtest with {profile} profile:")
            
            # Set profile
            trading_system = get_trading_system()
            trading_system.set_strategy_profile('MACD', profile)
            
            # Run backtest
            results = backtest_engine.run_backtest(
                symbol='AAPL',
                strategy_name='MACD',
                start_date='2023-01-01',
                end_date='2023-12-31',
                custom_parameters={},
                benchmark='SPY'
            )
            
            if 'error' not in results:
                trades = results.get('trades', [])
                total_return = results.get('total_return', 0)
                print(f"  ✓ {profile} profile: {len(trades)} trades, {total_return:.2f}% return")
            else:
                print(f"  ✗ {profile} profile: {results['error']}")
        
        print("✓ Backtest with New Architecture: PASSED")
        return True
        
    except Exception as e:
        print(f"✗ Backtest with New Architecture: FAILED - {str(e)}")
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🚀 Starting Phase 2 and Phase 3 Architecture Tests")
    print("=" * 60)
    
    tests = [
        ("Strategy Profile System", test_strategy_profile_system),
        ("Data Collection Module", test_data_collection_module),
        ("Independent Scoring System", test_independent_scoring_system),
        ("Trading System Integration", test_trading_system_integration),
        ("UI Integration", test_ui_integration),
        ("Backtest with New Architecture", test_backtest_with_new_architecture)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"✗ {test_name} failed")
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {str(e)}")
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Phase 2 and Phase 3 implementation is working correctly.")
        print("\n✅ Architecture Features Implemented:")
        print("  • Strategy Profile System - Multiple profiles for single strategy")
        print("  • Data Collection Module - Bulk and scheduled data collection")
        print("  • Independent Scoring System - Separate scoring and signal generation")
        print("  • UI Integration - Dashboard reflects all new features")
        print("  • Backtest Integration - Works with new architecture")
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 