#!/usr/bin/env python3
"""
Test script to manually trigger AI ranking update
"""

import requests
import json
from datetime import datetime

def test_ai_ranking_manual_trigger():
    """Test manual AI ranking trigger"""
    
    collection_id = "ALL_20250803_160817"
    base_url = "http://localhost:8080"
    
    print("🤖 Testing Manual AI Ranking Trigger")
    print("=" * 50)
    
    try:
        # Test 1: Check current status
        print("=== TEST 1: Current Status ===")
        response = requests.get(f"{base_url}/api/data-collection/collections/{collection_id}/scheduler/status")
        data = response.json()
        
        print(f"📅 Current AI Ranking: {data.get('ai_ranking_last_update_formatted', 'Never')}")
        
        # Test 2: Manually trigger AI ranking
        print("\n=== TEST 2: Manual Trigger ===")
        print("🔄 Triggering AI ranking update...")
        
        # The API automatically triggers AI ranking when status is checked
        response = requests.get(f"{base_url}/api/data-collection/collections/{collection_id}/scheduler/status")
        data = response.json()
        
        print(f"📅 Updated AI Ranking: {data.get('ai_ranking_last_update_formatted', 'Never')}")
        
        # Test 3: Check if the update was successful
        print("\n=== TEST 3: Verification ===")
        if data.get('ai_ranking_last_update'):
            update_time = datetime.fromisoformat(data['ai_ranking_last_update'].replace('Z', '+00:00'))
            now = datetime.now()
            time_diff = (now - update_time).total_seconds()
            
            print(f"⏰ Update Time: {update_time}")
            print(f"⏰ Current Time: {now}")
            print(f"⏱️  Time Difference: {time_diff:.1f} seconds")
            
            if time_diff < 60:  # Less than 1 minute
                print("✅ AI ranking was successfully updated!")
            else:
                print("⚠️  AI ranking was not updated recently")
        else:
            print("❌ No AI ranking timestamp found")
        
        # Test 4: Check metadata
        print("\n=== TEST 4: Metadata Check ===")
        if data.get('ai_ranking_metadata'):
            metadata = data['ai_ranking_metadata']
            print(f"📊 Total Stocks Ranked: {metadata.get('total_stocks_ranked', 'Unknown')}")
            print(f"🏆 Top Stock: {metadata.get('top_stocks', [{}])[0].get('symbol', 'Unknown') if metadata.get('top_stocks') else 'None'}")
            print(f"📈 Ranking Timestamp: {metadata.get('ranking_timestamp', 'Unknown')}")
        else:
            print("❌ No AI ranking metadata found")
        
        print("\n" + "=" * 50)
        print("🎉 Manual AI Ranking Trigger Test Complete!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ai_ranking_manual_trigger() 