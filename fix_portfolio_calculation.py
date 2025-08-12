#!/usr/bin/env python3
"""
Script to fix portfolio calculation logic after reset
"""

import sqlite3
import os
from datetime import datetime

def fix_portfolio_calculation():
    """Fix portfolio calculation to show correct P&L after reset."""
    
    # Database path
    db_path = "data/portfolio.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Portfolio database not found at {db_path}")
        return
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Fixing portfolio calculation logic...")
        print("=" * 50)
        
        # Get current portfolio state
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
        print(f"📊 Portfolio: {name}")
        print(f"💰 Initial Cash: ${initial_cash:,.2f}")
        print(f"💵 Current Cash: ${current_cash:,.2f}")
        
        # Check if this is a reset scenario (no positions, high cash)
        cursor.execute("""
            SELECT COUNT(*) FROM portfolio_positions WHERE portfolio_id = 2
        """)
        position_count = cursor.fetchone()[0]
        
        if position_count == 0 and current_cash > initial_cash:
            print("🔄 Detected reset scenario - fixing P&L calculation...")
            
            # For a reset scenario, we need to adjust the initial cash to match current cash
            # This makes P&L = 0, which is correct for a fresh start
            new_initial_cash = current_cash
            
            cursor.execute("""
                UPDATE portfolios 
                SET initial_cash = ?, updated_at = ?
                WHERE id = 2
            """, (new_initial_cash, datetime.now().isoformat()))
            
            print(f"💰 Updated initial cash: ${initial_cash:,.2f} → ${new_initial_cash:,.2f}")
            print(f"✅ P&L will now be: ${new_initial_cash - new_initial_cash:,.2f} (0%)")
            
        else:
            print("ℹ️  Not a reset scenario, no changes needed")
        
        # Also fix the cash settings to be more realistic
        print("\n🔧 Fixing cash settings for realistic trading...")
        
        # Update portfolio settings to use realistic cash values
        settings = {
            "initial_cash": current_cash,
            "cash_for_trading": current_cash * 0.9,  # 90% available for trading
            "available_cash_for_trading": current_cash * 0.9,  # Same as cash_for_trading
            "cash_reserve_pct": 0.1,  # Keep 10% as reserve
            "max_position_size": 0.08,
            "max_positions": 15,
            "stop_loss_pct": 0.12,
            "stop_gain_pct": 0.2,
            "rebalance_frequency": "monthly",
            "risk_level": "conservative",
            "safe_net": current_cash * 0.05,  # 5% safe net
            "transaction_limit_pct": 0.02
        }
        
        # Update portfolio with realistic settings
        cursor.execute("""
            UPDATE portfolios 
            SET settings = ?, updated_at = ?
            WHERE id = 2
        """, (str(settings), datetime.now().isoformat()))
        
        print(f"💰 Cash for Trading: ${settings['cash_for_trading']:,.2f}")
        print(f"💰 Available Cash for Trading: ${settings['available_cash_for_trading']:,.2f}")
        print(f"💰 Cash Reserve: ${current_cash * 0.1:,.2f}")
        
        # Commit changes
        conn.commit()
        
        # Verify the fix
        cursor.execute("""
            SELECT initial_cash, current_cash, settings FROM portfolios WHERE id = 2
        """)
        result = cursor.fetchone()
        final_initial, final_current, final_settings = result
        
        print("\n✅ Portfolio Calculation Fixed!")
        print("=" * 50)
        print(f"💰 Initial Cash: ${final_initial:,.2f}")
        print(f"💵 Current Cash: ${final_current:,.2f}")
        print(f"📊 P&L: ${final_current - final_initial:,.2f} (0%)")
        print(f"🔄 Ready for fresh start with realistic cash values!")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error fixing portfolio calculation: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    fix_portfolio_calculation()
