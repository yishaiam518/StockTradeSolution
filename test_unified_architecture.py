#!/usr/bin/env python3
"""
Test script for the new unified architecture.

This script tests:
1. Strategy+profile selection
2. Separate scoring lists for different modes
3. Unified trading system integration
4. Backtesting with new architecture
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.machine_learning.stock_scorer import UnifiedStockScorer, ScoringMode
from src.trading_system import get_trading_system
from src.backtesting.backtest_engine import BacktestEngine
from src.utils.logger import get_logger

def test_unified_scoring_system():
    """Test the unified scoring system with different modes."""
    print("\n=== Testing Unified Scoring System ===")
    
    try:
        # Initialize unified scorer
        scorer = UnifiedStockScorer()
        print("✓ Unified stock scorer initialized")
        
        # Test backtesting mode (single stock)
        print("\n--- Testing Backtesting Mode ---")
        backtest_scores = scorer.create_scoring_list(
            mode=ScoringMode.BACKTESTING,
            strategy="MACD",
            profile="balanced",
            symbol="AAPL",
            max_stocks=1,
            min_score=0.1
        )
        print(f"✓ Created backtesting scoring list with {len(backtest_scores)} stocks")
        
        # Test historical mode (multiple stocks)
        print("\n--- Testing Historical Mode ---")
        historical_scores = scorer.create_scoring_list(
            mode=ScoringMode.HISTORICAL,
            strategy="MACD",
            profile="canonical",
            max_stocks=5,
            min_score=0.3
        )
        print(f"✓ Created historical scoring list with {len(historical_scores)} stocks")
        
        # Test automation mode (watchlist)
        print("\n--- Testing Automation Mode ---")
        automation_scores = scorer.create_scoring_list(
            mode=ScoringMode.AUTOMATION,
            strategy="MACD",
            profile="aggressive",
            max_stocks=10,
            min_score=0.4
        )
        print(f"✓ Created automation scoring list with {len(automation_scores)} stocks")
        
        # Test trading signal generation
        print("\n--- Testing Trading Signal Generation ---")
        signals = scorer.generate_trading_signals(
            mode=ScoringMode.BACKTESTING,
            strategy="MACD",
            profile="balanced"
        )
        print(f"✓ Generated {len(signals)} trading signals")
        
        # Test cache statistics
        cache_stats = scorer.get_cache_stats()
        print(f"✓ Cache stats: {cache_stats}")
        
        print("✓ Unified Scoring System: PASSED")
        return True
        
    except Exception as e:
        print(f"✗ Unified Scoring System: FAILED - {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_trading_system_integration():
    """Test the trading system integration with unified scoring."""
    print("\n=== Testing Trading System Integration ===")
    
    try:
        # Get trading system
        trading_system = get_trading_system()
        print("✓ Trading system initialized")
        
        # Test strategy profile management
        print("\n--- Testing Strategy Profile Management ---")
        available_profiles = trading_system.get_available_profiles("MACD")
        print(f"✓ Available profiles for MACD: {available_profiles}")
        
        # Set strategy profile
        trading_system.set_strategy_profile("MACD", "conservative")
        current_profile = trading_system.get_strategy_profile("MACD")
        print(f"✓ Set MACD profile to: {current_profile}")
        
        # Test scoring list creation through trading system
        print("\n--- Testing Scoring List Creation ---")
        scoring_list = trading_system.create_scoring_list(
            mode=ScoringMode.BACKTESTING,
            strategy="MACD",
            profile="balanced",
            symbol="AAPL",
            max_stocks=1,
            min_score=0.1
        )
        print(f"✓ Created scoring list through trading system: {len(scoring_list)} stocks")
        
        # Test trading signal generation through trading system
        signals = trading_system.generate_trading_signals(
            mode=ScoringMode.BACKTESTING,
            strategy="MACD",
            profile="balanced"
        )
        print(f"✓ Generated trading signals through trading system: {len(signals)} signals")
        
        # Test stock selection
        selected_stocks = trading_system.select_stocks(max_stocks=5, min_score=0.3)
        print(f"✓ Selected stocks: {selected_stocks}")
        
        print("✓ Trading System Integration: PASSED")
        return True
        
    except Exception as e:
        print(f"✗ Trading System Integration: FAILED - {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_backtesting_engine():
    """Test the backtesting engine with new architecture."""
    print("\n=== Testing Backtesting Engine ===")
    
    try:
        # Initialize backtesting engine
        backtest_engine = BacktestEngine()
        print("✓ Backtesting engine initialized")
        
        # Test single stock backtest
        print("\n--- Testing Single Stock Backtest ---")
        results = backtest_engine.run_backtest(
            symbol="AAPL",
            strategy="MACD",
            profile="balanced",
            start_date="2023-01-01",
            end_date="2023-12-31"
        )
        
        if 'error' in results:
            print(f"✗ Single stock backtest failed: {results['error']}")
            return False
        
        print(f"✓ Single stock backtest completed")
        print(f"  - Total trades: {len(results.get('trades', []))}")
        print(f"  - Strategy: {results.get('strategy', 'N/A')}")
        print(f"  - Profile: {results.get('profile', 'N/A')}")
        
        if 'performance' in results:
            perf = results['performance']
            print(f"  - Total return: {perf.get('total_return', 0):.2f}%")
            print(f"  - Sharpe ratio: {perf.get('sharpe_ratio', 0):.2f}")
            print(f"  - Max drawdown: {perf.get('max_drawdown', 0):.2f}%")
        
        # Test historical backtest
        print("\n--- Testing Historical Backtest ---")
        historical_results = backtest_engine.run_historical_backtest(
            strategy="MACD",
            profile="canonical",
            start_date="2023-01-01",
            end_date="2023-12-31",
            benchmark="SPY"
        )
        
        if 'error' in historical_results:
            print(f"✗ Historical backtest failed: {historical_results['error']}")
            return False
        
        print(f"✓ Historical backtest completed")
        print(f"  - Total trades: {len(historical_results.get('trades', []))}")
        print(f"  - Symbols tested: {historical_results.get('symbols', [])}")
        
        if 'performance' in historical_results:
            perf = historical_results['performance']
            print(f"  - Total return: {perf.get('total_return', 0):.2f}%")
            print(f"  - Sharpe ratio: {perf.get('sharpe_ratio', 0):.2f}")
            print(f"  - Max drawdown: {perf.get('max_drawdown', 0):.2f}%")
        
        print("✓ Backtesting Engine: PASSED")
        return True
        
    except Exception as e:
        print(f"✗ Backtesting Engine: FAILED - {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_profile_configurations():
    """Test different profile configurations."""
    print("\n=== Testing Profile Configurations ===")
    
    try:
        trading_system = get_trading_system()
        
        profiles = ['balanced', 'canonical', 'aggressive', 'conservative']
        
        for profile in profiles:
            print(f"\n--- Testing {profile.upper()} Profile ---")
            
            # Set profile
            trading_system.set_strategy_profile("MACD", profile)
            current_profile = trading_system.get_strategy_profile("MACD")
            print(f"✓ Set profile to: {current_profile}")
            
            # Test scoring with this profile
            scoring_list = trading_system.create_scoring_list(
                mode=ScoringMode.BACKTESTING,
                strategy="MACD",
                profile=profile,
                symbol="AAPL",
                max_stocks=1,
                min_score=0.1
            )
            
            if scoring_list:
                score = scoring_list[0]
                print(f"✓ {profile} profile scoring: {score.symbol} = {score.score:.3f}")
            else:
                print(f"✗ No scoring results for {profile} profile")
        
        print("✓ Profile Configurations: PASSED")
        return True
        
    except Exception as e:
        print(f"✗ Profile Configurations: FAILED - {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests for the unified architecture."""
    print("🧪 Testing Unified Architecture")
    print("=" * 50)
    
    tests = [
        test_unified_scoring_system,
        test_trading_system_integration,
        test_backtesting_engine,
        test_profile_configurations
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Unified architecture is working correctly.")
    else:
        print("❌ Some tests failed. Please check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 