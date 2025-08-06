#!/usr/bin/env python3
"""
Debug script to test data collection and identify issues
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.data_collection.data_manager import DataCollectionManager, DataCollectionConfig, Exchange
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

def test_data_collection():
    """Test data collection to identify issues"""
    
    # Initialize data manager
    data_manager = DataCollectionManager()
    
    # Test 1: Check symbol retrieval
    print("=== Testing Symbol Retrieval ===")
    
    # Test ALL exchange
    config_all = DataCollectionConfig(
        exchange=Exchange.ALL,
        start_date="2024-01-01",
        end_date="2024-12-31"
    )
    
    symbols_all = data_manager._get_symbols_for_exchange(config_all)
    print(f"ALL exchange symbols: {len(symbols_all)} symbols")
    print(f"First 10 symbols: {symbols_all[:10]}")
    
    # Test AMEX exchange
    config_amex = DataCollectionConfig(
        exchange=Exchange.AMEX,
        start_date="2024-01-01",
        end_date="2024-12-31"
    )
    
    symbols_amex = data_manager._get_symbols_for_exchange(config_amex)
    print(f"AMEX exchange symbols: {len(symbols_amex)} symbols")
    print(f"First 10 symbols: {symbols_amex[:10]}")
    
    # Test 2: Check data fetching for a few symbols
    print("\n=== Testing Data Fetching ===")
    
    test_symbols = ['AAPL', 'SPY', 'BND', 'INVALID_SYMBOL']
    
    for symbol in test_symbols:
        print(f"\nTesting symbol: {symbol}")
        data = data_manager._fetch_symbol_data(symbol, "2024-01-01", "2024-12-31")
        if data is not None:
            print(f"✅ Success: {len(data)} data points")
            print(f"Columns: {list(data.columns)}")
            print(f"Date range: {data['Date'].min()} to {data['Date'].max()}")
        else:
            print(f"❌ Failed: No data returned")
    
    # Test 3: Check existing collections
    print("\n=== Checking Existing Collections ===")
    
    collections = data_manager.list_collections()
    print(f"Found {len(collections)} collections")
    
    for collection in collections:
        print(f"\nCollection: {collection['collection_id']}")
        print(f"  Exchange: {collection['exchange']}")
        print(f"  Total symbols: {collection['total_symbols']}")
        print(f"  Successful symbols: {collection['successful_symbols']}")
        print(f"  Failed count: {collection['failed_count']}")
        
        # Get actual symbols for this collection
        symbols = data_manager.get_collection_symbols(collection['collection_id'])
        print(f"  Actual symbols in DB: {len(symbols)}")
        if symbols:
            print(f"  Sample symbols: {symbols[:5]}")

if __name__ == "__main__":
    test_data_collection() 