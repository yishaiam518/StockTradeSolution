#!/usr/bin/env python3
"""
Test script to verify stock viewer fixes
"""

import requests
import json
import time

def test_stock_viewer_fixes():
    """Test the stock viewer fixes"""
    base_url = "http://localhost:8080"
    
    print("🧪 Testing Stock Viewer Fixes")
    print("=" * 50)
    
    # Test 1: Check if dashboard is running
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✅ Dashboard is running")
        else:
            print(f"❌ Dashboard returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to dashboard: {e}")
        return False
    
    # Test 2: Get available collections
    try:
        response = requests.get(f"{base_url}/api/data-collection/collections")
        if response.status_code == 200:
            data = response.json()
            collections = data.get('collections', [])
            print(f"✅ Found {len(collections)} collections")
            
            if collections:
                # Use the first collection
                collection_id = collections[0]['collection_id']
                print(f"📊 Using collection: {collection_id}")
                
                # Test 3: Get symbols for this collection
                response = requests.get(f"{base_url}/api/data-collection/collections/{collection_id}/symbols")
                if response.status_code == 200:
                    symbols_data = response.json()
                    if symbols_data.get('success') and symbols_data.get('symbols'):
                        symbols = symbols_data['symbols']
                        print(f"✅ Found {len(symbols)} symbols")
                        
                        # Test 4: Get data for first symbol
                        if symbols:
                            symbol = symbols[0]
                            print(f"📈 Testing symbol: {symbol}")
                            
                            # Test with indicators endpoint
                            response = requests.get(f"{base_url}/api/data-collection/collections/{collection_id}/symbols/{symbol}/data-with-indicators")
                            if response.status_code == 200:
                                data = response.json()
                                if data.get('success'):
                                    print(f"✅ Data with indicators endpoint works")
                                    print(f"   - Data points: {len(data.get('data', []))}")
                                    print(f"   - Columns: {len(data.get('columns', []))}")
                                    print(f"   - Indicators available: {data.get('indicators_available', False)}")
                                else:
                                    print(f"❌ Data with indicators endpoint failed: {data.get('error', 'Unknown error')}")
                            else:
                                print(f"❌ Data with indicators endpoint returned status {response.status_code}")
                            
                            # Test with regular endpoint
                            response = requests.get(f"{base_url}/api/data-collection/collections/{collection_id}/symbols/{symbol}")
                            if response.status_code == 200:
                                data = response.json()
                                if data.get('success'):
                                    print(f"✅ Regular data endpoint works")
                                    print(f"   - Stock data points: {len(data.get('stock_data', []))}")
                                else:
                                    print(f"❌ Regular data endpoint failed: {data.get('error', 'Unknown error')}")
                            else:
                                print(f"❌ Regular data endpoint returned status {response.status_code}")
                        else:
                            print("❌ No symbols found in collection")
                    else:
                        print(f"❌ Failed to get symbols: {symbols_data}")
                else:
                    print(f"❌ Failed to get symbols, status: {response.status_code}")
            else:
                print("❌ No collections found")
        else:
            print(f"❌ Failed to get collections, status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing collections: {e}")
        return False
    
    print("\n🎉 Stock Viewer Fixes Test Complete!")
    return True

if __name__ == "__main__":
    test_stock_viewer_fixes() 