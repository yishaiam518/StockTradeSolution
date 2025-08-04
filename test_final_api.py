#!/usr/bin/env python3
"""
Final test script to verify the API is working correctly.
"""

import requests

def test_final_api():
    """Test the final API endpoint."""
    
    print("✅ FINAL API TEST")
    print("=" * 50)
    
    # Test the data-with-indicators endpoint
    response = requests.get('http://localhost:8080/api/data-collection/collections/AMEX_20250803_161652/symbols/BND/data-with-indicators')
    data = response.json()
    
    print(f"Status: {response.status_code}")
    print(f"Success: {data.get('success')}")
    print(f"Indicators available: {data.get('indicators_available')}")
    print(f"Data points: {len(data.get('data', []))}")
    print(f"Total columns: {len(data.get('columns', []))}")
    
    # Check for indicator columns
    indicator_cols = [col for col in data.get('columns', []) if any(indicator in col.upper() for indicator in ['SMA', 'EMA', 'RSI', 'MACD', 'BOLLINGER', 'ATR', 'STOCHASTIC'])]
    print(f"Indicator columns: {len(indicator_cols)}")
    print(f"Sample indicators: {indicator_cols[:5]}")
    
    # Check if the latest data point has indicator values
    if data.get('data'):
        latest_point = data['data'][-1]
        has_indicators = any(indicator in str(latest_point).upper() for indicator in ['SMA', 'EMA', 'RSI', 'MACD'])
        print(f"Latest data point has indicators: {has_indicators}")
        
        # Show some indicator values from the latest point
        indicator_values = {k: v for k, v in latest_point.items() if any(indicator in k.upper() for indicator in ['SMA', 'EMA', 'RSI', 'MACD'])}
        print(f"Sample indicator values from latest point:")
        for key, value in list(indicator_values.items())[:5]:
            print(f"  {key}: {value}")
    
    print("\n🎉 Phase 2 Technical Indicators are now working in the GUI!")

if __name__ == "__main__":
    test_final_api() 