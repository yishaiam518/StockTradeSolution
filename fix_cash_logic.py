#!/usr/bin/env python3
"""
Script to fix cash logic - one Available Cash field, Cash for Trading = Available Cash - Position Values
"""

import sqlite3
import os
import json
from datetime import datetime

def fix_cash_logic():
    """Fix cash logic to have one Available Cash field and proper Cash for Trading calculation."""
    
    # Database path
    db_path = "data/portfolio.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Portfolio database not found at {db_path}")
        return
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Fixing cash logic...")
        print("=" * 50)
        
        # Get current portfolio state
        cursor.execute("""
            SELECT current_cash, settings FROM portfolios WHERE id = 2
        """)
        result = cursor.fetchone()
        
        if not result:
            print("❌ Portfolio not found")
            return
        
        current_cash, current_settings = result
        
        # Parse current settings
        if isinstance(current_settings, str):
            try:
                settings = json.loads(current_settings)
            except:
                settings = eval(current_settings)
        else:
            settings = current_settings
        
        print(f"💰 Current Cash: ${current_cash:,.2f}")
        
        # Get current positions value
        cursor.execute("""
            SELECT COALESCE(SUM(shares * current_price), 0) FROM portfolio_positions WHERE portfolio_id = 2
        """)
        positions_value = cursor.fetchone()[0] or 0
        
        print(f"📈 Current Positions Value: ${positions_value:,.2f}")
        
        # New logic:
        # 1. Available Cash = Total portfolio cash (editable)
        # 2. Cash for Trading = Available Cash - Positions Value
        # 3. Cash Reserve = Safety buffer
        
        available_cash = current_cash
        cash_for_trading = available_cash - positions_value
        cash_reserve = available_cash * 0.1  # 10% reserve
        
        print(f"\n🔧 New Cash Logic:")
        print(f"   💰 Available Cash: ${available_cash:,.2f} (editable)")
        print(f"   💼 Cash for Trading: ${cash_for_trading:,.2f} (Available Cash - Positions)")
        print(f"   🛡️  Cash Reserve: ${cash_reserve:,.2f} (10% of Available Cash)")
        
        # Update portfolio settings
        new_settings = {
            "initial_cash": available_cash,
            "available_cash": available_cash,  # The ONE editable field
            "cash_for_trading": cash_for_trading,  # Calculated: Available Cash - Positions
            "cash_reserve": cash_reserve,
            "max_position_size": 0.08,
            "max_positions": 15,
            "stop_loss_pct": 0.12,
            "stop_gain_pct": 0.2,
            "rebalance_frequency": "monthly",
            "risk_level": "conservative",
            "safe_net": available_cash * 0.05,  # 5% safe net
            "transaction_limit_pct": 0.02
        }
        
        # Update portfolio with new settings
        json_settings = json.dumps(new_settings)
        cursor.execute("""
            UPDATE portfolios 
            SET settings = ?, updated_at = ?
            WHERE id = 2
        """, (json_settings, datetime.now().isoformat()))
        
        conn.commit()
        print("✅ Portfolio updated with new cash logic")
        
        # Verify the changes
        cursor.execute("""
            SELECT settings FROM portfolios WHERE id = 2
        """)
        result = cursor.fetchone()
        final_settings = json.loads(result[0])
        
        print("\n✅ Cash Logic Fixed!")
        print("=" * 50)
        print(f"💰 Available Cash: ${final_settings['available_cash']:,.2f}")
        print(f"💼 Cash for Trading: ${final_settings['cash_for_trading']:,.2f}")
        print(f"🛡️  Cash Reserve: ${final_settings['cash_reserve']:,.2f}")
        
        print(f"\n🎯 New Logic:")
        print(f"   • Available Cash: ONE editable field")
        print(f"   • Cash for Trading: Available Cash - Position Values")
        print(f"   • When you change Available Cash, Cash for Trading updates automatically")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error fixing cash logic: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    fix_cash_logic()
