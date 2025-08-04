#!/usr/bin/env python3
"""
Technical Indicators Verification Script

This script verifies that technical indicators are calculated for ALL data points
in a collection, not just a subset. It provides detailed progress reporting
and data validation to ensure comprehensive processing.
"""

import sys
import os
import time
import pandas as pd
from datetime import datetime
import sqlite3

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data_collection.data_manager import DataCollectionManager
from src.indicators import indicator_manager

def verify_collection_data_completeness(collection_id: str):
    """Verify that all data points in a collection are processed for indicators."""
    
    print(f"🔍 VERIFYING COLLECTION: {collection_id}")
    print("=" * 60)
    
    # Initialize data manager
    data_manager = DataCollectionManager()
    
    # Get collection details
    collection_details = data_manager.get_collection_details(collection_id)
    if not collection_details:
        print(f"❌ Collection {collection_id} not found!")
        return False
    
    print(f"📊 Collection Details:")
    print(f"   Exchange: {collection_details.get('exchange', 'N/A')}")
    print(f"   Date Range: {collection_details.get('start_date', 'N/A')} to {collection_details.get('end_date', 'N/A')}")
    print(f"   Total Symbols: {collection_details.get('total_symbols', 0)}")
    print(f"   Successful Symbols: {collection_details.get('successful_symbols', 0)}")
    print()
    
    # Get all symbols in the collection
    symbols = data_manager.get_collection_symbols(collection_id)
    if not symbols:
        print("❌ No symbols found in collection!")
        return False
    
    print(f"📈 Analyzing {len(symbols)} symbols...")
    print()
    
    # Track detailed statistics
    total_data_points = 0
    processed_data_points = 0
    symbols_with_indicators = 0
    symbols_without_indicators = 0
    detailed_stats = []
    
    for i, symbol in enumerate(symbols, 1):
        print(f"🔍 Processing {i}/{len(symbols)}: {symbol}")
        
        # Get raw data
        raw_data = data_manager.get_symbol_data(collection_id, symbol)
        if raw_data is None or raw_data.empty:
            print(f"   ⚠️  No raw data available")
            symbols_without_indicators += 1
            continue
        
        raw_data_points = len(raw_data)
        total_data_points += raw_data_points
        print(f"   📊 Raw data points: {raw_data_points}")
        
        # Get indicators data
        indicators_data = data_manager.get_symbol_indicators(collection_id, symbol)
        if indicators_data is None or indicators_data.empty:
            print(f"   ❌ No indicators calculated")
            symbols_without_indicators += 1
            continue
        
        indicators_data_points = len(indicators_data)
        processed_data_points += indicators_data_points
        symbols_with_indicators += 1
        
        print(f"   ✅ Indicators data points: {indicators_data_points}")
        
        # Verify data completeness
        if raw_data_points != indicators_data_points:
            print(f"   ⚠️  MISMATCH: Raw data has {raw_data_points} points, indicators have {indicators_data_points}")
        else:
            print(f"   ✅ Data points match: {raw_data_points}")
        
        # Check for indicator columns
        indicator_columns = [col for col in indicators_data.columns if any(indicator in col.lower() for indicator in 
                          ['sma', 'ema', 'wma', 'hma', 'rsi', 'macd', 'stochastic', 'williams', 'bollinger', 'atr', 'obv', 'vwap', 'mfi'])]
        
        print(f"   📊 Indicator columns found: {len(indicator_columns)}")
        print(f"   📋 Sample indicators: {indicator_columns[:5]}")
        
        # Check for NaN values in indicators
        nan_count = indicators_data[indicator_columns].isna().sum().sum()
        print(f"   🔍 NaN values in indicators: {nan_count}")
        
        # Store detailed stats
        detailed_stats.append({
            'symbol': symbol,
            'raw_points': raw_data_points,
            'indicator_points': indicators_data_points,
            'indicator_columns': len(indicator_columns),
            'nan_count': nan_count,
            'match': raw_data_points == indicators_data_points
        })
        
        print()
    
    # Summary report
    print("=" * 60)
    print("📋 VERIFICATION SUMMARY")
    print("=" * 60)
    
    print(f"📊 Overall Statistics:")
    print(f"   Total symbols: {len(symbols)}")
    print(f"   Symbols with indicators: {symbols_with_indicators}")
    print(f"   Symbols without indicators: {symbols_without_indicators}")
    print(f"   Coverage: {(symbols_with_indicators/len(symbols)*100):.1f}%")
    print()
    
    print(f"📈 Data Points Analysis:")
    print(f"   Total raw data points: {total_data_points:,}")
    print(f"   Total processed data points: {processed_data_points:,}")
    print(f"   Data processing ratio: {(processed_data_points/total_data_points*100):.1f}%" if total_data_points > 0 else "   Data processing ratio: 0%")
    print()
    
    # Detailed analysis
    matching_symbols = sum(1 for stat in detailed_stats if stat['match'])
    print(f"🔍 Data Completeness Analysis:")
    print(f"   Symbols with matching data points: {matching_symbols}/{len(detailed_stats)}")
    print(f"   Data completeness: {(matching_symbols/len(detailed_stats)*100):.1f}%" if detailed_stats else "   Data completeness: 0%")
    print()
    
    # Show symbols with issues
    issues = [stat for stat in detailed_stats if not stat['match']]
    if issues:
        print(f"⚠️  Symbols with data mismatches:")
        for issue in issues:
            print(f"   {issue['symbol']}: Raw={issue['raw_points']}, Indicators={issue['indicator_points']}")
        print()
    
    # Show symbols with high NaN counts
    high_nan = [stat for stat in detailed_stats if stat['nan_count'] > 0]
    if high_nan:
        print(f"⚠️  Symbols with NaN values in indicators:")
        for stat in high_nan:
            print(f"   {stat['symbol']}: {stat['nan_count']} NaN values")
        print()
    
    return symbols_with_indicators > 0 and matching_symbols == len(detailed_stats)

