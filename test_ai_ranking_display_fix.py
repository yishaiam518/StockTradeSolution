#!/usr/bin/env python3
"""
Test script to verify the AI ranking display fix
"""

import requests
import json
from datetime import datetime

def test_ai_ranking_display_fix():
    """Test the AI ranking display fix"""
    
    collection_id = "ALL_20250803_160817"
    base_url = "http://localhost:8080"
    
    print("🤖 Testing AI Ranking Display Fix")
    print("=" * 50)
    
    try:
        # Test 1: Check API response
        print("=== TEST 1: API Response ===")
        response = requests.get(f"{base_url}/api/data-collection/collections/{collection_id}/scheduler/status")
        data = response.json()
        
        print(f"✅ Success: {data.get('success')}")
        print(f"📅 AI Ranking Last Update: {data.get('ai_ranking_last_update_formatted', 'Not found')}")
        print(f"🔧 AI Ranking Raw: {data.get('ai_ranking_last_update', 'Not found')}")
        print(f"📊 AI Ranking Integrated: {data.get('ai_ranking_integrated', False)}")
        
        if data.get('ai_ranking_metadata'):
            metadata = data['ai_ranking_metadata']
            print(f"📈 Total Stocks Ranked: {metadata.get('total_stocks_ranked', 'Unknown')}")
            print(f"🏆 Top Stock: {metadata.get('top_stocks', [{}])[0].get('symbol', 'Unknown') if metadata.get('top_stocks') else 'None'}")
        
        # Test 2: Check if the timestamp is recent
        print("\n=== TEST 2: Timestamp Analysis ===")
        ai_update_time = data.get('ai_ranking_last_update')
        if ai_update_time:
            try:
                update_datetime = datetime.fromisoformat(ai_update_time.replace('Z', '+00:00'))
                now = datetime.now()
                time_diff = (now - update_datetime).total_seconds()
                
                print(f"⏰ Update Time: {update_datetime}")
                print(f"⏰ Current Time: {now}")
                print(f"⏱️  Time Difference: {time_diff:.1f} seconds")
                
                if time_diff < 300:  # Less than 5 minutes
                    print("✅ AI ranking is recent (within 5 minutes)")
                else:
                    print("⚠️  AI ranking is older than 5 minutes")
            except Exception as e:
                print(f"❌ Error parsing timestamp: {e}")
        else:
            print("❌ No AI ranking timestamp found")
        
        # Test 3: Check frontend accessibility
        print("\n=== TEST 3: Frontend Accessibility ===")
        try:
            response = requests.get(f"{base_url}/data-collection")
            if response.status_code == 200:
                print("✅ Data collection page is accessible")
                
                # Check if the page contains the expected JavaScript
                content = response.text
                if "ai-ranking-last-update" in content:
                    print("✅ AI ranking element ID found in page")
                else:
                    print("❌ AI ranking element ID not found in page")
                
                if "loadCollectionSchedulerStatus" in content:
                    print("✅ Scheduler status function found in page")
                else:
                    print("❌ Scheduler status function not found in page")
            else:
                print(f"❌ Data collection page returned status {response.status_code}")
        except Exception as e:
            print(f"❌ Error accessing frontend: {e}")
        
        # Test 4: Check collections API
        print("\n=== TEST 4: Collections API ===")
        try:
            response = requests.get(f"{base_url}/api/data-collection/collections")
            data = response.json()
            
            if data.get('success'):
                collections = data.get('collections', [])
                print(f"✅ Found {len(collections)} collections")
                
                # Check if our collection is in the list
                target_collection = None
                for collection in collections:
                    if collection.get('collection_id') == collection_id:
                        target_collection = collection
                        break
                
                if target_collection:
                    print(f"✅ Target collection found: {target_collection.get('exchange')}")
                    print(f"📅 Collection AI Ranking: {target_collection.get('ai_ranking_last_update', 'Not set')}")
                else:
                    print("❌ Target collection not found in list")
            else:
                print("❌ Collections API returned error")
        except Exception as e:
            print(f"❌ Error accessing collections API: {e}")
        
        print("\n" + "=" * 50)
        print("🎉 AI Ranking Display Fix Test Complete!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ai_ranking_display_fix() 