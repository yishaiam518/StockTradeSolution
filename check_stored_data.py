#!/usr/bin/env python3
"""
Check what's actually stored in the database.
"""

import sqlite3
import json
import pandas as pd

def check_stored_data():
    """Check what's actually stored in the database."""
    
    print("🔍 CHECKING STORED DATA")
    print("=" * 50)
    
    conn = sqlite3.connect('data/collections.db')
    
    # Get the stored indicators data
    cursor = conn.execute('''
        SELECT indicators_data FROM technical_indicators 
        WHERE collection_id = ? AND symbol = ?
    ''', ('AMEX_20250803_161652', 'BND'))
    
    row = cursor.fetchone()
    if row:
        print(f"📊 Found stored data for BND")
        print(f"Data length: {len(row[0])} characters")
        
        # Parse the JSON
        try:
            data = json.loads(row[0])
            print(f"JSON keys: {list(data.keys())}")
            print(f"First 10 keys: {list(data.keys())[:10]}")
            
            # Look for indicator keys
            indicator_keys = [k for k in data.keys() if any(indicator in k.upper() for indicator in ['SMA', 'EMA', 'RSI', 'MACD', 'BOLLINGER', 'ATR', 'STOCHASTIC'])]
            print(f"Indicator keys found: {len(indicator_keys)}")
            print(f"First 10 indicators: {indicator_keys[:10]}")
            
            # Convert to DataFrame
            df = pd.read_json(row[0])
            print(f"DataFrame shape: {df.shape}")
            print(f"DataFrame columns: {df.columns.tolist()}")
            
            # Check for indicator columns in DataFrame
            indicator_cols = [col for col in df.columns if any(indicator in col.upper() for indicator in ['SMA', 'EMA', 'RSI', 'MACD', 'BOLLINGER', 'ATR', 'STOCHASTIC'])]
            print(f"Indicator columns in DataFrame: {len(indicator_cols)}")
            print(f"First 10 indicator columns: {indicator_cols[:10]}")
            
        except Exception as e:
            print(f"Error parsing data: {e}")
    else:
        print("No data found for BND")
    
    conn.close()

if __name__ == "__main__":
    check_stored_data() 