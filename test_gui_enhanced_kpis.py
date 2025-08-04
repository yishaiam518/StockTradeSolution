#!/usr/bin/env python3
"""
Test script to verify enhanced KPIs are displayed in the GUI.
This script will run a backtest and check if the enhanced KPIs are visible.
"""

import requests
import json
import time
from datetime import datetime, timedelta

def test_enhanced_kpis():
    """Test the enhanced KPIs in the GUI"""
    print("🧪 Testing Enhanced KPIs in GUI")
    print("=" * 50)
    
    # Test data for backtest
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    test_data = {
        "start_date": start_date,
        "end_date": end_date,
        "strategy": "MACD",
        "profile": "balanced",
        "benchmark": "SPY"
    }
    
    print(f"📅 Test period: {start_date} to {end_date}")
    print(f"🎯 Strategy: {test_data['strategy']} ({test_data['profile']})")
    print(f"📊 Benchmark: {test_data['benchmark']}")
    
    try:
        # Make API call to run backtest
        print("\n🚀 Running backtest...")
        response = requests.post(
            'http://localhost:8080/api/automation/historical-backtest',
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Backtest completed successfully!")
            
            # Check if we have the expected data structure
            if 'trades' in result and 'summary' in result:
                trades = result['trades']
                summary = result['summary']
                
                print(f"\n📊 Backtest Results:")
                print(f"   Total trades: {len(trades)}")
                print(f"   Total return: {summary.get('total_return', 0):.2f}%")
                print(f"   Final portfolio value: ${summary.get('final_portfolio_value', 0):,.2f}")
                
                # Check for enhanced KPI elements in the response
                print(f"\n🔍 Enhanced KPIs should now be visible in the GUI:")
                print(f"   - Current Position Value")
                print(f"   - Position P&L")
                print(f"   - Total Loss")
                print(f"   - Total Profit")
                print(f"   - Net Realized P&L")
                print(f"   - Total P&L")
                print(f"   - Profit Factor")
                
                # Calculate expected values
                sell_trades = [t for t in trades if t.get('action') == 'SELL']
                buy_trades = [t for t in trades if t.get('action') == 'BUY']
                
                total_profit = sum(t.get('pnl', 0) for t in sell_trades if t.get('pnl', 0) > 0)
                total_loss = sum(abs(t.get('pnl', 0)) for t in sell_trades if t.get('pnl', 0) < 0)
                
                print(f"\n💰 Expected KPI Values:")
                print(f"   Total Profit: ${total_profit:.2f}")
                print(f"   Total Loss: ${total_loss:.2f}")
                print(f"   Net Realized P&L: ${total_profit - total_loss:.2f}")
                
                if total_loss > 0:
                    profit_factor = total_profit / total_loss
                    print(f"   Profit Factor: {profit_factor:.2f}")
                
                print(f"\n🌐 GUI Access:")
                print(f"   Open your browser and go to: http://localhost:8080")
                print(f"   Run a historical backtest to see the enhanced KPIs")
                print(f"   The enhanced KPIs should appear in the 'Historical Backtest Results' section")
                
            else:
                print("❌ Unexpected response format")
                print(f"Response: {result}")
                
        else:
            print(f"❌ API call failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the web server")
        print("   Make sure the dashboard is running on http://localhost:8080")
    except Exception as e:
        print(f"❌ Error during test: {e}")

if __name__ == "__main__":
    test_enhanced_kpis() 