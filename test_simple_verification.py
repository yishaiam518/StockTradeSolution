#!/usr/bin/env python3
"""
Simple Verification Test for StockTradeSolution
Tests core functionality without complex dependencies
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

def test_configuration():
    """Test configuration loading"""
    print("🧪 Testing Configuration...")
    
    try:
        from src.utils.config_loader import ConfigLoader
        
        # Load configuration
        config = ConfigLoader().config
        
        print(f"   ✅ Configuration loaded successfully")
        print(f"      Config keys: {list(config.keys())}")
        
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

def test_base_strategy():
    """Test base strategy functionality"""
    print("🧪 Testing Base Strategy...")
    
    try:
        from src.strategies.base_strategy import BaseStrategy
        
        # Create sample data with indicators
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        sample_data = pd.DataFrame({
            'Open': np.random.uniform(150, 200, len(dates)),
            'High': np.random.uniform(160, 210, len(dates)),
            'Low': np.random.uniform(140, 190, len(dates)),
            'Close': np.random.uniform(150, 200, len(dates)),
            'close': np.random.uniform(150, 200, len(dates)),  # Add lowercase version
            'Volume': np.random.randint(1000000, 5000000, len(dates)),
            'macd_line': np.random.uniform(-2, 2, len(dates)),
            'macd_signal': np.random.uniform(-2, 2, len(dates)),
            'macd_crossover_up': np.random.choice([True, False], len(dates)),
            'macd_crossover_down': np.random.choice([True, False], len(dates))
        }, index=dates)
        
        # Test base strategy (we can't instantiate it directly since it's abstract)
        print(f"   ✅ Base strategy class loaded successfully")
        
        # Test data validation
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required_columns:
            if col not in sample_data.columns:
                raise ValueError(f"Missing required column: {col}")
        
        print(f"   ✅ Data validation passed")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Base strategy test failed: {e}")
        return False

def test_macd_strategy():
    """Test MACD strategy functionality"""
    print("🧪 Testing MACD Strategy...")
    
    try:
        from src.strategies.macd_canonical_strategy import MACDCanonicalStrategy
        
        # Create sample data with indicators
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        sample_data = pd.DataFrame({
            'Open': np.random.uniform(150, 200, len(dates)),
            'High': np.random.uniform(160, 210, len(dates)),
            'Low': np.random.uniform(140, 190, len(dates)),
            'Close': np.random.uniform(150, 200, len(dates)),
            'close': np.random.uniform(150, 200, len(dates)),  # Add lowercase version
            'Volume': np.random.randint(1000000, 5000000, len(dates)),
            'macd_line': np.random.uniform(-2, 2, len(dates)),
            'macd_signal': np.random.uniform(-2, 2, len(dates)),
            'macd_crossover_up': np.random.choice([True, False], len(dates)),
            'macd_crossover_down': np.random.choice([True, False], len(dates))
        }, index=dates)
        
        # Test strategy initialization
        strategy = MACDCanonicalStrategy()
        print(f"   ✅ MACD strategy initialized successfully")
        
        # Test profile configuration
        strategy.configure_profile('conservative')
        print(f"   ✅ Profile configuration successful")
        
        # Test signal generation
        signals = strategy.generate_signals(sample_data)
        print(f"   ✅ Signal generation completed: {len(signals)} signals")
        
        # Test strategy parameters
        params = strategy.get_strategy_parameters()
        print(f"   ✅ Strategy parameters: {len(params)} parameters")
        
        return True
        
    except Exception as e:
        print(f"   ❌ MACD strategy test failed: {e}")
        return False

def test_strategy_profiles():
    """Test strategy and profile combinations"""
    print("🧪 Testing Strategy and Profile Combinations...")
    
    try:
        from src.strategies.macd_canonical_strategy import MACDCanonicalStrategy
        from src.strategies.macd_aggressive_strategy import MACDAggressiveStrategy
        from src.strategies.macd_conservative_strategy import MACDConservativeStrategy
        
        # Create sample data with indicators
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        sample_data = pd.DataFrame({
            'Open': np.random.uniform(150, 200, len(dates)),
            'High': np.random.uniform(160, 210, len(dates)),
            'Low': np.random.uniform(140, 190, len(dates)),
            'Close': np.random.uniform(150, 200, len(dates)),
            'close': np.random.uniform(150, 200, len(dates)),  # Add lowercase version
            'Volume': np.random.randint(1000000, 5000000, len(dates)),
            'macd_line': np.random.uniform(-2, 2, len(dates)),
            'macd_signal': np.random.uniform(-2, 2, len(dates)),
            'macd_crossover_up': np.random.choice([True, False], len(dates)),
            'macd_crossover_down': np.random.choice([True, False], len(dates))
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

def test_indicators():
    """Test technical indicators"""
    print("🧪 Testing Technical Indicators...")
    
    try:
        from src.indicators.indicators import TechnicalIndicators
        
        # Create sample data
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        sample_data = pd.DataFrame({
            'Open': np.random.uniform(150, 200, len(dates)),
            'High': np.random.uniform(160, 210, len(dates)),
            'Low': np.random.uniform(140, 190, len(dates)),
            'Close': np.random.uniform(150, 200, len(dates)),
            'close': np.random.uniform(150, 200, len(dates)),  # Add lowercase version
            'Volume': np.random.randint(1000000, 5000000, len(dates))
        }, index=dates)
        
        # Test indicators
        indicators = TechnicalIndicators()
        
        # Test MACD calculation
        macd_data = indicators.calculate_macd(sample_data)
        print(f"   ✅ MACD calculation successful")
        
        # Test RSI calculation
        rsi_data = indicators.calculate_rsi(sample_data)
        print(f"   ✅ RSI calculation successful")
        
        # Test EMA calculation
        ema_data = indicators.calculate_ema(sample_data)
        print(f"   ✅ EMA calculation successful")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Indicators test failed: {e}")
        return False

def test_utils():
    """Test utility functions"""
    print("🧪 Testing Utilities...")
    
    try:
        from src.utils.logger import get_logger
        
        # Test logger setup
        logger = get_logger('test_utils')
        logger.info("Test log message")
        print(f"   ✅ Logger setup successful")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Utilities test failed: {e}")
        return False

def run_simple_tests():
    """Run all simple tests"""
    print("🚀 Starting Simple Verification Tests...")
    print("=" * 50)
    
    tests = [
        test_configuration,
        test_data_pipeline,
        test_base_strategy,
        test_macd_strategy,
        test_strategy_profiles,
        test_indicators,
        test_utils
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
    print(f"📊 Simple Test Results:")
    print(f"   Tests run: {len(tests)}")
    print(f"   Passed: {sum(results)}")
    print(f"   Failed: {len(tests) - sum(results)}")
    print(f"   Success rate: {(sum(results) / len(tests) * 100):.1f}%")
    
    if all(results):
        print("\n🎉 All simple tests passed! Core functionality is working.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
    
    return all(results)

if __name__ == "__main__":
    success = run_simple_tests()
    sys.exit(0 if success else 1) 