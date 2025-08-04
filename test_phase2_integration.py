#!/usr/bin/env python3
"""
Test Phase 2: Technical Indicators Integration
Tests the integration of technical indicators with the data collection system.
"""

import sys
import os
import time
import requests
import json
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class Phase2IntegrationTest:
    def __init__(self):
        self.base_url = "http://localhost:8080"
        self.test_results = []
        
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def test_api_connection(self):
        """Test basic API connectivity."""
        try:
            response = requests.get(f"{self.base_url}/api/data-collection/exchanges")
            if response.status_code == 200:
                self.log("✅ API connection successful")
                return True
            else:
                self.log(f"❌ API connection failed: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ API connection error: {e}")
            return False
    
    def test_get_collections(self):
        """Test getting data collections."""
        try:
            response = requests.get(f"{self.base_url}/api/data-collection/collections")
            if response.status_code == 200:
                data = response.json()
                collections = data.get('collections', [])
                self.log(f"✅ Found {len(collections)} collections")
                return collections
            else:
                self.log(f"❌ Failed to get collections: {response.status_code}")
                return []
        except Exception as e:
            self.log(f"❌ Error getting collections: {e}")
            return []
    
    def test_calculate_indicators(self, collection_id):
        """Test calculating technical indicators for a collection."""
        try:
            self.log(f"🔄 Calculating indicators for collection {collection_id}...")
            response = requests.post(f"{self.base_url}/api/data-collection/collections/{collection_id}/indicators/calculate")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.log(f"✅ Indicators calculated successfully!")
                    self.log(f"   - Calculated: {result.get('calculated_count', 0)}/{result.get('total_symbols', 0)} symbols")
                    self.log(f"   - Coverage: {result.get('coverage', '0%')}")
                    if result.get('errors'):
                        self.log(f"   - Errors: {len(result.get('errors', []))}")
                    return True
                else:
                    self.log(f"❌ Indicator calculation failed: {result.get('error')}")
                    return False
            else:
                self.log(f"❌ Indicator calculation request failed: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error calculating indicators: {e}")
            return False
    
    def test_get_indicators_status(self, collection_id):
        """Test getting indicators status for a collection."""
        try:
            response = requests.get(f"{self.base_url}/api/data-collection/collections/{collection_id}/indicators/status")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    status = data.get('status', {})
                    self.log(f"✅ Indicators status retrieved:")
                    self.log(f"   - Total symbols: {status.get('total_symbols', 0)}")
                    self.log(f"   - Symbols with indicators: {status.get('symbols_with_indicators', 0)}")
                    self.log(f"   - Coverage: {status.get('indicators_coverage', '0%')}")
                    self.log(f"   - Latest calculation: {status.get('latest_calculation', 'Never')}")
                    return status
                else:
                    self.log(f"❌ Failed to get indicators status: {data.get('error')}")
                    return None
            else:
                self.log(f"❌ Indicators status request failed: {response.status_code}")
                return None
        except Exception as e:
            self.log(f"❌ Error getting indicators status: {e}")
            return None
    
    def test_get_symbol_indicators(self, collection_id, symbol):
        """Test getting indicators data for a specific symbol."""
        try:
            response = requests.get(f"{self.base_url}/api/data-collection/collections/{collection_id}/symbols/{symbol}/indicators")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    indicators_data = data.get('indicators_data', [])
                    columns = data.get('columns', [])
                    shape = data.get('shape', [0, 0])
                    
                    self.log(f"✅ Indicators data retrieved for {symbol}:")
                    self.log(f"   - Data points: {shape[0]}")
                    self.log(f"   - Columns: {len(columns)}")
                    
                    # Show available indicators
                    indicator_columns = [col for col in columns if any(indicator in col for indicator in ['SMA', 'EMA', 'RSI', 'MACD', 'Bollinger', 'ATR', 'OBV', 'VWAP'])]
                    self.log(f"   - Available indicators: {len(indicator_columns)}")
                    
                    if indicators_data:
                        latest = indicators_data[-1]
                        self.log(f"   - Latest data point: {len(latest)} fields")
                        
                        # Show some sample indicator values
                        sample_indicators = {}
                        for col in indicator_columns[:5]:  # Show first 5 indicators
                            if col in latest and latest[col] is not None:
                                sample_indicators[col] = latest[col]
                        
                        if sample_indicators:
                            self.log(f"   - Sample values: {sample_indicators}")
                    
                    return True
                else:
                    self.log(f"❌ Failed to get indicators for {symbol}: {data.get('error')}")
                    return False
            else:
                self.log(f"❌ Indicators request failed for {symbol}: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error getting indicators for {symbol}: {e}")
            return False
    
    def test_get_data_with_indicators(self, collection_id, symbol):
        """Test getting combined data with indicators."""
        try:
            response = requests.get(f"{self.base_url}/api/data-collection/collections/{collection_id}/symbols/{symbol}/data-with-indicators")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    combined_data = data.get('data', [])
                    columns = data.get('columns', [])
                    indicators_available = data.get('indicators_available', False)
                    
                    self.log(f"✅ Combined data retrieved for {symbol}:")
                    self.log(f"   - Data points: {len(combined_data)}")
                    self.log(f"   - Total columns: {len(columns)}")
                    self.log(f"   - Indicators available: {indicators_available}")
                    
                    if combined_data:
                        latest = combined_data[-1]
                        # Count indicator columns
                        indicator_count = sum(1 for col in columns if any(indicator in col for indicator in ['SMA', 'EMA', 'RSI', 'MACD', 'Bollinger', 'ATR', 'OBV', 'VWAP']))
                        self.log(f"   - Indicator columns: {indicator_count}")
                        
                        # Show OHLCV + indicators structure
                        ohlcv_cols = [col for col in columns if col in ['Open', 'High', 'Low', 'Close', 'Volume']]
                        self.log(f"   - OHLCV columns: {ohlcv_cols}")
                    
                    return True
                else:
                    self.log(f"❌ Failed to get combined data for {symbol}: {data.get('error')}")
                    return False
            else:
                self.log(f"❌ Combined data request failed for {symbol}: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error getting combined data for {symbol}: {e}")
            return False
    
    def test_symbols_with_indicators(self, collection_id):
        """Test getting symbols that have indicators available."""
        try:
            # First get all symbols
            response = requests.get(f"{self.base_url}/api/data-collection/collections/{collection_id}/symbols")
            
            if response.status_code == 200:
                data = response.json()
                symbols = data.get('symbols', [])
                
                self.log(f"🔄 Testing indicators for {len(symbols)} symbols...")
                
                symbols_with_indicators = []
                for symbol in symbols[:5]:  # Test first 5 symbols
                    if self.test_get_symbol_indicators(collection_id, symbol):
                        symbols_with_indicators.append(symbol)
                
                self.log(f"✅ Found {len(symbols_with_indicators)} symbols with indicators")
                return symbols_with_indicators
            else:
                self.log(f"❌ Failed to get symbols: {response.status_code}")
                return []
        except Exception as e:
            self.log(f"❌ Error testing symbols with indicators: {e}")
            return []
    
    def run_full_test(self):
        """Run the complete Phase 2 integration test."""
        self.log("🚀 Starting Phase 2 Technical Indicators Integration Test")
        self.log("=" * 60)
        
        # Test 1: API Connection
        if not self.test_api_connection():
            self.log("❌ Cannot proceed without API connection")
            return False
        
        # Test 2: Get Collections
        collections = self.test_get_collections()
        if not collections:
            self.log("❌ No collections available for testing")
            return False
        
        # Use the first collection for testing
        test_collection = collections[0]
        collection_id = test_collection['collection_id']
        self.log(f"📊 Using collection: {collection_id}")
        
        # Test 3: Calculate Indicators
        if self.test_calculate_indicators(collection_id):
            # Wait a moment for calculation to complete
            time.sleep(2)
            
            # Test 4: Get Indicators Status
            status = self.test_get_indicators_status(collection_id)
            
            # Test 5: Test Symbol Indicators
            symbols_with_indicators = self.test_symbols_with_indicators(collection_id)
            
            if symbols_with_indicators:
                # Test 6: Test Combined Data
                test_symbol = symbols_with_indicators[0]
                self.test_get_data_with_indicators(collection_id, test_symbol)
        
        self.log("=" * 60)
        self.log("✅ Phase 2 Integration Test Completed!")
        return True

def main():
    """Main test function."""
    test = Phase2IntegrationTest()
    test.run_full_test()

if __name__ == "__main__":
    main() 