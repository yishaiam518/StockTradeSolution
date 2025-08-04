#!/usr/bin/env python3
"""
Debug script to test the API endpoint directly.
"""

from src.web_dashboard.dashboard_app import DashboardApp
from src.data_collection.data_manager import DataCollectionManager

def debug_api_endpoint():
    """Debug the data-with-indicators API endpoint."""
    
    print("🔍 DEBUGGING API ENDPOINT")
    print("=" * 50)
    
    # Initialize the dashboard app
    app = DashboardApp()
    
    collection_id = 'AMEX_20250803_161652'
    symbol = 'BND'
    
    # Test the data manager methods directly
    print(f"📊 Testing data manager methods for {symbol}...")
    
    # Get original data
    original_data = app.data_collection_manager.get_symbol_data(collection_id, symbol)
    print(f"Original data shape: {original_data.shape}")
    print(f"Original columns: {original_data.columns.tolist()}")
    
    # Get indicators data
    indicators_data = app.data_collection_manager.get_symbol_indicators(collection_id, symbol)
    print(f"Indicators data shape: {indicators_data.shape if indicators_data is not None else 'None'}")
    print(f"Indicators columns: {indicators_data.columns.tolist() if indicators_data is not None else 'None'}")
    
    # Check for indicator columns in indicators data
    if indicators_data is not None:
        indicator_cols = [col for col in indicators_data.columns if any(indicator in col.upper() for indicator in ['SMA', 'EMA', 'RSI', 'MACD', 'BOLLINGER', 'ATR', 'STOCHASTIC'])]
        print(f"Indicator columns in indicators_data: {len(indicator_cols)}")
        print(f"Sample indicators: {indicator_cols[:5]}")
    
    # Test the merge logic
    print(f"\n🔧 Testing merge logic...")
    if indicators_data is not None:
        # Start with the indicators data (which contains both original and indicators)
        combined_data = indicators_data.copy()
        
        # Ensure we have the original column names for compatibility
        column_mapping = {
            'open': 'Open',
            'high': 'High', 
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        }
        
        # Rename columns if needed
        for old_col, new_col in column_mapping.items():
            if old_col in combined_data.columns and new_col not in combined_data.columns:
                combined_data[new_col] = combined_data[old_col]
        
        # Ensure Date column is present
        if 'Date' not in combined_data.columns and 'date' in combined_data.columns:
            combined_data['Date'] = combined_data['date']
        
        print(f"Combined data shape: {combined_data.shape}")
        print(f"Combined columns: {combined_data.columns.tolist()}")
        
        # Check for indicator columns in combined data
        combined_indicator_cols = [col for col in combined_data.columns if any(indicator in col.upper() for indicator in ['SMA', 'EMA', 'RSI', 'MACD', 'BOLLINGER', 'ATR', 'STOCHASTIC'])]
        print(f"Indicator columns in combined data: {len(combined_indicator_cols)}")
        print(f"Sample indicators: {combined_indicator_cols[:5]}")
    else:
        print("No indicators data available")

if __name__ == "__main__":
    debug_api_endpoint() 