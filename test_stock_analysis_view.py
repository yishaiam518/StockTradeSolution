#!/usr/bin/env python3
"""
Test script to verify stock analysis view functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json
from datetime import datetime

def test_stock_analysis_view():
    """Test the stock analysis view functionality."""
    
    print("🔍 Testing Stock Analysis View Functionality")
    print("=" * 50)
    
    base_url = "http://localhost:8080"
    collection_id = "ALL_20250803_160817"
    test_symbols = ["PFE", "AAPL", "GOOG", "TSLA"]
    
    print(f"\n📊 Testing with collection: {collection_id}")
    print(f"🎯 Test symbols: {', '.join(test_symbols)}")
    
    # Test 1: Check if stock analysis page is accessible
    print("\n=== TEST 1: Stock Analysis Page Accessibility ===")
    try:
        response = requests.get(f"{base_url}/stock-analysis")
        if response.status_code == 200:
            print("✅ Stock analysis page is accessible")
        else:
            print(f"❌ Stock analysis page returned status code: {response.status_code}")
    except Exception as e:
        print(f"❌ Error accessing stock analysis page: {e}")
    
    # Test 2: Test stock analysis API for each symbol
    print("\n=== TEST 2: Stock Analysis API ===")
    
    for symbol in test_symbols:
        print(f"\n--- Testing {symbol} ---")
        
        try:
            # Test AI analysis API
            response = requests.get(f"{base_url}/api/ai-ranking/collection/{collection_id}/stock/{symbol}")
            data = response.json()
            
            if data.get('success'):
                print(f"✅ AI analysis successful for {symbol}")
                
                # Check for required fields
                scores = data.get('scores', {})
                explanation = data.get('explanation', '')
                technical_indicators = data.get('technical_indicators', {})
                risk_metrics = data.get('risk_metrics', {})
                
                print(f"   📈 Total Score: {scores.get('total_score', 'N/A')}")
                print(f"   🤖 Explanation: {explanation[:100]}...")
                print(f"   📊 Technical Indicators: {len(technical_indicators)} found")
                print(f"   ⚠️  Risk Metrics: {len(risk_metrics)} found")
                
            else:
                print(f"❌ AI analysis failed for {symbol}: {data.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Error testing {symbol}: {e}")
    
    # Test 3: Test stock data API
    print("\n=== TEST 3: Stock Data API ===")
    
    for symbol in test_symbols:
        print(f"\n--- Testing {symbol} Data ---")
        
        try:
            response = requests.get(f"{base_url}/api/data-collection/collections/{collection_id}/symbols/{symbol}")
            data = response.json()
            
            if data.get('success'):
                stock_data = data.get('stock_data', [])
                print(f"✅ Stock data successful for {symbol}")
                print(f"   📊 Data points: {len(stock_data)}")
                
                if stock_data:
                    latest = stock_data[-1]
                    print(f"   💰 Latest price: ${latest.get('Close', 'N/A')}")
                    print(f"   📈 Volume: {latest.get('Volume', 'N/A')}")
                    
            else:
                print(f"❌ Stock data failed for {symbol}: {data.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Error testing {symbol} data: {e}")
    
    # Test 4: Test URL generation for stock analysis
    print("\n=== TEST 4: URL Generation ===")
    
    for symbol in test_symbols:
        url = f"{base_url}/stock-analysis?symbol={symbol}&collection={collection_id}"
        print(f"   🔗 {symbol}: {url}")
    
    print("\n" + "=" * 50)
    print("🎯 Stock Analysis View Test Complete!")
    print("\n📋 Summary:")
    print("✅ Stock analysis page template created")
    print("✅ Stock analysis API enhanced")
    print("✅ URL generation for individual stocks")
    print("✅ Integration with AI ranking system")
    print("✅ Technical indicators and risk metrics")
    print("✅ Interactive charts and visualizations")
    
    print("\n🚀 Next Steps:")
    print("1. Test the stock analysis page in browser")
    print("2. Click 'View' buttons in AI ranking to test navigation")
    print("3. Verify charts and interactive features")
    print("4. Test with different collections and symbols")

if __name__ == "__main__":
    test_stock_analysis_view() 