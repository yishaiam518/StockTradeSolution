#!/usr/bin/env python3
"""
Debug script to test the API response and see what data is being returned.
"""

import requests
import json

def test_api_response():
    """Test the historical backtest API endpoint."""
    
    # Test data
    test_data = {
        "strategy": "MACD",
        "profile": "balanced", 
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "benchmark": "SPY"
    }
    
    # Make API call
    try:
        response = requests.post(
            'http://localhost:8080/api/automation/historical-backtest',
            headers={'Content-Type': 'application/json'},
            json=test_data
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if we have trades
            if 'trades' in data:
                trades = data['trades']
                print(f"\nTotal trades: {len(trades)}")
                
                # Check for SELL trades with P&L
                sell_trades = [t for t in trades if t.get('action') == 'SELL']
                print(f"SELL trades: {len(sell_trades)}")
                
                # Check for trades with non-zero P&L
                non_zero_pnl = [t for t in sell_trades if t.get('pnl', 0) != 0]
                print(f"SELL trades with non-zero P&L: {len(non_zero_pnl)}")
                
                # Check for trades with identical buy/sell prices
                same_price_trades = [t for t in trades if t.get('buy_price') == t.get('sell_price')]
                print(f"Trades with same buy/sell price: {len(same_price_trades)}")
                
                # Show first few trades
                print(f"\nFirst 5 trades:")
                for i, trade in enumerate(trades[:5]):
                    print(f"  {i+1}. {trade.get('date')} {trade.get('symbol')} {trade.get('action')} "
                          f"${trade.get('price', 0):.2f} P&L: ${trade.get('pnl', 0):.2f}")
                
                # Show summary if available
                if 'summary' in data:
                    summary = data['summary']
                    print(f"\nSummary:")
                    print(f"  Final portfolio value: ${summary.get('final_portfolio_value', 0):.2f}")
                    print(f"  Total return: {summary.get('total_return', 0):.2f}%")
                    print(f"  Total trades: {summary.get('total_trades', 0)}")
                
            else:
                print("No trades found in response")
                print(f"Response keys: {list(data.keys())}")
                
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error making API call: {e}")

if __name__ == "__main__":
    test_api_response() 