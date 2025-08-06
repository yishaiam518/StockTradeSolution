#!/usr/bin/env python3
"""
Test script to verify AI ranking fix
"""

import requests
import json

def test_ai_ranking():
    """Test the AI ranking API to verify it returns all stocks."""
    
    print("🔍 Testing AI Ranking API...")
    
    # Test the API endpoint
    url = "http://localhost:8080/api/ai-ranking/collection/ALL_20250803_160817/rank"
    params = {"max_stocks": 1000}
    
    try:
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ API Response:")
            print(f"   Success: {data.get('success', False)}")
            print(f"   Total stocks: {data.get('total_stocks', 0)}")
            print(f"   Top stocks array length: {len(data.get('top_stocks', []))}")
            
            if data.get('top_stocks'):
                print(f"\n🏆 First 5 stocks:")
                for i, stock in enumerate(data['top_stocks'][:5], 1):
                    print(f"   {i}. {stock['symbol']} - Score: {stock['total_score']:.1f}")
                
                print(f"\n📊 Last 5 stocks:")
                for i, stock in enumerate(data['top_stocks'][-5:], len(data['top_stocks'])-4):
                    print(f"   {i}. {stock['symbol']} - Score: {stock['total_score']:.1f}")
                
                print(f"\n✅ VERIFICATION:")
                if len(data['top_stocks']) == 112:
                    print("   ✓ SUCCESS: All 112 stocks are being returned!")
                else:
                    print(f"   ❌ ISSUE: Only {len(data['top_stocks'])} stocks returned (expected 112)")
            else:
                print("   ❌ No stocks returned")
                
        else:
            print(f"❌ API failed with status code: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")

if __name__ == "__main__":
    test_ai_ranking() 