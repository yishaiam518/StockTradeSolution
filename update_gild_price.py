#!/usr/bin/env python3
"""
Script to manually update GILD position price in AI Portfolio
"""

import sqlite3
import os
from datetime import datetime

def update_gild_price():
    """Update GILD position price to current market price."""
    
    # Database path
    db_path = "data/portfolio.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Portfolio database not found at {db_path}")
        return
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Current GILD market price (from Yahoo)
        current_gild_price = 120.47
        
        # Update GILD position price
        cursor.execute("""
            UPDATE portfolio_positions 
            SET current_price = ?, updated_at = ?
            WHERE portfolio_id = 2 AND symbol = 'GILD'
        """, (current_gild_price, datetime.now().isoformat()))
        
        # Update position P&L
        cursor.execute("""
            UPDATE portfolio_positions 
            SET pnl = (current_price - avg_price) * shares,
                pnl_pct = ((current_price - avg_price) / avg_price) * 100
            WHERE portfolio_id = 2 AND symbol = 'GILD'
        """)
        
        # Commit changes
        conn.commit()
        
        # Verify the update
        cursor.execute("""
            SELECT symbol, avg_price, current_price, shares, pnl, pnl_pct
            FROM portfolio_positions 
            WHERE portfolio_id = 2 AND symbol = 'GILD'
        """)
        
        result = cursor.fetchone()
        if result:
            symbol, avg_price, current_price, shares, pnl, pnl_pct = result
            print(f"✅ GILD position updated successfully!")
            print(f"   Symbol: {symbol}")
            print(f"   Bought at: ${avg_price:.2f}")
            print(f"   Current price: ${current_price:.2f}")
            print(f"   Shares: {shares}")
            print(f"   Unrealized P&L: ${pnl:.2f}")
            print(f"   P&L %: {pnl_pct:.2f}%")
            
            # Calculate expected values
            expected_pnl = (current_gild_price - avg_price) * shares
            expected_pnl_pct = ((current_gild_price - avg_price) / avg_price) * 100
            
            print(f"\n📊 Expected values:")
            print(f"   Unrealized P&L: ${expected_pnl:.2f}")
            print(f"   P&L %: {expected_pnl_pct:.2f}%")
        else:
            print("❌ GILD position not found in portfolio")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error updating GILD price: {e}")

if __name__ == "__main__":
    update_gild_price()
