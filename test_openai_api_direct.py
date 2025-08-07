#!/usr/bin/env python3
"""
Test OpenAI API Directly

This script tests the OpenAI API directly to see if it's working
and what scores it's returning.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.ai_ranking.openai_integration import OpenAIStockAnalyzer
from src.data_collection.data_manager import DataCollectionManager
import json

def test_openai_api_directly():
    """Test the OpenAI API directly."""
    print("🔍 Testing OpenAI API Directly...")
    
    # Initialize the analyzer
    analyzer = OpenAIStockAnalyzer()
    
    print(f"OpenAI available: {analyzer.is_available()}")
    print(f"Client available: {analyzer.client is not None}")
    
    if not analyzer.is_available():
        print("❌ OpenAI not available - check API key and package installation")
        return
    
    # Test with sample data
    symbol = "AAPL"
    technical_data = {
        'current_price': 150.0,
        'rsi': 65.0,
        'macd': 0.5,
        'macd_signal': 0.3,
        'sma_20': 148.0,
        'sma_50': 145.0,
        'volume': 50000000
    }
    
    market_context = {
        'market_regime': 'bullish',
        'volatility_level': 'moderate'
    }
    
    print(f"\n📊 Testing {symbol} with sample data:")
    print(f"   Technical data: {technical_data}")
    print(f"   Market context: {market_context}")
    
    try:
        # Test comprehensive analysis
        result = analyzer.analyze_stock_comprehensive(symbol, technical_data, market_context)
        
        print(f"\n✅ OpenAI Analysis Result:")
        print(f"   Score: {result.get('score', 'N/A')}")
        print(f"   Analysis: {result.get('analysis', 'N/A')[:200]}...")
        print(f"   Technical insights: {result.get('technical_insights', [])}")
        print(f"   Recommendation: {result.get('recommendation', 'N/A')}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error in OpenAI analysis: {e}")
        return None

def test_with_real_data():
    """Test with real stock data."""
    print("\n🔍 Testing with Real Stock Data...")
    
    # Initialize components
    data_manager = DataCollectionManager()
    analyzer = OpenAIStockAnalyzer()
    
    if not analyzer.is_available():
        print("❌ OpenAI not available")
        return
    
    collection_id = "ALL_20250803_160817"
    symbol = "AAPL"
    
    # Get real stock data
    stock_data = data_manager.get_symbol_indicators(collection_id, symbol)
    
    if stock_data is not None and not stock_data.empty:
        print(f"✅ Got real data for {symbol}: {len(stock_data)} rows")
        
        # Get latest data
        latest = stock_data.iloc[-1]
        
        # Prepare technical data
        technical_data = {
            'current_price': latest.get('close', 0),
            'rsi': latest.get('rsi_14', 50),
            'macd': latest.get('macd_line_12_26', 0),
            'macd_signal': latest.get('macd_signal_12_26_9', 0),
            'sma_20': latest.get('sma_20', 0),
            'sma_50': latest.get('sma_50', 0),
            'volume': latest.get('volume', 0)
        }
        
        market_context = {
            'market_regime': 'bullish',
            'volatility_level': 'moderate'
        }
        
        print(f"   Technical data: {technical_data}")
        
        try:
            # Test comprehensive analysis with real data
            result = analyzer.analyze_stock_comprehensive(symbol, technical_data, market_context)
            
            print(f"\n✅ Real Data Analysis Result:")
            print(f"   Score: {result.get('score', 'N/A')}")
            print(f"   Analysis: {result.get('analysis', 'N/A')[:200]}...")
            print(f"   Technical insights: {result.get('technical_insights', [])}")
            print(f"   Recommendation: {result.get('recommendation', 'N/A')}")
            
            return result
            
        except Exception as e:
            print(f"❌ Error in real data analysis: {e}")
            return None
    else:
        print(f"❌ No real data available for {symbol}")
        return None

def test_multiple_symbols():
    """Test multiple symbols to see score distribution."""
    print("\n🔍 Testing Multiple Symbols...")
    
    analyzer = OpenAIStockAnalyzer()
    data_manager = DataCollectionManager()
    
    if not analyzer.is_available():
        print("❌ OpenAI not available")
        return
    
    collection_id = "ALL_20250803_160817"
    test_symbols = ['AAPL', 'PFE', 'ABBV', 'KO', 'GILD']
    
    results = []
    
    for symbol in test_symbols:
        print(f"\n📊 Testing {symbol}...")
        
        stock_data = data_manager.get_symbol_indicators(collection_id, symbol)
        
        if stock_data is not None and not stock_data.empty:
            latest = stock_data.iloc[-1]
            
            technical_data = {
                'current_price': latest.get('close', 0),
                'rsi': latest.get('rsi_14', 50),
                'macd': latest.get('macd_line_12_26', 0),
                'macd_signal': latest.get('macd_signal_12_26_9', 0),
                'sma_20': latest.get('sma_20', 0),
                'sma_50': latest.get('sma_50', 0),
                'volume': latest.get('volume', 0)
            }
            
            market_context = {
                'market_regime': 'bullish',
                'volatility_level': 'moderate'
            }
            
            try:
                result = analyzer.analyze_stock_comprehensive(symbol, technical_data, market_context)
                score = result.get('score', 0)
                
                print(f"   Score: {score}")
                results.append({'symbol': symbol, 'score': score})
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                results.append({'symbol': symbol, 'score': 0})
        else:
            print(f"   ❌ No data available")
            results.append({'symbol': symbol, 'score': 0})
    
    print(f"\n📊 OpenAI Score Distribution:")
    for result in results:
        print(f"   {result['symbol']}: {result['score']}")
    
    unique_scores = set(r['score'] for r in results)
    print(f"   Unique scores: {sorted(unique_scores)}")
    
    return results

def main():
    """Run the OpenAI API tests."""
    print("🚀 OpenAI API Direct Testing")
    print("=" * 80)
    
    # Test with sample data
    test_openai_api_directly()
    
    # Test with real data
    test_with_real_data()
    
    # Test multiple symbols
    test_multiple_symbols()
    
    print("\n" + "=" * 80)
    print("✅ OpenAI API Direct Testing Completed!")

if __name__ == "__main__":
    main() 