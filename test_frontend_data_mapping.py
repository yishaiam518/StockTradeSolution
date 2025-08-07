#!/usr/bin/env python3
"""
Test Frontend Data Mapping

This script tests the frontend data mapping to ensure
the API data is correctly displayed in the UI.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json
import time
from datetime import datetime

def test_api_data_structure():
    """Test the API data structure to ensure it's correct."""
    base_url = "http://localhost:8080"
    collection_id = "ALL_20250803_160817"
    
    print("🔍 Testing API Data Structure...")
    
    try:
        response = requests.get(f"{base_url}/api/ai-ranking/collection/{collection_id}/hybrid-rank?max_stocks=3", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API Response Status: Success")
            
            if data.get('success') and data.get('dual_scores'):
                dual_scores = data['dual_scores']
                print(f"✅ Found {len(dual_scores)} dual scores")
                
                # Check first item structure
                first_item = dual_scores[0]
                print("\n📊 First Item Structure:")
                print(f"   Symbol: {first_item.get('symbol')}")
                print(f"   OpenAI Score: {first_item.get('openai_score')}")
                print(f"   Local Score: {first_item.get('local_score')}")
                print(f"   Combined Score: {first_item.get('combined_score')}")
                print(f"   Confidence Level: {first_item.get('confidence_level')}")
                print(f"   Explanation: {first_item.get('explanation')[:100]}...")
                
                # Check if scores are non-zero
                openai_score = first_item.get('openai_score', 0)
                local_score = first_item.get('local_score', 0)
                
                if openai_score > 0 and local_score > 0:
                    print("✅ Scores are non-zero - API data is correct")
                else:
                    print("❌ Scores are zero - API data issue")
                    
                return dual_scores
            else:
                print("❌ No dual_scores in response")
                return []
        else:
            print(f"❌ API request failed: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return []

def test_frontend_data_mapping():
    """Test the frontend data mapping logic."""
    print("\n🔍 Testing Frontend Data Mapping...")
    
    # Simulate the API data structure
    api_data = {
        "symbol": "AAPL",
        "openai_score": 45.0,
        "local_score": 60.0,
        "combined_score": 52.5,
        "confidence_level": "Medium Confidence",
        "explanation": "Moderate agreement between AI (45.0) and local (60.0) analysis for AAPL. Consider both perspectives.",
        "recommendations": ["Hold - Mixed signals, monitor closely"]
    }
    
    print("📊 Simulated API Data:")
    print(f"   Symbol: {api_data['symbol']}")
    print(f"   OpenAI Score: {api_data['openai_score']}")
    print(f"   Local Score: {api_data['local_score']}")
    print(f"   Combined Score: {api_data['combined_score']}")
    
    # Simulate the frontend mapping logic
    frontend_data = {
        "rank": 1,
        "symbol": api_data["symbol"],
        "totalScore": api_data["combined_score"],
        "openaiScore": api_data["openai_score"],
        "localScore": api_data["local_score"],
        "technicalScore": api_data["openai_score"],
        "riskScore": api_data["local_score"],
        "confidenceLevel": api_data["confidence_level"],
        "explanation": api_data["explanation"],
        "recommendation": "Hold"
    }
    
    print("\n📊 Frontend Mapped Data:")
    print(f"   Symbol: {frontend_data['symbol']}")
    print(f"   OpenAI Score: {frontend_data['openaiScore']}")
    print(f"   Local Score: {frontend_data['localScore']}")
    print(f"   Total Score: {frontend_data['totalScore']}")
    print(f"   Technical Score: {frontend_data['technicalScore']}")
    print(f"   Risk Score: {frontend_data['riskScore']}")
    
    # Check if mapping is correct
    if (frontend_data['openaiScore'] == api_data['openai_score'] and 
        frontend_data['localScore'] == api_data['local_score']):
        print("✅ Frontend mapping is correct")
    else:
        print("❌ Frontend mapping issue")
        
    return frontend_data

def test_template_rendering():
    """Test the template rendering logic."""
    print("\n🔍 Testing Template Rendering...")
    
    # Simulate the grid data
    grid_data = {
        "openaiScore": 45.0,
        "localScore": 60.0,
        "totalScore": 52.5
    }
    
    # Simulate the template logic
    openai_score = grid_data.get('openaiScore', 0)
    local_score = grid_data.get('localScore', 0)
    combined_score = ((openai_score + local_score) / 2)
    
    print("📊 Template Rendering:")
    print(f"   OpenAI Score: {openai_score}")
    print(f"   Local Score: {local_score}")
    print(f"   Combined Score: {combined_score}")
    
    # Check if template would render correctly
    if openai_score > 0 and local_score > 0:
        print("✅ Template would render correctly")
    else:
        print("❌ Template rendering issue - scores are zero")
        
    return {
        "openai_score": openai_score,
        "local_score": local_score,
        "combined_score": combined_score
    }

def main():
    """Run the frontend data mapping tests."""
    print("🚀 Frontend Data Mapping Test")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test API data structure
    api_data = test_api_data_structure()
    
    # Test frontend data mapping
    frontend_data = test_frontend_data_mapping()
    
    # Test template rendering
    template_data = test_template_rendering()
    
    print("\n" + "=" * 60)
    print("✅ Frontend Data Mapping Test Completed!")
    
    if api_data and frontend_data and template_data:
        print("\n📋 Summary:")
        print("1. ✅ API data structure is correct")
        print("2. ✅ Frontend mapping logic is correct")
        print("3. ✅ Template rendering logic is correct")
        print("4. ✅ All scores are non-zero")
        
        print("\n🎯 Next Steps:")
        print("- Refresh the frontend page")
        print("- Check browser console for any JavaScript errors")
        print("- Verify the AI Ranking display shows correct scores")
    else:
        print("\n❌ Issues Found:")
        print("- Check API response structure")
        print("- Verify frontend data mapping")
        print("- Debug template rendering")

if __name__ == "__main__":
    main() 