#!/usr/bin/env python3
"""
Script to simplify portfolio cash structure and remove redundancy
"""

import sqlite3
import os
import json
from datetime import datetime

def simplify_cash_structure():
    """Simplify portfolio cash structure to be more logical."""
    
    # Database path
    db_path = "data/portfolio.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Portfolio database not found at {db_path}")
        return
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Simplifying portfolio cash structure...")
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
        print(f"📊 Current Settings: {json.dumps(settings, indent=2)}")
        
        # Create simplified cash structure
        print("\n🔧 Creating simplified cash structure...")
        
        # Simplified approach:
        # 1. Available Cash = Total portfolio cash (what user sees)
        # 2. Cash for Trading = Amount available for new positions (90% of total)
        # 3. Cash Reserve = Amount kept as safety buffer (10% of total)
        
        new_settings = {
            "initial_cash": current_cash,
            "available_cash": current_cash,  # Total cash user sees
            "cash_for_trading": current_cash * 0.9,  # 90% for trading
            "cash_reserve": current_cash * 0.1,  # 10% as reserve
            "max_position_size": 0.08,
            "max_positions": 15,
            "stop_loss_pct": 0.12,
            "stop_gain_pct": 0.2,
            "rebalance_frequency": "monthly",
            "risk_level": "conservative",
            "safe_net": current_cash * 0.05,  # 5% safe net
            "transaction_limit_pct": 0.02
        }
        
        print(f"✅ New simplified structure:")
        print(f"   💰 Available Cash: ${new_settings['available_cash']:,.2f}")
        print(f"   💼 Cash for Trading: ${new_settings['cash_for_trading']:,.2f}")
        print(f"   🛡️  Cash Reserve: ${new_settings['cash_reserve']:,.2f}")
        
        # Update portfolio with simplified settings
        json_settings = json.dumps(new_settings)
        cursor.execute("""
            UPDATE portfolios 
            SET settings = ?, updated_at = ?
            WHERE id = 2
        """, (json_settings, datetime.now().isoformat()))
        
        conn.commit()
        print("✅ Portfolio updated with simplified cash structure")
        
        # Verify the changes
        cursor.execute("""
            SELECT settings FROM portfolios WHERE id = 2
        """)
        result = cursor.fetchone()
        final_settings = json.loads(result[0])
        
        print("\n✅ Cash Structure Simplified!")
        print("=" * 50)
        print(f"💰 Available Cash: ${final_settings['available_cash']:,.2f}")
        print(f"💼 Cash for Trading: ${final_settings['cash_for_trading']:,.2f}")
        print(f"🛡️  Cash Reserve: ${final_settings['cash_reserve']:,.2f}")
        print(f"📊 Total Cash: ${current_cash:,.2f}")
        
        print(f"\n🎯 Benefits of new structure:")
        print(f"   • Available Cash = Total portfolio cash")
        print(f"   • Cash for Trading = Amount for new positions")
        print(f"   • Cash Reserve = Safety buffer")
        print(f"   • No more confusing redundant fields!")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error simplifying cash structure: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    simplify_cash_structure()
