#!/usr/bin/env python3
"""
Test script to verify indicator storage.
"""

from src.data_collection.data_manager import DataCollectionManager
from src.indicators import indicator_manager

def test_indicator_storage():
    """Test that enhanced data with indicators is stored correctly."""
    
    print("🧪 TESTING INDICATOR STORAGE")
    print("=" * 50)
    
    dm = DataCollectionManager()
    collection_id = 'AMEX_20250803_161652'
    symbol = 'BND'
    
    # Get original data
    print(f"📊 Getting original data for {symbol}...")
    original_data = dm.get_symbol_data(collection_id, symbol)
    print(f"Original data shape: {original_data.shape}")
    print(f"Original columns: {original_data.columns.tolist()}")
    
    # Calculate indicators
    print(f"\n🔧 Calculating indicators for {symbol}...")
    enhanced_data = indicator_manager.calculate_all_indicators(original_data)
    print(f"Enhanced data shape: {enhanced_data.shape}")
    print(f"Enhanced columns: {enhanced_data.columns.tolist()}")
    
    # Check for indicator columns
    indicator_cols = [col for col in enhanced_data.columns if any(indicator in col.upper() for indicator in ['SMA', 'EMA', 'RSI', 'MACD', 'BOLLINGER', 'ATR', 'STOCHASTIC'])]
    print(f"Indicator columns found: {len(indicator_cols)}")
    print(f"First 10 indicator columns: {indicator_cols[:10]}")
    
    # Store the enhanced data
    print(f"\n💾 Storing enhanced data for {symbol}...")
    success = dm.store_symbol_indicators(collection_id, symbol, enhanced_data)
    print(f"Storage success: {success}")
    
    # Retrieve the stored data
    print(f"\n📥 Retrieving stored data for {symbol}...")
    retrieved_data = dm.get_symbol_indicators(collection_id, symbol)
    if retrieved_data is not None:
        print(f"Retrieved data shape: {retrieved_data.shape}")
        print(f"Retrieved columns: {retrieved_data.columns.tolist()}")
        
        # Check for indicator columns in retrieved data
        retrieved_indicator_cols = [col for col in retrieved_data.columns if any(indicator in col.upper() for indicator in ['SMA', 'EMA', 'RSI', 'MACD', 'BOLLINGER', 'ATR', 'STOCHASTIC'])]
        print(f"Retrieved indicator columns: {len(retrieved_indicator_cols)}")
        print(f"First 10 retrieved indicator columns: {retrieved_indicator_cols[:10]}")
        
        # Compare with enhanced data
        if len(indicator_cols) == len(retrieved_indicator_cols):
            print("✅ Indicator columns match!")
        else:
            print(f"❌ Indicator columns don't match! Expected: {len(indicator_cols)}, Got: {len(retrieved_indicator_cols)}")
    else:
        print("❌ No data retrieved!")

if __name__ == "__main__":
    test_indicator_storage() 