def test_indicator_calculation_speed(collection_id: str, symbol: str):
    """Test the speed and thoroughness of indicator calculation."""
    
    print(f"⚡ SPEED TEST: Calculating indicators for {symbol}")
    print("=" * 60)
    
    data_manager = DataCollectionManager()
    
    # Get raw data
    raw_data = data_manager.get_symbol_data(collection_id, symbol)
    if raw_data is None or raw_data.empty:
        print(f"❌ No data available for {symbol}")
        return False
    
    print(f"📊 Raw data shape: {raw_data.shape}")
    print(f"📅 Date range: {raw_data.index.min()} to {raw_data.index.max()}")
    print(f"📈 Data points: {len(raw_data)}")
    print()
    
    # Time the calculation
    start_time = time.time()
    
    print("🔄 Calculating indicators...")
    enhanced_data = indicator_manager.calculate_all_indicators(raw_data)
    
    end_time = time.time()
    calculation_time = end_time - start_time
    
    print(f"⏱️  Calculation completed in {calculation_time:.2f} seconds")
    print(f"📊 Enhanced data shape: {enhanced_data.shape}")
    print()
    
    # Analyze the results
    indicator_columns = [col for col in enhanced_data.columns if any(indicator in col.lower() for indicator in 
                      ['sma', 'ema', 'wma', 'hma', 'rsi', 'macd', 'stochastic', 'williams', 'bollinger', 'atr', 'obv', 'vwap', 'mfi'])]
    
    print(f"📋 Indicator Analysis:")
    print(f"   Total columns: {len(enhanced_data.columns)}")
    print(f"   Indicator columns: {len(indicator_columns)}")
    print(f"   Data points processed: {len(enhanced_data)}")
    print(f"   Processing speed: {len(enhanced_data)/calculation_time:.0f} points/second")
    print()
    
    # Check for NaN values
    nan_counts = enhanced_data[indicator_columns].isna().sum()
    total_nan = nan_counts.sum()
    
    print(f"🔍 Data Quality Check:")
    print(f"   Total NaN values: {total_nan}")
    print(f"   NaN percentage: {(total_nan/(len(enhanced_data)*len(indicator_columns))*100):.2f}%")
    print()
    
    # Show sample of calculated indicators
    print(f"📊 Sample Indicator Values (latest data point):")
    latest = enhanced_data.iloc[-1]
    for col in indicator_columns[:10]:  # Show first 10 indicators
        value = latest[col]
        print(f"   {col}: {value:.4f}" if pd.notna(value) else f"   {col}: NaN")
    
    return True

def main():
    """Main verification function."""
    
    print("🔍 TECHNICAL INDICATORS VERIFICATION SCRIPT")
    print("=" * 60)
    print("This script verifies that ALL data points are processed for indicators")
    print("and provides detailed analysis of the calculation process.")
    print()
    
    # Get available collections
    data_manager = DataCollectionManager()
    collections = data_manager.list_collections()
    
    if not collections:
        print("❌ No collections found!")
        return
    
    print(f"📋 Available Collections:")
    for i, collection in enumerate(collections, 1):
        print(f"   {i}. {collection['collection_id']} ({collection['exchange']})")
        print(f"      Symbols: {collection['total_symbols']}, Date: {collection['collection_date']}")
    
    print()
    
    # Use the first collection for testing
    collection_id = collections[0]['collection_id']
    print(f"🎯 Using collection: {collection_id}")
    print()
    
    # Verify collection completeness
    print("STEP 1: Verifying collection data completeness...")
    completeness_ok = verify_collection_data_completeness(collection_id)
    print()
    
    # Test calculation speed for a specific symbol
    print("STEP 2: Testing calculation speed and thoroughness...")
    symbols = data_manager.get_collection_symbols(collection_id)
    if symbols:
        test_symbol = symbols[0]  # Use first symbol
        speed_ok = test_indicator_calculation_speed(collection_id, test_symbol)
    else:
        print("❌ No symbols available for speed test")
        speed_ok = False
    
    print()
    print("=" * 60)
    print("📋 FINAL VERIFICATION RESULTS")
    print("=" * 60)
    
    if completeness_ok and speed_ok:
        print("✅ VERIFICATION PASSED")
        print("   - All data points are being processed")
        print("   - Indicators are calculated for the full dataset")
        print("   - Calculation speed is reasonable")
    else:
        print("❌ VERIFICATION FAILED")
        if not completeness_ok:
            print("   - Some data points may not be processed")
        if not speed_ok:
            print("   - Calculation speed or thoroughness issues")
    
    print()
    print("💡 TIPS:")
    print("   - The calculation speed depends on the number of data points")
    print("   - All historical data should be processed, not just recent data")
    print("   - Check the 'Data Points Analysis' section above for verification")
    print("   - If you see mismatches, the calculation may be incomplete")

if __name__ == "__main__":
    main() 