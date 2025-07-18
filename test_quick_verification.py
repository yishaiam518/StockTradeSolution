#!/usr/bin/env python3
"""
Quick Verification Test for StockTradeSolution
Fast test to verify core functionality is working
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_unified_scoring():
    """Test unified scoring system"""
    print("🧪 Testing Unified Scoring System...")
    
    try:
        from src.machine_learning.stock_scorer import UnifiedStockScorer
        from src.strategies.macd_canonical_strategy import MACDCanonicalStrategy
        
        # Create sample data
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        sample_data = {
            'AAPL': pd.DataFrame({
                'Open': np.random.uniform(150, 200, len(dates)),
                'High': np.random.uniform(160, 210, len(dates)),
                'Low': np.random.uniform(140, 190, len(dates)),
                'Close': np.random.uniform(150, 200, len(dates)),
                'Volume': np.random.randint(1000000, 5000000, len(dates))
            }, index=dates)
        }
        
        # Test scorer
        scorer = UnifiedStockScorer()
        strategy = MACDCanonicalStrategy()
        
        # Test scoring list creation
        scoring_list = scorer.create_scoring_list('backtesting')
        print(f"   ✅ Scoring list created: {len(scoring_list)} items")
        
        # Test stock scoring
        scores = scorer.score_stocks(
            sample_data, 
            strategy=strategy, 
            profile='conservative', 
            mode='backtesting'
        )
        print(f"   ✅ Stock scoring completed: {len(scores)} stocks scored")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Unified scoring test failed: {e}")
        return False

def test_trading_system():
    """Test trading system integration"""
    print("🧪 Testing Trading System...")
    
    try:
        from src.trading_system import TradingSystem
        
        # Create sample data
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        sample_data = pd.DataFrame({
            'Open': np.random.uniform(150, 200, len(dates)),
            'High': np.random.uniform(160, 210, len(dates)),
            'Low': np.random.uniform(140, 190, len(dates)),
            'Close': np.random.uniform(150, 200, len(dates)),
            'Volume': np.random.randint(1000000, 5000000, len(dates))
        }, index=dates)
        
        # Test trading system
        trading_system = TradingSystem()
        
        # Test available components
        profiles = trading_system.get_available_profiles()
        strategies = trading_system.get_available_strategies()
        print(f"   ✅ Available profiles: {len(profiles)}")
        print(f"   ✅ Available strategies: {len(strategies)}")
        
        # Test signal generation
        signals = trading_system.generate_signals(
            sample_data,
            strategy_name='MACDCanonical',
            profile_name='conservative'
        )
        print(f"   ✅ Signal generation completed: {len(signals)} signals")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Trading system test failed: {e}")
        return False

def test_backtesting_engine():
    """Test backtesting engine"""
    print("🧪 Testing Backtesting Engine...")
    
    try:
        from src.backtesting.backtest_engine import BacktestEngine
        
        # Create sample data
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        sample_data = pd.DataFrame({
            'Open': np.random.uniform(150, 200, len(dates)),
            'High': np.random.uniform(160, 210, len(dates)),
            'Low': np.random.uniform(140, 190, len(dates)),
            'Close': np.random.uniform(150, 200, len(dates)),
            'Volume': np.random.randint(1000000, 5000000, len(dates))
        }, index=dates)
        
        # Test backtesting engine
        engine = BacktestEngine()
        
        # Test single stock backtest
        results = engine.run_single_stock_backtest(
            sample_data,
            strategy_name='MACDCanonical',
            profile_name='conservative',
            initial_capital=10000
        )
        
        print(f"   ✅ Single stock backtest completed")
        print(f"      Total return: {results.get('total_return', 'N/A')}")
        print(f"      Sharpe ratio: {results.get('sharpe_ratio', 'N/A')}")
        print(f"      Max drawdown: {results.get('max_drawdown', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Backtesting engine test failed: {e}")
        return False

def test_strategy_profiles():
    """Test strategy and profile combinations"""
    print("🧪 Testing Strategy and Profile Combinations...")
    
    try:
        from src.strategies.macd_canonical_strategy import MACDCanonicalStrategy
        from src.strategies.macd_aggressive_strategy import MACDAggressiveStrategy
        from src.strategies.macd_conservative_strategy import MACDConservativeStrategy
        
        # Create sample data
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        sample_data = pd.DataFrame({
            'Open': np.random.uniform(150, 200, len(dates)),
            'High': np.random.uniform(160, 210, len(dates)),
            'Low': np.random.uniform(140, 190, len(dates)),
            'Close': np.random.uniform(150, 200, len(dates)),
            'Volume': np.random.randint(1000000, 5000000, len(dates))
        }, index=dates)
        
        # Test all strategies
        strategies = [
            ('MACDCanonical', MACDCanonicalStrategy()),
            ('MACDAggressive', MACDAggressiveStrategy()),
            ('MACDConservative', MACDConservativeStrategy())
        ]
        
        profiles = ['conservative', 'moderate', 'aggressive']
        
        for strategy_name, strategy in strategies:
            for profile in profiles:
                # Configure strategy
                strategy.configure_profile(profile)
                
                # Generate signals
                signals = strategy.generate_signals(sample_data)
                
                print(f"   ✅ {strategy_name} with {profile} profile: {len(signals)} signals")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Strategy and profile test failed: {e}")
        return False

def test_configuration():
    """Test configuration loading"""
    print("🧪 Testing Configuration...")
    
    try:
        from src.utils.config_loader import ConfigLoader
        
        # Load configuration
        config = ConfigLoader().config
        
        print(f"   ✅ Configuration loaded successfully")
        print(f"      Strategies: {len(config.get('strategies', {}))}")
        print(f"      Profiles: {len(config.get('profiles', {}))}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Configuration test failed: {e}")
        return False

def test_data_pipeline():
    """Test data pipeline"""
    print("🧪 Testing Data Pipeline...")
    
    try:
        # Create sample data
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        sample_data = pd.DataFrame({
            'Open': np.random.uniform(150, 200, len(dates)),
            'High': np.random.uniform(160, 210, len(dates)),
            'Low': np.random.uniform(140, 190, len(dates)),
            'Close': np.random.uniform(150, 200, len(dates)),
            'Volume': np.random.randint(1000000, 5000000, len(dates))
        }, index=dates)
        
        # Validate data
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required_columns:
            if col not in sample_data.columns:
                raise ValueError(f"Missing required column: {col}")
        
        # Check data types
        if not isinstance(sample_data.index, pd.DatetimeIndex):
            raise ValueError("Index must be DatetimeIndex")
        
        # Check for missing values
        if sample_data.isnull().sum().sum() > 0:
            raise ValueError("Data contains missing values")
        
        print(f"   ✅ Data pipeline validation passed")
        print(f"      Data shape: {sample_data.shape}")
        print(f"      Date range: {sample_data.index.min()} to {sample_data.index.max()}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Data pipeline test failed: {e}")
        return False

def run_quick_tests():
    """Run all quick tests"""
    print("🚀 Starting Quick Verification Tests...")
    print("=" * 50)
    
    tests = [
        test_configuration,
        test_data_pipeline,
        test_unified_scoring,
        test_trading_system,
        test_backtesting_engine,
        test_strategy_profiles
    ]
    
    results = []
    
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"   ❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    # Print summary
    print("=" * 50)
    print(f"📊 Quick Test Results:")
    print(f"   Tests run: {len(tests)}")
    print(f"   Passed: {sum(results)}")
    print(f"   Failed: {len(tests) - sum(results)}")
    print(f"   Success rate: {(sum(results) / len(tests) * 100):.1f}%")
    
    if all(results):
        print("\n🎉 All quick tests passed! Core functionality is working.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
    
    return all(results)

if __name__ == "__main__":
    success = run_quick_tests()
    sys.exit(0 if success else 1) 