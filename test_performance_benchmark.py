#!/usr/bin/env python3
"""
Performance Benchmark Test for StockTradeSolution
Tests system performance with different data sizes and configurations
"""

import sys
import os
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def create_test_data(days=365, symbols=10):
    """Create test data of specified size"""
    dates = pd.date_range(start='2023-01-01', periods=days, freq='D')
    
    data = {}
    for i in range(symbols):
        symbol = f'STOCK_{i:02d}'
        data[symbol] = pd.DataFrame({
            'Open': np.random.uniform(50, 200, len(dates)),
            'High': np.random.uniform(60, 220, len(dates)),
            'Low': np.random.uniform(40, 180, len(dates)),
            'Close': np.random.uniform(50, 200, len(dates)),
            'Volume': np.random.randint(100000, 5000000, len(dates))
        }, index=dates)
    
    return data

def benchmark_scoring_system():
    """Benchmark the unified scoring system"""
    print("📊 Benchmarking Scoring System...")
    
    try:
        from src.machine_learning.stock_scorer import UnifiedStockScorer
        from src.strategies.macd_canonical_strategy import MACDCanonicalStrategy
        
        scorer = UnifiedStockScorer()
        strategy = MACDCanonicalStrategy()
        
        # Test different data sizes
        data_sizes = [30, 90, 180, 365]  # days
        symbol_counts = [5, 10, 20, 50]
        
        results = []
        
        for days in data_sizes:
            for symbols in symbol_counts:
                print(f"   Testing {days} days, {symbols} symbols...")
                
                # Create test data
                start_time = time.time()
                test_data = create_test_data(days, symbols)
                data_creation_time = time.time() - start_time
                
                # Test scoring
                start_time = time.time()
                scores = scorer.score_stocks(
                    test_data,
                    strategy=strategy,
                    profile='conservative',
                    mode='backtesting'
                )
                scoring_time = time.time() - start_time
                
                results.append({
                    'days': days,
                    'symbols': symbols,
                    'data_creation_time': data_creation_time,
                    'scoring_time': scoring_time,
                    'total_time': data_creation_time + scoring_time,
                    'data_points': days * symbols
                })
                
                print(f"      ✅ Completed in {scoring_time:.2f}s")
        
        # Print results
        print("\n📈 Scoring System Performance Results:")
        print("=" * 60)
        for result in results:
            print(f"   {result['days']:3d} days, {result['symbols']:2d} symbols: "
                  f"{result['scoring_time']:6.2f}s ({result['data_points']:4d} data points)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Scoring benchmark failed: {e}")
        return False

def benchmark_backtesting_engine():
    """Benchmark the backtesting engine"""
    print("📊 Benchmarking Backtesting Engine...")
    
    try:
        from src.backtesting.backtest_engine import BacktestEngine
        
        engine = BacktestEngine()
        
        # Test different data sizes
        data_sizes = [30, 90, 180, 365]  # days
        
        results = []
        
        for days in data_sizes:
            print(f"   Testing {days} days...")
            
            # Create test data
            start_time = time.time()
            test_data = create_test_data(days, 1)  # Single stock
            data_creation_time = time.time() - start_time
            
            # Test backtesting
            start_time = time.time()
            results_backtest = engine.run_single_stock_backtest(
                list(test_data.values())[0],
                strategy_name='MACDCanonical',
                profile_name='conservative',
                initial_capital=10000
            )
            backtest_time = time.time() - start_time
            
            results.append({
                'days': days,
                'data_creation_time': data_creation_time,
                'backtest_time': backtest_time,
                'total_time': data_creation_time + backtest_time,
                'total_return': results_backtest.get('total_return', 0)
            })
            
            print(f"      ✅ Completed in {backtest_time:.2f}s (Return: {results_backtest.get('total_return', 0):.2f}%)")
        
        # Print results
        print("\n📈 Backtesting Engine Performance Results:")
        print("=" * 60)
        for result in results:
            print(f"   {result['days']:3d} days: {result['backtest_time']:6.2f}s "
                  f"(Return: {result['total_return']:6.2f}%)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Backtesting benchmark failed: {e}")
        return False

