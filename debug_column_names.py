#!/usr/bin/env python3
"""
Debug script to check column names in the data.
"""

import sys
import os
import pandas as pd

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data_collection.data_manager import DataCollectionManager

def check_column_names():
    """Check the actual column names in the data."""
    
    print("🔍 CHECKING COLUMN NAMES IN DATA")
    print("=" * 50)
    
    # Initialize data manager
    data_manager = DataCollectionManager()
    
    # Get available collections
    collections = data_manager.list_collections()
    if not collections:
        print("❌ No collections found!")
        return
    
    # Use the first collection
    collection_id = collections[0]['collection_id']
    print(f"📋 Using collection: {collection_id}")
    print()
    
    # Get symbols
    symbols = data_manager.get_collection_symbols(collection_id)
    if not symbols:
        print("❌ No symbols found!")
        return
    
    # Check first few symbols
    for i, symbol in enumerate(symbols[:5], 1):
        print(f"🔍 Symbol {i}: {symbol}")
        
        # Get raw data
        raw_data = data_manager.get_symbol_data(collection_id, symbol)
        if raw_data is None or raw_data.empty:
            print(f"   ❌ No data available")
            continue
        
        print(f"   📊 Raw data shape: {raw_data.shape}")
        print(f"   📋 Raw data columns: {list(raw_data.columns)}")
        print(f"   📅 Raw data index type: {type(raw_data.index)}")
        print(f"   📈 Sample data:")
        print(f"      {raw_data.head(3)}")
        print()
        
        # Get indicators data
        indicators_data = data_manager.get_symbol_indicators(collection_id, symbol)
        if indicators_data is None or indicators_data.empty:
            print(f"   ❌ No indicators data available")
            continue
        
        print(f"   📊 Indicators data shape: {indicators_data.shape}")
        print(f"   📋 Indicators data columns: {list(indicators_data.columns)}")
        print(f"   📅 Indicators data index type: {type(indicators_data.index)}")
        print(f"   📈 Sample indicators data:")
        print(f"      {indicators_data.head(3)}")
        print()
        
        # Check for OHLCV columns
        ohlcv_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in ohlcv_columns if col not in raw_data.columns]
        
        if missing_columns:
            print(f"   ⚠️  Missing OHLCV columns: {missing_columns}")
        else:
            print(f"   ✅ All OHLCV columns present")
        
        print("-" * 50)
        print()

if __name__ == "__main__":
    check_column_names() 