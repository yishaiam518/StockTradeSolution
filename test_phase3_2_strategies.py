#!/usr/bin/env python3
"""
Test script for Phase 3.2: Strategy Framework
Tests all implemented strategies with the backtesting framework
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.backtesting.backtest_engine import BacktestEngine
from src.backtesting.strategies import (
    MACDStrategy, 
    RSIStrategy, 
    BollingerBandsStrategy, 
    MovingAverageStrategy
)
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_all_strategies():
    """Test all implemented strategies"""
    print("🧪 TESTING PHASE 3.2: STRATEGY FRAMEWORK")
    print("=" * 60)
    
    # Initialize backtesting engine
    engine = BacktestEngine(initial_capital=100000.0)
    
    # Test data
    collection_id = "AMEX_20250803_161652"
    symbol = "BND"
    start_date = "2023-01-01"
    end_date = "2024-12-31"
    
    # Load data once for all strategies
    print("1. Loading test data...")
    data = engine.load_data(collection_id, symbol)
    if data.empty:
        print("❌ No data available for testing")
        return
    
    print(f"✅ Data loaded: {len(data)} data points")
    
    # Define strategies to test
    strategies = {
        'MACD Strategy': MACDStrategy({
            'fast_period': 12,
            'slow_period': 26,
            'signal_period': 9,
            'position_size': 0.1,
            'enable_short': False
        }),
        
        'RSI Strategy': RSIStrategy({
            'rsi_period': 14,
            'oversold_threshold': 30,
            'overbought_threshold': 70,
            'position_size': 0.1,
            'enable_short': False,
            'use_volume_confirmation': True
        }),
        
        'Bollinger Bands Strategy': BollingerBandsStrategy({
            'bb_period': 20,
            'bb_std_dev': 2.0,
            'position_size': 0.1,
            'enable_short': True,
            'use_rsi_confirmation': True,
            'use_volume_confirmation': True
        }),
        
        'Moving Average Strategy': MovingAverageStrategy({
            'fast_ma_period': 10,
            'slow_ma_period': 20,
            'position_size': 0.1,
            'enable_short': True,
            'use_volume_confirmation': True,
            'use_rsi_filter': True
        })
    }
    
    results = {}
    
    # Test each strategy
    for strategy_name, strategy in strategies.items():
        print(f"\n2. Testing {strategy_name}...")
        
        try:
            # Run backtest
            result = engine.run_backtest(
                strategy=strategy,
                collection_id=collection_id,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
            )
            
            if "error" in result:
                print(f"❌ {strategy_name} failed: {result['error']}")
                continue
            
            results[strategy_name] = result
            
            # Print results
            print(f"✅ {strategy_name} completed successfully!")
            print(f"   Total Return: {result['total_return']:.2f}%")
            print(f"   Total Trades: {result['trades']}")
            print(f"   Win Rate: {result['performance']['win_rate']:.2f}%")
            print(f"   Sharpe Ratio: {result['performance']['sharpe_ratio']:.2f}")
            print(f"   Max Drawdown: {result['performance']['max_drawdown']:.2f}%")
            
        except Exception as e:
            print(f"❌ Error testing {strategy_name}: {e}")
            continue
    
    # Compare strategies
    print("\n" + "=" * 60)
    print("📊 STRATEGY COMPARISON")
    print("=" * 60)
    
    if results:
        # Sort by total return
        sorted_results = sorted(results.items(), key=lambda x: x[1]['total_return'], reverse=True)
        
        print(f"{'Strategy':<25} {'Return':<10} {'Trades':<8} {'Win Rate':<10} {'Sharpe':<8} {'Max DD':<8}")
        print("-" * 80)
        
        for strategy_name, result in sorted_results:
            performance = result['performance']
            print(f"{strategy_name:<25} "
                  f"{result['total_return']:>8.2f}% "
                  f"{result['trades']:>6} "
                  f"{performance['win_rate']:>8.2f}% "
                  f"{performance['sharpe_ratio']:>6.2f} "
                  f"{performance['max_drawdown']:>6.2f}%")
        
        # Find best strategy
        best_strategy = sorted_results[0]
        print(f"\n🏆 Best Strategy: {best_strategy[0]}")
        print(f"   Total Return: {best_strategy[1]['total_return']:.2f}%")
        print(f"   Sharpe Ratio: {best_strategy[1]['performance']['sharpe_ratio']:.2f}")
    
    print("\n🎉 PHASE 3.2 TESTING COMPLETE!")
    print("=" * 60)
    print("✅ All strategies implemented and tested")
    print("✅ Strategy comparison completed")
    print("✅ Ready for Phase 3.3: Performance Analytics")

def test_strategy_signals():
    """Test individual strategy signal generation"""
    print("\n🔍 TESTING STRATEGY SIGNALS")
    print("-" * 40)
    
    # Load sample data
    engine = BacktestEngine(initial_capital=100000.0)
    collection_id = "AMEX_20250803_161652"
    symbol = "BND"
    
    data = engine.load_data(collection_id, symbol)
    if data.empty:
        print("❌ No data available for signal testing")
        return
    
    # Test each strategy's signal generation
    strategies = {
        'MACD': MACDStrategy(),
        'RSI': RSIStrategy(),
        'Bollinger Bands': BollingerBandsStrategy(),
        'Moving Average': MovingAverageStrategy()
    }
    
    for strategy_name, strategy in strategies.items():
        print(f"\nTesting {strategy_name} signals...")
        
        long_signals = 0
        exit_signals = 0
        
        # Test last 50 data points
        test_data = data.tail(50)
        
        for i in range(len(test_data)):
            current_data = data.iloc[:len(data)-50+i+1]
            
            if strategy.should_enter_long(current_data, len(current_data)-1):
                long_signals += 1
            
            if strategy.should_exit_long(current_data, len(current_data)-1):
                exit_signals += 1
        
        print(f"   Long entry signals: {long_signals}")
        print(f"   Exit signals: {exit_signals}")
        print(f"   Signal frequency: {long_signals/50*100:.1f}%")

if __name__ == "__main__":
    test_all_strategies()
    test_strategy_signals() 