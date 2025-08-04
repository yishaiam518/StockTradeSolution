#!/usr/bin/env python3
"""
Debug script to check indicator storage and retrieval.
"""

import sqlite3
import json
import pandas as pd

def debug_indicators_storage():
    """Debug what's being stored in the indicators database."""
    
    print("🔍 DEBUGGING INDICATOR STORAGE")
    print("=" * 50)
    
    # Connect to database
    conn = sqlite3.connect('data/collections.db')
    
    # Check what's in the technical_indicators table
    cursor = conn.execute('''
        SELECT collection_id, symbol, calculated_date, 
               LENGTH(indicators_data) as data_length
        FROM technical_indicators 
        WHERE collection_id = 'AMEX_20250803_161652'
        LIMIT 5
    ''')
    
    rows = cursor.fetchall()
    print(f"Found {len(rows)} indicator records:")
    for row in rows:
        print(f"  {row[0]} - {row[1]} - {row[2]} - {row[3]} bytes")
    
    # Get the actual data for BND
    cursor = conn.execute('''
        SELECT indicators_data FROM technical_indicators 
        WHERE collection_id = ? AND symbol = ?
    ''', ('AMEX_20250803_161652', 'BND'))
    
    row = cursor.fetchone()
    if row:
        print(f"\n📊 BND Indicators Data Analysis:")
        print(f"Data length: {len(row[0])} characters")
        
        # Parse the JSON
        try:
            data = json.loads(row[0])
            print(f"JSON keys: {list(data.keys())}")
            
            # Check if it's a DataFrame format
            if 'Date' in data:
                print(f"Date column has {len(data['Date'])} entries")
                print(f"First few dates: {list(data['Date'].values())[:5]}")
            
            # Look for indicator columns
            indicator_columns = [col for col in data.keys() if any(indicator in col.upper() for indicator in ['SMA', 'EMA', 'RSI', 'MACD', 'BOLLINGER', 'ATR', 'STOCHASTIC'])]
            print(f"Potential indicator columns: {indicator_columns}")
            
            # Convert to DataFrame to see structure
            df = pd.read_json(row[0])
            print(f"DataFrame shape: {df.shape}")
            print(f"DataFrame columns: {df.columns.tolist()}")
            
            # Check for indicator columns in DataFrame
            indicator_cols = [col for col in df.columns if any(indicator in col.upper() for indicator in ['SMA', 'EMA', 'RSI', 'MACD', 'BOLLINGER', 'ATR', 'STOCHASTIC'])]
            print(f"Indicator columns in DataFrame: {indicator_cols}")
            
        except Exception as e:
            print(f"Error parsing JSON: {e}")
    else:
        print("No indicator data found for BND")
    
    conn.close()

if __name__ == "__main__":
    debug_indicators_storage() 