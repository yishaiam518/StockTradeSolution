#!/usr/bin/env python3
"""
Debug Technical Data

This script checks what technical data is available
for the scoring algorithm.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json
from datetime import datetime

def check_technical_data_for_symbol(symbol):
    """Check what technical data is available for a specific symbol."""
    base_url = "http://localhost:8080"
    collection_id = "ALL_20250803_160817"
    
    print(f"🔍 Checking technical data for {symbol}...")
    
    try:
        # Get the stock data
        response = requests.get(f"{base_url}/api/data-collection/collections/{collection_id}/symbols/{symbol}/indicators", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('indicators'):
                indicators = data['indicators']
                
                print(f"📊 Technical Data for {symbol}:")
                print(f"   Data points: {len(indicators)}")
                
                if len(indicators) > 0:
                    latest = indicators[-1]
                    print(f"   Latest data point:")
                    print(f"     Close: {latest.get('Close', 'N/A')}")
                    print(f"     RSI: {latest.get('rsi', 'N/A')}")
                    print(f"     MACD: {latest.get('macd', 'N/A')}")
                    print(f"     MACD Signal: {latest.get('macd_signal', 'N/A')}")
                    print(f"     SMA 20: {latest.get('sma_20', 'N/A')}")
                    print(f"     SMA 50: {latest.get('sma_50', 'N/A')}")
                    
                    # Check if data is meaningful
                    rsi = latest.get('rsi')
                    macd = latest.get('macd')
                    macd_signal = latest.get('macd_signal')
                    sma_20 = latest.get('sma_20')
                    sma_50 = latest.get('sma_50')
                    
                    if rsi is not None and macd is not None and sma_20 is not None:
                        print(f"   ✅ Technical indicators available")
                    else:
                        print(f"   ❌ Missing technical indicators")
                        
                else:
                    print(f"   ❌ No indicator data available")
            else:
                print(f"   ❌ No indicators data in response")
        else:
            print(f"   ❌ API request failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

def test_scoring_with_real_data():
    """Test the scoring algorithm with real technical data."""
    print("\n🔍 Testing Scoring with Real Data...")
    
    # Test with a few symbols
    symbols = ['AAPL', 'TSLA', 'NVDA', 'MSFT', 'GOOGL']
    
    for symbol in symbols:
        check_technical_data_for_symbol(symbol)
        print()

def main():
    """Run the technical data debug analysis."""
    print("🚀 Technical Data Debug Analysis")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check technical data for symbols
    test_scoring_with_real_data()
    
    print("=" * 60)
    print("✅ Technical Data Debug Analysis Completed!")

if __name__ == "__main__":
    main() 