#!/usr/bin/env python3
"""
Test Portfolio API

Tests the portfolio API endpoints to ensure they're working correctly.
"""

import sys
import os
import requests
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_portfolio_api():
    """Test portfolio API endpoints."""
    print("🧪 Testing Portfolio API")
    print("=" * 50)
    
    base_url = "http://localhost:8080"
    
    # Test 1: Get all portfolios
    print("\n📊 Test 1: Getting all portfolios")
    print("-" * 30)
    
    try:
        response = requests.get(f"{base_url}/api/portfolios")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {len(data.get('portfolios', []))} portfolios")
        else:
            print(f"❌ Failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Get specific portfolio
    print("\n📊 Test 2: Getting portfolio 1")
    print("-" * 30)
    
    try:
        response = requests.get(f"{base_url}/api/portfolios/1")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Portfolio: {data.get('portfolio', {}).get('name', 'Unknown')}")
        else:
            print(f"❌ Failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Buy stock
    print("\n📊 Test 3: Buying stock")
    print("-" * 30)
    
    try:
        buy_data = {
            "symbol": "AAPL",
            "shares": 10,
            "notes": "Test buy from API"
        }
        
        response = requests.post(
            f"{base_url}/api/portfolios/1/buy",
            json=buy_data,
            headers={'Content-Type': 'application/json'}
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! {data.get('message', 'Stock bought')}")
        else:
            print(f"❌ Failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Check available routes
    print("\n📊 Test 4: Checking available routes")
    print("-" * 30)
    
    try:
        response = requests.get(f"{base_url}/")
        print(f"Root endpoint: {response.status_code}")
        
        response = requests.get(f"{base_url}/data-collection")
        print(f"Data collection: {response.status_code}")
        
        response = requests.get(f"{base_url}/api/data-collection/collections")
        print(f"Data collections API: {response.status_code}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_portfolio_api() 