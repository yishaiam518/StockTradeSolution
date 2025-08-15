#!/usr/bin/env python3
"""
Fix AI Portfolio cash calculation and ensure safe net is respected
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def fix_ai_portfolio_cash():
    """Fix the AI portfolio cash calculation to respect safe net."""
    try:
        import json
        import sqlite3
        from src.portfolio_management.portfolio_database import PortfolioDatabase
        from src.portfolio_management.portfolio_manager import PortfolioManager, PortfolioSettings, RiskLevel
        from src.data_collection.data_manager import DataCollectionManager
        
        print("🔧 Fixing AI Portfolio cash calculation...")
        print("=" * 50)
        
        # Initialize components
        data_manager = DataCollectionManager()
        portfolio_db = PortfolioDatabase()
        portfolio_manager = PortfolioManager(data_manager)
        
        # Get the AI portfolio (ID 2)
        portfolio = portfolio_db.get_portfolio(2)
        if not portfolio:
            print("❌ AI Portfolio not found")
            return False
            
        print(f"📊 Current AI Portfolio Status:")
        print(f"   Name: {portfolio.name}")
        print(f"   Initial Cash: ${portfolio.initial_cash:,.2f}")
        print(f"   Current Cash: ${portfolio.current_cash:,.2f}")
        
        # Get current settings
        settings = portfolio_manager._load_settings_from_portfolio(portfolio)
        if settings:
            print(f"   Safe Net: ${settings.safe_net:,.2f}")
            print(f"   Transaction Limit %: {settings.transaction_limit_pct*100:.1f}%")
            print(f"   Cash for Trading: ${settings.cash_for_trading:,.2f}")
            print(f"   Available Cash for Trading: ${settings.available_cash_for_trading:,.2f}")
        
        # Get current positions
        positions = portfolio_db.get_portfolio_positions(2)
        total_positions_value = sum(pos.shares * pos.current_price for pos in positions)
        
        print(f"\n📈 Current Positions:")
        print(f"   Total Positions: {len(positions)}")
        print(f"   Total Positions Value: ${total_positions_value:,.2f}")
        
        # Calculate what the cash should be
        # The total portfolio value should be: initial_cash + P&L
        # Current cash should be: total_portfolio_value - positions_value
        # But it should never go below safe_net
        
        expected_total_value = portfolio.initial_cash + (portfolio.current_cash + total_positions_value - portfolio.initial_cash)
        expected_current_cash = expected_total_value - total_positions_value
        
        print(f"\n🧮 Cash Calculation:")
        print(f"   Expected Total Value: ${expected_total_value:,.2f}")
        print(f"   Expected Current Cash: ${expected_current_cash:,.2f}")
        
        # Ensure current cash respects safe net
        if settings and expected_current_cash < settings.safe_net:
            print(f"   ⚠️  Current cash would be below safe net (${settings.safe_net:,.2f})")
            print(f"   🔧 Adjusting current cash to safe net level")
            expected_current_cash = settings.safe_net
        
        # Update the portfolio with correct cash values
        print(f"\n💾 Updating portfolio cash...")
        
        with sqlite3.connect(portfolio_db.db_path) as conn:
            cursor = conn.cursor()
            
            # Update current cash
            cursor.execute("""
                UPDATE portfolios 
                SET current_cash = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (expected_current_cash, 2))
            
            # Update settings to ensure consistency
            if settings:
                # Update available_cash_for_trading to match current_cash
                new_available_cash = max(0, expected_current_cash - settings.safe_net)
                settings.available_cash_for_trading = new_available_cash
                
                # Update portfolio settings
                portfolio.settings = settings.__dict__.copy()
                portfolio.settings['risk_level'] = settings.risk_level.value
                
                cursor.execute("""
                    UPDATE portfolios 
                    SET settings = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (json.dumps(portfolio.settings), 2))
            
            conn.commit()
        
        print(f"✅ Portfolio updated successfully!")
        print(f"   New Current Cash: ${expected_current_cash:,.2f}")
        if settings:
            print(f"   New Available Cash for Trading: ${new_available_cash:,.2f}")
        
        # Verify the fix
        print(f"\n🔍 Verifying the fix...")
        updated_portfolio = portfolio_db.get_portfolio(2)
        print(f"   Updated Current Cash: ${updated_portfolio.current_cash:,.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing portfolio cash: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = fix_ai_portfolio_cash()
    sys.exit(0 if success else 1)
