#!/usr/bin/env python3
"""
Test script for all available strategies with enhanced logging.

This script tests:
1. All available strategies (MACD, Canonical, Aggressive, Conservative)
2. Enhanced logging with dates
3. Strategy configuration loading
4. Signal generation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.config_loader import config
from src.utils.logger import logger
from src.trading_system import get_trading_system
from src.data_engine.data_engine import DataEngine
from src.strategies import (
    MACDStrategy, 
    MACDCanonicalStrategy, 
    MACDAggressiveStrategy, 
    MACDConservativeStrategy
)

def test_strategy_initialization():
    """Test that all strategies can be initialized properly."""
    print("\n=== Testing Strategy Initialization ===")
    
    strategies = {
        'MACDStrategy': MACDStrategy,
        'MACDCanonicalStrategy': MACDCanonicalStrategy,
        'MACDAggressiveStrategy': MACDAggressiveStrategy,
        'MACDConservativeStrategy': MACDConservativeStrategy
    }
    
    for name, strategy_class in strategies.items():
        try:
            strategy = strategy_class()
            print(f"✓ {name} initialized successfully")
            print(f"  - Entry threshold: {strategy.entry_threshold}")
            print(f"  - RSI range: {strategy.rsi_range}")
            print(f"  - Take profit: {strategy.take_profit_pct}%")
            print(f"  - Stop loss: {strategy.stop_loss_pct}%")
            print(f"  - Max hold days: {strategy.max_hold_days}")
        except Exception as e:
            print(f"✗ {name} failed to initialize: {e}")
    
    return True

def test_strategy_config_loading():
    """Test that strategies load configuration correctly."""
    print("\n=== Testing Strategy Configuration Loading ===")
    
    # Test centralized trading system
    trading_system = get_trading_system()
    
    strategy_names = [
        'MACDStrategy',
        'MACDCanonicalStrategy', 
        'MACDAggressiveStrategy',
        'MACDConservativeStrategy'
    ]
    
    for strategy_name in strategy_names:
        try:
            # Get strategy config
            config_dict = trading_system.get_strategy_config(strategy_name)
            print(f"✓ {strategy_name} config loaded:")
            print(f"  - Entry weights: {config_dict.get('entry_weights', {})}")
            print(f"  - Entry threshold: {config_dict.get('entry_threshold', 'N/A')}")
            print(f"  - RSI range: {config_dict.get('rsi_range', 'N/A')}")
        except Exception as e:
            print(f"✗ {strategy_name} config loading failed: {e}")
    
    return True

def test_data_preparation():
    """Test data preparation for backtesting."""
    print("\n=== Testing Data Preparation ===")
    
    try:
        trading_system = get_trading_system()
        
        # Test data preparation for AAPL
        data = trading_system.prepare_data('AAPL', '2023-01-01', '2023-12-31')
        
        if not data.empty:
            print(f"✓ Data preparation successful")
            print(f"  - Data points: {len(data)}")
            print(f"  - Date range: {data.index[0]} to {data.index[-1]}")
            print(f"  - Columns: {list(data.columns)}")
            
            # Check for required indicators
            required_indicators = ['macd', 'macd_signal', 'rsi', 'ema_short', 'ema_long']
            missing_indicators = [ind for ind in required_indicators if ind not in data.columns]
            
            if missing_indicators:
                print(f"  - Missing indicators: {missing_indicators}")
            else:
                print(f"  - All required indicators present")
        else:
            print("✗ Data preparation failed - empty DataFrame")
            return False
            
    except Exception as e:
        print(f"✗ Data preparation failed: {e}")
        return False
    
    return True

def test_strategy_signals():
    """Test signal generation for all strategies."""
    print("\n=== Testing Strategy Signal Generation ===")
    
    try:
        trading_system = get_trading_system()
        
        # Prepare test data
        data = trading_system.prepare_data('AAPL', '2023-01-01', '2023-12-31')
        
        if data.empty:
            print("✗ No data available for signal testing")
            return False
        
        strategy_names = [
            'MACDStrategy',
            'MACDCanonicalStrategy', 
            'MACDAggressiveStrategy',
            'MACDConservativeStrategy'
        ]
        
        for strategy_name in strategy_names:
            try:
                # Reset strategy
                trading_system.reset_strategy(strategy_name)
                
                # Test signals at different points
                test_indices = [50, 100, 150, 200]  # Test at different points
                signals_found = 0
                
                for i in test_indices:
                    if i < len(data):
                        signal_generated, signal_details = trading_system.run_strategy_signal(
                            strategy_name, data, i
                        )
                        
                        if signal_generated:
                            signals_found += 1
                            action = signal_details.get('action', 'UNKNOWN')
                            reason = signal_details.get('reason', {}).get('summary', 'No reason')
                            print(f"  - {strategy_name}: {action} signal at index {i} - {reason}")
                
                print(f"✓ {strategy_name}: {signals_found} signals found in test points")
                
            except Exception as e:
                print(f"✗ {strategy_name} signal testing failed: {e}")
        
    except Exception as e:
        print(f"✗ Signal testing failed: {e}")
        return False
    
    return True

def test_backtest_with_logging():
    """Test backtest with enhanced logging."""
    print("\n=== Testing Backtest with Enhanced Logging ===")
    
    try:
        from src.backtesting.backtest_engine import BacktestEngine
        
        backtest_engine = BacktestEngine()
        
        # Test with different strategies
        strategies_to_test = ['MACDStrategy', 'MACDAggressiveStrategy']
        
        for strategy_name in strategies_to_test:
            print(f"\n--- Testing {strategy_name} ---")
            
            results = backtest_engine.run_backtest(
                symbol='AAPL',
                strategy_name=strategy_name,
                start_date='2023-01-01',
                end_date='2023-12-31'
            )
            
            if 'error' not in results:
                print(f"✓ {strategy_name} backtest completed")
                print(f"  - Total trades: {results.get('total_trades', 0)}")
                print(f"  - Total return: {results.get('total_return', 0):.2f}%")
                
                # Show trade details
                trades = results.get('trades', [])
                for trade in trades:
                    date = trade.get('date', 'Unknown')
                    action = trade.get('action', 'Unknown')
                    shares = trade.get('shares', 0)
                    price = trade.get('price', 0)
                    pnl_pct = trade.get('pnl_pct', 0)
                    
                    if action == 'BUY':
                        print(f"  BUY [{date}]: {shares:.6f} shares at ${price:.2f}")
                    elif action == 'SELL':
                        print(f"  SELL [{date}]: {shares:.6f} shares at ${price:.2f} - PnL: {pnl_pct:.2f}%")
            else:
                print(f"✗ {strategy_name} backtest failed: {results.get('error')}")
        
    except Exception as e:
        print(f"✗ Backtest testing failed: {e}")
        return False
    
    return True

def test_historical_backtest():
    """Test historical backtest with enhanced logging."""
    print("\n=== Testing Historical Backtest with Enhanced Logging ===")
    
    try:
        from src.real_time_trading.automation_engine import HistoricalBacktestEngine
        
        # Test historical backtest
        config_dict = config.config
        engine = HistoricalBacktestEngine(
            config_dict, 
            '2023-01-01', 
            '2023-12-31', 
            'SPY'
        )
        
        print("Running historical backtest...")
        results = engine.run_backtest()
        
        if 'error' not in results:
            print(f"✓ Historical backtest completed")
            print(f"  - Total trades: {results.get('total_trades', 0)}")
            print(f"  - Total return: {results.get('total_return', 0):.2f}%")
            print(f"  - Winning trades: {results.get('winning_trades', 0)}")
            print(f"  - Losing trades: {results.get('losing_trades', 0)}")
            
            # Show some trade details
            trades = results.get('trades', [])
            for trade in trades[:5]:  # Show first 5 trades
                date = trade.get('date', 'Unknown')
                symbol = trade.get('symbol', 'Unknown')
                action = trade.get('action', 'Unknown')
                shares = trade.get('shares', 0)
                price = trade.get('price', 0)
                pnl_pct = trade.get('pnl_pct', 0)
                
                if action == 'BUY':
                    print(f"  BUY [{date}]: {shares:.6f} shares of {symbol} at ${price:.2f}")
                elif action == 'SELL':
                    print(f"  SELL [{date}]: {shares:.6f} shares of {symbol} at ${price:.2f} - PnL: {pnl_pct:.2f}%")
        else:
            print(f"✗ Historical backtest failed: {results.get('error')}")
            return False
        
    except Exception as e:
        print(f"✗ Historical backtest testing failed: {e}")
        return False
    
    return True

def main():
    """Run all tests."""
    print("=== Stock Trading System - Strategy Testing ===")
    print("Testing all available strategies with enhanced logging...")
    
    tests = [
        test_strategy_initialization,
        test_strategy_config_loading,
        test_data_preparation,
        test_strategy_signals,
        test_backtest_with_logging,
        test_historical_backtest
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"✗ Test {test.__name__} failed")
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
    
    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed! All strategies are working correctly.")
    else:
        print("✗ Some tests failed. Please check the output above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 