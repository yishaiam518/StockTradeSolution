#!/usr/bin/env python3
"""
Script to reset AI Portfolio for a fresh start tomorrow
"""

import sqlite3
import os
from datetime import datetime

def reset_ai_portfolio():
    """Reset AI Portfolio to initial state for fresh start."""
    
    # Database path
    db_path = "data/portfolio.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Portfolio database not found at {db_path}")
        return
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Resetting AI Portfolio for fresh start...")
        print("=" * 50)
        
        # Get current AI portfolio state
        cursor.execute("""
            SELECT id, name, initial_cash, current_cash 
            FROM portfolios 
            WHERE id = 2
        """)
        portfolio = cursor.fetchone()
        
        if not portfolio:
            print("❌ AI Portfolio (ID 2) not found")
            return
        
        portfolio_id, name, initial_cash, current_cash = portfolio
        print(f"📊 Found AI Portfolio: {name} (ID: {portfolio_id})")
        print(f"💰 Initial Cash: ${initial_cash:,.2f}")
        print(f"💵 Current Cash: ${current_cash:,.2f}")
        
        # Get current positions
        cursor.execute("""
            SELECT symbol, shares, avg_price, current_price, pnl, pnl_pct
            FROM portfolio_positions 
            WHERE portfolio_id = 2
        """)
        positions = cursor.fetchall()
        
        print(f"📈 Current Positions: {len(positions)}")
        for pos in positions:
            symbol, shares, avg_price, current_price, pnl, pnl_pct = pos
            print(f"   {symbol}: {shares} shares @ ${avg_price:.2f} (P&L: ${pnl:.2f}, {pnl_pct:.2f}%)")
        
        # Get current transactions
        cursor.execute("""
            SELECT COUNT(*) FROM portfolio_transactions 
            WHERE portfolio_id = 2
        """)
        transaction_count = cursor.fetchone()[0]
        print(f"📝 Current Transactions: {transaction_count}")
        
        # Confirm reset
        print("\n⚠️  WARNING: This will reset the AI Portfolio to initial state!")
        print("   - All positions will be sold at current prices")
        print("   - All transactions will be cleared")
        print("   - Portfolio will return to initial cash amount")
        print("   - AI will start fresh tomorrow")
        
        confirm = input("\n❓ Are you sure you want to reset? Type 'YES' to confirm: ")
        if confirm != "YES":
            print("❌ Reset cancelled")
            return
        
        print("\n🔄 Starting AI Portfolio reset...")
        
        # Step 1: Calculate total cash from selling all positions
        total_cash_from_sales = 0
        for pos in positions:
            symbol, shares, current_price, _, _, _ = pos
            sale_value = shares * current_price
            total_cash_from_sales += sale_value
            print(f"   💰 Selling {symbol}: {shares} shares @ ${current_price:.2f} = ${sale_value:.2f}")
        
        # Step 2: Update portfolio cash
        new_total_cash = initial_cash + total_cash_from_sales
        cursor.execute("""
            UPDATE portfolios 
            SET current_cash = ?, updated_at = ?
            WHERE id = 2
        """, (new_total_cash, datetime.now().isoformat()))
        
        print(f"💰 Portfolio cash updated: ${new_total_cash:,.2f}")
        
        # Step 3: Clear all positions
        cursor.execute("""
            DELETE FROM portfolio_positions 
            WHERE portfolio_id = 2
        """)
        print(f"🗑️  Cleared {len(positions)} positions")
        
        # Step 4: Clear all transactions
        cursor.execute("""
            DELETE FROM portfolio_transactions 
            WHERE portfolio_id = 2
        """)
        print(f"🗑️  Cleared {transaction_count} transactions")
        
        # Step 5: Clear algorithm decisions
        cursor.execute("""
            DELETE FROM algorithm_decisions 
            WHERE portfolio_id = 2
        """)
        print("🗑️  Cleared algorithm decisions")
        
        # Step 6: Clear daily performance
        cursor.execute("""
            DELETE FROM daily_performance 
            WHERE portfolio_id = 2
        """)
        print("🗑️  Cleared daily performance")
        
        # Commit all changes
        conn.commit()
        
        # Verify reset
        cursor.execute("""
            SELECT COUNT(*) FROM portfolio_positions WHERE portfolio_id = 2
        """)
        remaining_positions = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM portfolio_transactions WHERE portfolio_id = 2
        """)
        remaining_transactions = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT current_cash FROM portfolios WHERE id = 2
        """)
        final_cash = cursor.fetchone()[0]
        
        print("\n✅ AI Portfolio Reset Complete!")
        print("=" * 50)
        print(f"💰 Final Cash: ${final_cash:,.2f}")
        print(f"📈 Remaining Positions: {remaining_positions}")
        print(f"📝 Remaining Transactions: {remaining_transactions}")
        print(f"🔄 AI Portfolio ready for fresh start tomorrow!")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error resetting AI Portfolio: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    reset_ai_portfolio()
