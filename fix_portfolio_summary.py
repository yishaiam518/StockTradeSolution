#!/usr/bin/env python3
"""
Script to fix portfolio summary calculation and show correct total P&L
"""

import sqlite3
import os
from datetime import datetime

def fix_portfolio_summary():
    """Fix portfolio summary to show correct total P&L."""
    
    # Database path
    db_path = "data/portfolio.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Portfolio database not found at {db_path}")
        return
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Fixing portfolio summary calculation...")
        print("=" * 50)
        
        # Get all positions with updated P&L
        cursor.execute("""
            SELECT symbol, shares, avg_price, current_price, pnl, pnl_pct
            FROM portfolio_positions 
            WHERE portfolio_id = 2
            ORDER BY pnl DESC
        """)
        
        positions = cursor.fetchall()
        
        if not positions:
            print("❌ No positions found in portfolio")
            return
        
        # Calculate total portfolio values
        total_pnl = 0
        total_positions_value = 0
        total_cost = 0
        
        print("📊 Individual Position Summary:")
        print("-" * 60)
        
        for pos in positions:
            symbol, shares, avg_price, current_price, pnl, pnl_pct = pos
            
            position_value = shares * current_price
            position_cost = shares * avg_price
            
            total_pnl += pnl
            total_positions_value += position_value
            total_cost += position_cost
            
            print(f"{symbol:>6}: ${pnl:>10.2f} ({pnl_pct:>+7.2f}%) | Value: ${position_value:>10.2f}")
        
        # Get current cash
        cursor.execute("""
            SELECT current_cash FROM portfolios WHERE id = 2
        """)
        
        cash_result = cursor.fetchone()
        current_cash = cash_result[0] if cash_result else 0
        
        # Calculate total portfolio value and P&L percentage
        total_portfolio_value = current_cash + total_positions_value
        total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0
        
        print("-" * 60)
        print(f"💰 Cash: ${current_cash:,.2f}")
        print(f"📈 Total Positions Value: ${total_positions_value:,.2f}")
        print(f"💵 Total Portfolio Value: ${total_portfolio_value:,.2f}")
        print(f"📊 Total Cost Basis: ${total_cost:,.2f}")
        print(f"🎯 Total P&L: ${total_pnl:,.2f}")
        print(f"📈 Total P&L %: {total_pnl_pct:+.2f}%")
        
        # Update portfolio summary in the database
        print("\n🔄 Updating portfolio summary...")
        
        # Update the portfolio record with new summary
        cursor.execute("""
            UPDATE portfolios 
            SET updated_at = ?
            WHERE id = 2
        """, (datetime.now().isoformat(),))
        
        # Check if we need to create/update daily performance record
        today = datetime.now().date().isoformat()
        cursor.execute("""
            SELECT id FROM daily_performance 
            WHERE portfolio_id = 2 AND date = ?
        """, (today,))
        
        if cursor.fetchone():
            # Update existing daily performance
            cursor.execute("""
                UPDATE daily_performance 
                SET total_value = ?, pnl = ?, return_pct = ?, cash = ?, positions_value = ?
                WHERE portfolio_id = 2 AND date = ?
            """, (total_portfolio_value, total_pnl, total_pnl_pct, current_cash, total_positions_value, today))
            print("✅ Updated daily performance record")
        else:
            # Create new daily performance record
            cursor.execute("""
                INSERT INTO daily_performance 
                (portfolio_id, date, total_value, pnl, return_pct, cash, positions_value)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (2, today, total_portfolio_value, total_pnl, total_pnl_pct, current_cash, total_positions_value))
            print("✅ Created new daily performance record")
        
        # Commit all changes
        conn.commit()
        
        print("\n🎯 Portfolio Summary Fixed Successfully!")
        print("=" * 50)
        print(f"📊 Dashboard should now show:")
        print(f"   Total P&L: ${total_pnl:,.2f}")
        print(f"   P&L %: {total_pnl_pct:+.2f}%")
        print(f"   Total Value: ${total_portfolio_value:,.2f}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error fixing portfolio summary: {e}")

if __name__ == "__main__":
    fix_portfolio_summary()
