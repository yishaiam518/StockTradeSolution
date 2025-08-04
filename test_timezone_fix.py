#!/usr/bin/env python3
"""
Test script to verify unified timezone system is working correctly.
"""

import sys
import os
from datetime import datetime, timedelta

# Add src to path
sys.path.append('src')

from src.utils.timezone_utils import (
    make_timezone_naive, normalize_dataframe_dates, 
    normalize_index_dates, safe_date_comparison,
    safe_date_range_filter, parse_date_string
)
from src.backtesting.backtest_engine import BacktestEngine
from src.utils.logger import get_logger

def test_timezone_system():
    """Test the unified timezone system."""
    logger = get_logger('timezone_test')
    logger.info("🧪 Testing unified timezone system...")
    
    try:
        # Test 1: Parse date string
        test_date = "2023-01-01"
        parsed_date = parse_date_string(test_date)
        logger.info(f"✅ Parsed date '{test_date}' -> {parsed_date}")
        
        # Test 2: Make timezone naive
        import pandas as pd
        from datetime import timezone
        
        # Create timezone-aware datetime
        aware_dt = datetime.now(timezone.utc)
        naive_dt = make_timezone_naive(aware_dt)
        logger.info(f"✅ Timezone-aware: {aware_dt} -> Naive: {naive_dt}")
        
        # Test 3: Normalize dataframe dates
        dates = pd.date_range('2023-01-01', periods=5, freq='D', tz='UTC')
        df = pd.DataFrame({'close': [100, 101, 102, 103, 104]}, index=dates)
        normalized_df = normalize_index_dates(df)
        logger.info(f"✅ Normalized dataframe dates: {normalized_df.index[0]} (tz: {normalized_df.index[0].tz})")
        
        # Test 4: Safe date comparison
        date1 = datetime(2023, 1, 1, tzinfo=timezone.utc)
        date2 = datetime(2023, 1, 1)  # Naive
        comparison = safe_date_comparison(date1, date2)
        logger.info(f"✅ Safe date comparison: {date1} == {date2} -> {comparison}")
        
        # Test 5: Backtest engine with unified timezone
        logger.info("🔄 Testing backtest engine with unified timezone...")
        backtest_engine = BacktestEngine()
        
        # Run a simple historical backtest
        results = backtest_engine.run_historical_backtest(
            strategy="macd_canonical",
            profile="aggressive",
            start_date="2023-01-01",
            end_date="2023-01-31"
        )
        
        if 'error' not in results:
            logger.info(f"✅ Backtest completed successfully!")
            logger.info(f"   Total trades: {len(results.get('trades', []))}")
            logger.info(f"   Final portfolio value: ${results.get('final_portfolio_value', 0):.2f}")
        else:
            logger.error(f"❌ Backtest failed: {results.get('error')}")
        
        logger.info("🎉 Timezone system test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Timezone system test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_timezone_system()
    sys.exit(0 if success else 1) 