#!/usr/bin/env python3
"""
Script to fix portfolio settings format from Python dict to JSON
"""

import sqlite3
import os
import json
from datetime import datetime

def fix_settings_format():
    """Fix portfolio settings format to proper JSON."""
    
    # Database path
    db_path = "data/portfolio.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Portfolio database not found at {db_path}")
        return
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Fixing portfolio settings format...")
        print("=" * 50)
        
        # Get current settings
        cursor.execute("""
            SELECT settings FROM portfolios WHERE id = 2
        """)
        result = cursor.fetchone()
        
        if not result:
            print("❌ Portfolio not found")
            return
        
        current_settings = result[0]
        print(f"📝 Current settings format: {type(current_settings)}")
        print(f"📄 Settings content: {current_settings[:100]}...")
        
        # Convert Python dict string to proper JSON
        try:
            # First, convert the string representation to actual dict
            if isinstance(current_settings, str):
                # Remove the string quotes and eval safely
                settings_dict = eval(current_settings)
            else:
                settings_dict = current_settings
            
            # Convert to proper JSON
            json_settings = json.dumps(settings_dict)
            
            print(f"✅ Converted to JSON format")
            print(f"📊 Settings: {json_settings}")
            
            # Update the database with JSON format
            cursor.execute("""
                UPDATE portfolios 
                SET settings = ?, updated_at = ?
                WHERE id = 2
            """, (json_settings, datetime.now().isoformat()))
            
            conn.commit()
            print("✅ Settings updated in database")
            
        except Exception as e:
            print(f"❌ Error converting settings: {e}")
            return
        
        # Verify the fix
        cursor.execute("""
            SELECT settings FROM portfolios WHERE id = 2
        """)
        result = cursor.fetchone()
        final_settings = result[0]
        
        print("\n✅ Settings Format Fixed!")
        print("=" * 50)
        print(f"📝 Final format: {type(final_settings)}")
        print(f"📄 Content: {final_settings[:100]}...")
        
        # Test JSON parsing
        try:
            parsed = json.loads(final_settings)
            print(f"✅ JSON parsing successful: {len(parsed)} settings")
        except Exception as e:
            print(f"❌ JSON parsing failed: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error fixing settings format: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    fix_settings_format()
