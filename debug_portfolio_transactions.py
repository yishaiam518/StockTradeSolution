#!/usr/bin/env python3
"""
Debug Portfolio Transactions
Test buy/sell transactions and see exact error messages
"""

import requests
import json

def debug_portfolio_transactions():
    base_url = "http://localhost:8080"
    session = requests.Session()
    
    # Test portfolio creation
    print("🔍 Testing Portfolio Creation...")
    test_portfolio = {
        "name": "Debug Portfolio",
        "portfolio_type": "user_managed",
        "initial_cash": 10000.0
    }
    
    response = session.post(f"{base_url}/api/portfolios", json=test_portfolio)
    print(f"Portfolio Creation Status: {response.status_code}")
    
    if response.status_code == 200:
        portfolio_data = response.json()
        portfolio_id = portfolio_data.get('portfolio_id')
        print(f"Created Portfolio ID: {portfolio_id}")
        
        # Test buy transaction
        print("\n🔍 Testing Buy Transaction...")
        buy_data = {
            "symbol": "AAPL",
            "shares": 10,
            "price": 150.0,
            "notes": "Debug buy transaction"
        }
        
        response = session.post(f"{base_url}/api/portfolios/{portfolio_id}/buy", json=buy_data)
        print(f"Buy Transaction Status: {response.status_code}")
        print(f"Buy Transaction Response: {response.text}")
        
        # Test sell transaction
        print("\n🔍 Testing Sell Transaction...")
        sell_data = {
            "symbol": "AAPL",
            "shares": 5,
            "price": 155.0,
            "notes": "Debug sell transaction"
        }
        
        response = session.post(f"{base_url}/api/portfolios/{portfolio_id}/sell", json=sell_data)
        print(f"Sell Transaction Status: {response.status_code}")
        print(f"Sell Transaction Response: {response.text}")
        
        # Check portfolio summary
        print("\n🔍 Checking Portfolio Summary...")
        response = session.get(f"{base_url}/api/portfolios/{portfolio_id}")
        print(f"Portfolio Summary Status: {response.status_code}")
        if response.status_code == 200:
            portfolio_info = response.json()
            summary = portfolio_info.get('summary', {})
            print(f"Summary: {json.dumps(summary, indent=2)}")
        
    else:
        print(f"Portfolio Creation Failed: {response.text}")

if __name__ == "__main__":
    debug_portfolio_transactions()