def benchmark_trading_system():
    """Benchmark the trading system"""
    print("📊 Benchmarking Trading System...")
    
    try:
        from src.trading_system import TradingSystem
        
        trading_system = TradingSystem()
        
        # Test different strategies and profiles
        strategies = ['MACDCanonical', 'MACDAggressive', 'MACDConservative']
        profiles = ['conservative', 'moderate', 'aggressive']
        
        # Create test data
        test_data = create_test_data(365, 1)  # 1 year, 1 stock
        stock_data = list(test_data.values())[0]
        
        results = []
        
        for strategy in strategies:
            for profile in profiles:
                print(f"   Testing {strategy} with {profile} profile...")
                
                start_time = time.time()
                signals = trading_system.generate_signals(
                    stock_data,
                    strategy_name=strategy,
                    profile_name=profile
                )
                signal_time = time.time() - start_time
                
                results.append({
                    'strategy': strategy,
                    'profile': profile,
                    'signal_time': signal_time,
                    'signal_count': len(signals)
                })
                
                print(f"      ✅ Completed in {signal_time:.2f}s ({len(signals)} signals)")
        
        # Print results
        print("\n📈 Trading System Performance Results:")
        print("=" * 60)
        for result in results:
            print(f"   {result['strategy']:15s} + {result['profile']:12s}: "
                  f"{result['signal_time']:6.2f}s ({result['signal_count']:3d} signals)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Trading system benchmark failed: {e}")
        return False

def benchmark_memory_usage():
    """Benchmark memory usage"""
    print("📊 Benchmarking Memory Usage...")
    
    try:
        import psutil
        import gc
        
        process = psutil.Process()
        
        # Test different data sizes
        data_sizes = [30, 90, 180, 365]  # days
        symbol_counts = [5, 10, 20, 50]
        
        results = []
        
        for days in data_sizes:
            for symbols in symbol_counts:
                print(f"   Testing {days} days, {symbols} symbols...")
                
                # Measure memory before
                gc.collect()
                memory_before = process.memory_info().rss / 1024 / 1024  # MB
                
                # Create test data
                test_data = create_test_data(days, symbols)
                
                # Measure memory after
                memory_after = process.memory_info().rss / 1024 / 1024  # MB
                memory_used = memory_after - memory_before
                
                results.append({
                    'days': days,
                    'symbols': symbols,
                    'memory_used_mb': memory_used,
                    'data_points': days * symbols,
                    'memory_per_point_kb': (memory_used * 1024) / (days * symbols)
                })
                
                print(f"      ✅ Memory used: {memory_used:.2f} MB")
                
                # Clean up
                del test_data
                gc.collect()
        
        # Print results
        print("\n📈 Memory Usage Results:")
        print("=" * 60)
        for result in results:
            print(f"   {result['days']:3d} days, {result['symbols']:2d} symbols: "
                  f"{result['memory_used_mb']:6.2f} MB "
                  f"({result['memory_per_point_kb']:.2f} KB per data point)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Memory benchmark failed: {e}")
        return False

def run_performance_benchmarks():
    """Run all performance benchmarks"""
    print("🚀 Starting Performance Benchmarks...")
    print("=" * 60)
    
    benchmarks = [
        benchmark_scoring_system,
        benchmark_backtesting_engine,
        benchmark_trading_system,
        benchmark_memory_usage
    ]
    
    results = []
    
    for benchmark in benchmarks:
        try:
            result = benchmark()
            results.append(result)
        except Exception as e:
            print(f"   ❌ Benchmark {benchmark.__name__} failed with exception: {e}")
            results.append(False)
    
    # Print summary
    print("=" * 60)
    print(f"📊 Benchmark Results:")
    print(f"   Benchmarks run: {len(benchmarks)}")
    print(f"   Passed: {sum(results)}")
    print(f"   Failed: {len(benchmarks) - sum(results)}")
    print(f"   Success rate: {(sum(results) / len(benchmarks) * 100):.1f}%")
    
    if all(results):
        print("\n🎉 All benchmarks completed successfully!")
    else:
        print("\n⚠️  Some benchmarks failed. Check the output above for details.")
    
    return all(results)

if __name__ == "__main__":
    success = run_performance_benchmarks()
    sys.exit(0 if success else 1) 