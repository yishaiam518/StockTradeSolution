#!/usr/bin/env python3
"""
Test script to debug AI ranking modal loading issue
"""

import requests
import json
import time

def test_ai_ranking_debug():
    """Test the AI ranking modal loading with detailed debugging"""
    
    base_url = "http://localhost:8080"
    
    print("🔍 Testing AI Ranking Modal Debug")
    print("=" * 50)
    
    # Test 1: Check if the API is working
    print("\n📊 Test 1: AI Ranking API Response")
    print("-" * 30)
    
    try:
        response = requests.get(f"{base_url}/api/ai-ranking/collection/ALL_20250803_160817/hybrid-rank?max_stocks=5")
        if response.status_code == 200:
            data = response.json()
            print("✅ API Response received")
            print(f"   - Success: {data.get('success')}")
            print(f"   - Dual scores count: {len(data.get('dual_scores', []))}")
            print(f"   - Collection ID: {data.get('collection_id')}")
            
            if data.get('dual_scores'):
                first_score = data['dual_scores'][0]
                print(f"   - First score: {first_score.get('symbol')} - OpenAI: {first_score.get('openai_score')}, Local: {first_score.get('local_score')}")
        else:
            print(f"❌ API failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")
    
    # Test 2: Check if the modal HTML elements exist
    print("\n📊 Test 2: Modal HTML Elements")
    print("-" * 30)
    
    try:
        response = requests.get(f"{base_url}/data-collection")
        if response.status_code == 200:
            content = response.text
            
            # Check for modal elements
            elements_to_check = [
                'hybridAIRankingModal',
                'hybrid-ai-ranking-loading',
                'hybrid-ai-ranking-content',
                'hybrid-ranking-table',
                'portfolio-summary'
            ]
            
            for element in elements_to_check:
                if element in content:
                    print(f"✅ {element} found in HTML")
                else:
                    print(f"❌ {element} NOT found in HTML")
                    
        else:
            print(f"❌ Failed to load page: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error checking HTML elements: {e}")
    
    # Test 3: Check JavaScript functions
    print("\n📊 Test 3: JavaScript Functions")
    print("-" * 30)
    
    try:
        response = requests.get(f"{base_url}/static/js/data_collection.js")
        if response.status_code == 200:
            content = response.text
            
            functions_to_check = [
                'loadAIRankingData',
                'displayHybridAIRankingResults',
                'initializeAIRankingGrid',
                'createFallbackTable'
            ]
            
            for func in functions_to_check:
                if func in content:
                    print(f"✅ {func} found in JavaScript")
                else:
                    print(f"❌ {func} NOT found in JavaScript")
                    
        else:
            print(f"❌ Failed to load JavaScript: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error checking JavaScript: {e}")
    
    print("\n🎯 Debug Summary")
    print("=" * 50)
    print("If all elements are found but modal still doesn't work:")
    print("1. Check browser console for JavaScript errors")
    print("2. Verify that the modal is being opened correctly")
    print("3. Check if the data is being processed correctly")
    print("4. Ensure the loading element is being hidden properly")

if __name__ == "__main__":
    test_ai_ranking_debug() 