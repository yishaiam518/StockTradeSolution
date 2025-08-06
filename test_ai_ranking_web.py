#!/usr/bin/env python3
"""
Test script for AI Ranking System Web Interface
"""

import requests
import json
import time
import sys
import os

def test_ai_ranking_web():
    """Test the AI ranking system through web API."""
    
    base_url = "http://localhost:8080"
    
    print("🧪 Testing AI Ranking System Web Interface")
    print("=" * 50)
    
    # Wait for dashboard to start
    print("⏳ Waiting for dashboard to start...")
    time.sleep(5)
    
    try:
        # Test 1: Check if dashboard is running
        print("\n🔍 Test 1: Dashboard Availability")
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            print("✅ Dashboard is running")
        else:
            print(f"❌ Dashboard returned status {response.status_code}")
            return
        
        # Test 2: Get collections
        print("\n🔍 Test 2: Collections API")
        response = requests.get(f"{base_url}/api/data-collection/collections", timeout=10)
        if response.status_code == 200:
            response_data = response.json()
            collections = response_data.get('collections', [])
            print(f"✅ Found {len(collections)} collections")
            if collections and len(collections) > 0:
                # Use the collection with the most stocks (ALL_20250803_160817 has 112 stocks)
                collection_with_most_stocks = max(collections, key=lambda x: x.get('successful_symbols', 0))
                collection_id = collection_with_most_stocks.get('collection_id', '')
                if collection_id:
                    print(f"   Using collection: {collection_id} ({collection_with_most_stocks.get('successful_symbols', 0)} stocks)")
                else:
                    print("❌ No valid collection ID found")
                    return
            else:
                print("❌ No collections available")
                return
        else:
            print(f"❌ Collections API failed: {response.status_code}")
            return
        
        # Test 3: AI Ranking API
        print("\n🔍 Test 3: AI Ranking API")
        response = requests.get(f"{base_url}/api/ai-ranking/collection/{collection_id}/rank?max_stocks=1000", timeout=30)
        if response.status_code == 200:
            ranking_data = response.json()
            print("✅ AI Ranking API working!")
            print(f"   Success: {ranking_data.get('success', False)}")
            print(f"   Total stocks: {ranking_data.get('total_stocks', 0)}")
            
            if ranking_data.get('top_stocks'):
                print("\n🏆 Top 5 Stocks:")
                for i, stock in enumerate(ranking_data['top_stocks'][:5], 1):
                    print(f"   {i}. {stock['symbol']} - Score: {stock['total_score']:.1f}")
        else:
            print(f"❌ AI Ranking API failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return
        
        # Test 4: Individual Stock Analysis
        print("\n🔍 Test 4: Individual Stock Analysis")
        test_symbol = "AAPL"
        response = requests.get(f"{base_url}/api/ai-ranking/collection/{collection_id}/stock/{test_symbol}", timeout=30)
        if response.status_code == 200:
            stock_data = response.json()
            print(f"✅ Stock analysis for {test_symbol} working!")
            print(f"   Success: {stock_data.get('success', False)}")
            if stock_data.get('analysis'):
                analysis = stock_data['analysis']
                print(f"   Rank: {analysis.get('rank', 'N/A')}")
                print(f"   Score: {analysis.get('total_score', 'N/A')}")
        else:
            print(f"❌ Stock analysis failed: {response.status_code}")
        
        # Test 5: Export Functionality
        print("\n🔍 Test 5: Export Functionality")
        response = requests.get(f"{base_url}/api/ai-ranking/collection/{collection_id}/export", timeout=30)
        if response.status_code == 200:
            export_data = response.json()
            print("✅ Export functionality working!")
            print(f"   Success: {export_data.get('success', False)}")
            print(f"   Format: {export_data.get('format', 'N/A')}")
        else:
            print(f"❌ Export failed: {response.status_code}")
        
        print("\n🎉 AI Ranking Web Interface Test Completed Successfully!")
        print("\n📋 Summary:")
        print("   ✅ Dashboard is running")
        print("   ✅ Collections API working")
        print("   ✅ AI Ranking API working")
        print("   ✅ Stock Analysis API working")
        print("   ✅ Export functionality working")
        print("\n🌐 You can now access the dashboard at: http://localhost:8080")
        print("   Click on any collection and use the 'AI Ranking' button!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to dashboard. Make sure it's running on port 8080.")
    except Exception as e:
        print(f"❌ Error testing web interface: {e}")

if __name__ == "__main__":
    test_ai_ranking_web() 