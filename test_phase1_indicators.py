#!/usr/bin/env python3
"""
Test script for Phase 1 Technical Indicators implementation.
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.indicators import (
    indicator_manager,
    SMAIndicator,
    EMAIndicator,
    RSIIndicator,
    MACDIndicator,
    BollingerBandsIndicator,
    OBVIndicator
)
from src.utils.logger import logger


def create_sample_data():
    """Create sample OHLCV data for testing."""
    # Generate sample data
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    np.random.seed(42)  # For reproducible results
    
    # Create realistic price data with trend and volatility
    base_price = 100
    trend = np.linspace(0, 20, len(dates))  # Upward trend
    noise = np.random.normal(0, 2, len(dates))
    prices = base_price + trend + noise
    
    # Create OHLCV data
    data = pd.DataFrame({
        'date': dates,
        'open': prices + np.random.normal(0, 0.5, len(dates)),
        'high': prices + np.random.uniform(0, 2, len(dates)),
        'low': prices - np.random.uniform(0, 2, len(dates)),
        'close': prices,
        'volume': np.random.uniform(1000000, 5000000, len(dates))
    })
    
    # Ensure high >= close >= low
    data['high'] = data[['open', 'close', 'high']].max(axis=1)
    data['low'] = data[['open', 'close', 'low']].min(axis=1)
    
    data.set_index('date', inplace=True)
    return data


def test_individual_indicators():
    """Test individual indicators."""
    logger.info("Testing individual indicators...")
    
    data = create_sample_data()
    logger.info(f"Created sample data with {len(data)} rows")
    
    # Test SMA
    logger.info("Testing SMA indicator...")
    sma_indicator = SMAIndicator(period=20)
    data_with_sma = sma_indicator.calculate(data.copy())
    sma_signals = sma_indicator.get_signals(data_with_sma)
    logger.info(f"SMA signals: {sma_signals}")
    
    # Test EMA
    logger.info("Testing EMA indicator...")
    ema_indicator = EMAIndicator(period=20)
    data_with_ema = ema_indicator.calculate(data.copy())
    ema_signals = ema_indicator.get_signals(data_with_ema)
    logger.info(f"EMA signals: {ema_signals}")
    
    # Test RSI
    logger.info("Testing RSI indicator...")
    rsi_indicator = RSIIndicator(period=14)
    data_with_rsi = rsi_indicator.calculate(data.copy())
    rsi_signals = rsi_indicator.get_signals(data_with_rsi)
    logger.info(f"RSI signals: {rsi_signals}")
    
    # Test MACD
    logger.info("Testing MACD indicator...")
    macd_indicator = MACDIndicator(fast_period=12, slow_period=26, signal_period=9)
    data_with_macd = macd_indicator.calculate(data.copy())
    macd_signals = macd_indicator.get_signals(data_with_macd)
    logger.info(f"MACD signals: {macd_signals}")
    
    # Test Bollinger Bands
    logger.info("Testing Bollinger Bands indicator...")
    bb_indicator = BollingerBandsIndicator(period=20, std_dev=2.0)
    data_with_bb = bb_indicator.calculate(data.copy())
    bb_signals = bb_indicator.get_signals(data_with_bb)
    logger.info(f"Bollinger Bands signals: {bb_signals}")
    
    # Test OBV
    logger.info("Testing OBV indicator...")
    obv_indicator = OBVIndicator()
    data_with_obv = obv_indicator.calculate(data.copy())
    obv_signals = obv_indicator.get_signals(data_with_obv)
    logger.info(f"OBV signals: {obv_signals}")
    
    return True


def test_indicator_manager():
    """Test the indicator manager."""
    logger.info("Testing indicator manager...")
    
    data = create_sample_data()
    
    # Test calculating all indicators
    logger.info("Calculating all indicators...")
    data_with_all_indicators = indicator_manager.calculate_all_indicators(data)
    
    # Check that indicators were added
    indicator_columns = [col for col in data_with_all_indicators.columns 
                        if any(indicator in col for indicator in ['sma', 'ema', 'rsi', 'macd', 'bb', 'obv', 'vwap'])]
    logger.info(f"Added {len(indicator_columns)} indicator columns")
    logger.info(f"Indicator columns: {indicator_columns[:10]}...")  # Show first 10
    
    # Test getting all signals
    logger.info("Getting all signals...")
    all_signals = indicator_manager.get_all_signals(data_with_all_indicators)
    
    for indicator_name, signals in all_signals.items():
        logger.info(f"{indicator_name}: {signals.get('signal', 'no_signal')} (strength: {signals.get('strength', 0)})")
    
    return True


def test_indicator_parameters():
    """Test indicator parameter handling."""
    logger.info("Testing indicator parameters...")
    
    # Test SMA with different periods
    sma_10 = SMAIndicator(period=10)
    sma_20 = SMAIndicator(period=20)
    sma_50 = SMAIndicator(period=50)
    
    logger.info(f"SMA 10 parameters: {sma_10.get_parameters()}")
    logger.info(f"SMA 20 parameters: {sma_20.get_parameters()}")
    logger.info(f"SMA 50 parameters: {sma_50.get_parameters()}")
    
    # Test MACD with different parameters
    macd_standard = MACDIndicator(fast_period=12, slow_period=26, signal_period=9)
    macd_fast = MACDIndicator(fast_period=8, slow_period=21, signal_period=5)
    
    logger.info(f"MACD standard parameters: {macd_standard.get_parameters()}")
    logger.info(f"MACD fast parameters: {macd_fast.get_parameters()}")
    
    return True


def test_data_validation():
    """Test data validation."""
    logger.info("Testing data validation...")
    
    # Test with invalid data
    invalid_data = pd.DataFrame({
        'open': [100, 101, 102],
        'high': [105, 106, 107],
        'low': [95, 96, 97]
        # Missing 'close' and 'volume'
    })
    
    sma_indicator = SMAIndicator(period=20)
    result = sma_indicator.calculate(invalid_data)
    
    # Should return original data without modification
    assert len(result.columns) == len(invalid_data.columns), "Invalid data should not be modified"
    logger.info("Data validation test passed")
    
    return True


def test_performance():
    """Test indicator calculation performance."""
    logger.info("Testing performance...")
    
    # Create larger dataset
    dates = pd.date_range(start='2020-01-01', end='2023-12-31', freq='D')
    np.random.seed(42)
    
    base_price = 100
    trend = np.linspace(0, 50, len(dates))
    noise = np.random.normal(0, 3, len(dates))
    prices = base_price + trend + noise
    
    large_data = pd.DataFrame({
        'date': dates,
        'open': prices + np.random.normal(0, 0.5, len(dates)),
        'high': prices + np.random.uniform(0, 3, len(dates)),
        'low': prices - np.random.uniform(0, 3, len(dates)),
        'close': prices,
        'volume': np.random.uniform(1000000, 5000000, len(dates))
    })
    
    large_data['high'] = large_data[['open', 'close', 'high']].max(axis=1)
    large_data['low'] = large_data[['open', 'close', 'low']].min(axis=1)
    large_data.set_index('date', inplace=True)
    
    logger.info(f"Testing with {len(large_data)} data points...")
    
    import time
    start_time = time.time()
    
    # Calculate all indicators
    result_data = indicator_manager.calculate_all_indicators(large_data)
    
    end_time = time.time()
    calculation_time = end_time - start_time
    
    logger.info(f"Calculated all indicators in {calculation_time:.2f} seconds")
    logger.info(f"Result data has {len(result_data.columns)} columns")
    
    return True


def main():
    """Run all tests."""
    logger.info("Starting Phase 1 Technical Indicators tests...")
    
    try:
        # Test individual indicators
        test_individual_indicators()
        logger.info("✅ Individual indicators test passed")
        
        # Test indicator manager
        test_indicator_manager()
        logger.info("✅ Indicator manager test passed")
        
        # Test parameter handling
        test_indicator_parameters()
        logger.info("✅ Parameter handling test passed")
        
        # Test data validation
        test_data_validation()
        logger.info("✅ Data validation test passed")
        
        # Test performance
        test_performance()
        logger.info("✅ Performance test passed")
        
        logger.info("🎉 All Phase 1 tests passed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 