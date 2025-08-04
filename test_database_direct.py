#!/usr/bin/env python3
"""
Direct database test to see what's actually stored.
"""

import sqlite3
import os

def test_database_direct():
    """Test database contents directly."""
    db_path = "data/collections.db"
    
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return
    
    try:
        with sqlite3.connect(db_path) as conn:
            # Get all collections with scheduler fields
            cursor = conn.execute('''
                SELECT collection_id, auto_update, update_interval, last_run, next_run 
                FROM collections 
                ORDER BY collection_date DESC
            ''')
            rows = cursor.fetchall()
            
            print(f"Found {len(rows)} collections in database:")
            for row in rows:
                print(f"  Collection: {row[0]}")
                print(f"    auto_update: {row[1]}")
                print(f"    update_interval: {row[2]}")
                print(f"    last_run: {row[3]}")
                print(f"    next_run: {row[4]}")
                print()
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_database_direct() 