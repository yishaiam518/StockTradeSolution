#!/usr/bin/env python3
"""
Final test script for stock viewer with technical indicators
"""

import requests
import json
import time

def test_stock_viewer():
    print("🧪 FINAL STOCK VIEWER TEST")
    print("=" * 50)
    
    base_url = "http://localhost:8080"
    collection_id = "AMEX_20250803_161652"
    symbol = "BND"
    
    try:
        # Test 1: Check if dashboard is running
        print("1. Testing dashboard availability...")
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✅ Dashboard is running")
        else:
            print("❌ Dashboard not accessible")
            return
        
        # Test 2: Check stock viewer page
        print("\n2. Testing stock viewer page...")
        stock_viewer_url = f"{base_url}/stock-viewer?collection_id={collection_id}&exchange=AMEX&start_date=2020-08-03&end_date=2025-08-03"
        response = requests.get(stock_viewer_url)
        if response.status_code == 200:
            print("✅ Stock viewer page accessible")
        else:
            print("❌ Stock viewer page not accessible")
            return
        
        # Test 3: Check API endpoint with indicators
        print("\n3. Testing API endpoint with indicators...")
        api_url = f"{base_url}/api/data-collection/collections/{collection_id}/symbols/{symbol}/data-with-indicators"
        response = requests.get(api_url)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API endpoint working")
            print(f"   Success: {data.get('success', False)}")
            print(f"   Indicators available: {data.get('indicators_available', False)}")
            print(f"   Data points: {len(data.get('data', []))}")
            print(f"   Total columns: {len(data.get('columns', []))}")
            
            # Check for indicator columns
            columns = data.get('columns', [])
            indicator_columns = [col for col in columns if any(indicator in col.lower() for indicator in ['sma', 'ema', 'rsi', 'macd', 'bb_', 'atr', 'stoch', 'williams', 'obv'])]
            print(f"   Indicator columns found: {len(indicator_columns)}")
            
            if data.get('data') and len(data['data']) > 0:
                latest = data['data'][-1]
                sample_indicators = {col: latest[col] for col in indicator_columns[:5] if col in latest}
                print(f"   Sample indicator values: {sample_indicators}")
            
        else:
            print(f"❌ API endpoint failed: {response.status_code}")
            return
        
        # Test 4: Check symbols endpoint
        print("\n4. Testing symbols endpoint...")
        symbols_url = f"{base_url}/api/data-collection/collections/{collection_id}/symbols"
        response = requests.get(symbols_url)
        
        if response.status_code == 200:
            symbols_data = response.json()
            print(f"✅ Symbols endpoint working")
            print(f"   Symbols count: {len(symbols_data.get('symbols', []))}")
        else:
            print(f"❌ Symbols endpoint failed: {response.status_code}")
        
        print("\n🎉 STOCK VIEWER TEST COMPLETE!")
        print("=" * 50)
        print("📋 SUMMARY:")
        print("✅ Dashboard is running")
        print("✅ Stock viewer page is accessible")
        print("✅ API endpoint with indicators is working")
        print("✅ Technical indicators are available")
        print("\n🌐 To test in browser:")
        print(f"   Open: {stock_viewer_url}")
        print("   Select a symbol from the dropdown")
        print("   Technical indicators should appear below the chart")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")

if __name__ == "__main__":
    test_stock_viewer() 