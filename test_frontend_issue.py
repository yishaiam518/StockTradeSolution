#!/usr/bin/env python3
"""
Test script to verify the frontend issue with AI ranking display
"""

import requests
import json
from datetime import datetime

def test_frontend_issue():
    """Test the frontend issue with AI ranking display"""
    
    collection_id = "ALL_20250803_160817"
    base_url = "http://localhost:8080"
    
    try:
        # Test 1: Check API response
        print("=== TEST 1: API Response ===")
        response = requests.get(f"{base_url}/api/data-collection/collections/{collection_id}/scheduler/status")
        data = response.json()
        
        print(f"Success: {data.get('success')}")
        print(f"AI Ranking Last Update: {data.get('ai_ranking_last_update_formatted', 'Not found')}")
        print(f"AI Ranking Raw: {data.get('ai_ranking_last_update', 'Not found')}")
        
        # Test 2: Check if the element ID would be correct
        print("\n=== TEST 2: Element ID Check ===")
        element_id = f"ai-ranking-last-update-{collection_id}"
        print(f"Expected element ID: {element_id}")
        
        # Test 3: Check the actual HTML structure
        print("\n=== TEST 3: HTML Structure Check ===")
        response = requests.get(f"{base_url}/data-collection")
        html_content = response.text
        
        # Look for the AI ranking element
        if element_id in html_content:
            print(f"✅ Element ID '{element_id}' found in HTML")
        else:
            print(f"❌ Element ID '{element_id}' NOT found in HTML")
            
        # Look for AI ranking content
        if "AI Ranking: Never" in html_content:
            print("✅ 'AI Ranking: Never' found in HTML")
        else:
            print("❌ 'AI Ranking: Never' NOT found in HTML")
            
        if "ai-ranking-last-update" in html_content:
            print("✅ 'ai-ranking-last-update' found in HTML")
        else:
            print("❌ 'ai-ranking-last-update' NOT found in HTML")
        
        # Test 4: Check if the issue is with the API data
        print("\n=== TEST 4: API Data Analysis ===")
        if data.get('success'):
            ai_update_time = data.get('ai_ranking_last_update_formatted') or data.get('ai_ranking_last_update')
            if ai_update_time:
                print(f"✅ API has AI ranking update time: {ai_update_time}")
                try:
                    parsed_time = datetime.fromisoformat(ai_update_time.replace('Z', '+00:00'))
                    print(f"✅ Time can be parsed: {parsed_time}")
                except Exception as e:
                    print(f"❌ Time parsing error: {e}")
            else:
                print("❌ API does not have AI ranking update time")
        else:
            print("❌ API request failed")
            
        return True
        
    except Exception as e:
        print(f"Error testing frontend issue: {e}")
        return False

if __name__ == "__main__":
    test_frontend_issue() 