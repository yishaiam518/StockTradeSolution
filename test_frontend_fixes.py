#!/usr/bin/env python3
"""
Test Frontend Fixes

Tests the frontend functionality to identify and fix the remaining issues.
"""

import sys
import os
import requests
import json

def test_frontend_functionality():
    """Test frontend functionality."""
    print("🧪 Testing Frontend Functionality")
    print("=" * 50)
    
    base_url = "http://localhost:8080"
    
    # Test 1: Check if data collection page loads
    print("\n📊 Test 1: Data Collection Page")
    print("-" * 30)
    
    try:
        response = requests.get(f"{base_url}/data-collection")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            print(f"✅ Page loads successfully")
            
            # Check for portfolio buttons
            if "Portfolio Management" in content:
                print("✅ Portfolio Management buttons found")
            else:
                print("❌ Portfolio Management buttons NOT found")
                
            # Check for AI ranking modal
            if "hybridAIRankingModal" in content:
                print("✅ AI Ranking modal found")
            else:
                print("❌ AI Ranking modal NOT found")
                
            # Check for stock analysis modal
            if "stockAnalysisModal" in content:
                print("✅ Stock Analysis modal found")
            else:
                print("❌ Stock Analysis modal NOT found")
                
        else:
            print(f"❌ Failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Check portfolio API
    print("\n📊 Test 2: Portfolio API")
    print("-" * 30)
    
    try:
        response = requests.get(f"{base_url}/api/portfolios")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Portfolio API working - {len(data.get('portfolios', []))} portfolios")
        else:
            print(f"❌ Portfolio API failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Check if we can buy a stock
    print("\n📊 Test 3: Buy Stock API")
    print("-" * 30)
    
    try:
        buy_data = {
            "symbol": "MSFT",
            "shares": 5,
            "notes": "Test buy from frontend test"
        }
        
        response = requests.post(
            f"{base_url}/api/portfolios/1/buy",
            json=buy_data,
            headers={'Content-Type': 'application/json'}
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Buy stock API working - {data.get('message', 'Success')}")
        else:
            print(f"❌ Buy stock API failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Check JavaScript functions
    print("\n📊 Test 4: JavaScript Functions")
    print("-" * 30)
    
    try:
        response = requests.get(f"{base_url}/static/js/data_collection.js")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            
            # Check for portfolio functions
            functions_to_check = [
                "buyStock",
                "sellStock", 
                "buyStockFromAnalysis",
                "sellStockFromAnalysis",
                "executeTrade",
                "cancelTrade",
                "openUserPortfolioModal",
                "openAIPortfolioModal"
            ]
            
            for func in functions_to_check:
                if func in content:
                    print(f"✅ {func} function found")
                else:
                    print(f"❌ {func} function NOT found")
        else:
            print(f"❌ JavaScript file failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_frontend_functionality() 