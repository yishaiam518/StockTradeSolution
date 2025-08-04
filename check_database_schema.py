#!/usr/bin/env python3
"""
Script to check the database schema for the collections table.
"""

import sqlite3
import os

def check_database_schema():
    """Check the database schema for the collections table."""
    db_path = "data/collections.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return
    
    try:
        with sqlite3.connect(db_path) as conn:
            # Get table info
            cursor = conn.execute("PRAGMA table_info(collections)")
            columns = cursor.fetchall()
            
            print("📊 Collections table schema:")
            print("=" * 50)
            for column in columns:
                print(f"  {column[1]} ({column[2]}) - {'NOT NULL' if column[3] else 'NULL'}")
            
            # Check if specific columns exist
            column_names = [col[1] for col in columns]
            required_columns = ['auto_update', 'update_interval', 'last_run', 'next_run']
            
            print("\n🔍 Checking required columns:")
            for col in required_columns:
                if col in column_names:
                    print(f"  ✅ {col}")
                else:
                    print(f"  ❌ {col} - MISSING")
            
            # Show sample data
            print("\n📋 Sample data from collections table:")
            cursor = conn.execute("SELECT collection_id, auto_update, update_interval, last_run, next_run FROM collections LIMIT 3")
            rows = cursor.fetchall()
            
            for row in rows:
                print(f"  Collection: {row[0]}")
                print(f"    auto_update: {row[1]}")
                print(f"    update_interval: {row[2]}")
                print(f"    last_run: {row[3]}")
                print(f"    next_run: {row[4]}")
                print()
                
    except Exception as e:
        print(f"❌ Error checking database: {e}")

if __name__ == "__main__":
    check_database_schema() 