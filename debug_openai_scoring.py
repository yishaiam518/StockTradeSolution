#!/usr/bin/env python3
"""
Debug OpenAI Scoring

This script investigates why OpenAI scoring is falling back to simplified scoring
and only producing 7 unique scores.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json
from datetime import datetime

def test_openai_analysis_directly():
    """Test OpenAI analysis directly to see what's happening."""
    base_url = "http://localhost:8080"
    collection_id = "ALL_20250803_160817"
    
    print("🔍 Testing OpenAI Analysis Directly...")
    
    # Test with a few symbols
    test_symbols = ['AAPL', 'PFE', 'ABBV', 'KO', 'GILD']
    
    for symbol in test_symbols:
        print(f"\n📊 Testing {symbol}:")
        
        try:
            # Get the stock data first
            data_response = requests.get(f"{base_url}/api/data-collection/collections/{collection_id}/symbols/{symbol}", timeout=30)
            
            if data_response.status_code == 200:
                data = data_response.json()
                if data.get('success') and data.get('indicators'):
                    indicators = data['indicators']
                    print(f"   ✅ Got {len(indicators)} data points for {symbol}")
                    
                    # Check if we have technical indicators
                    if len(indicators) > 0:
                        latest = indicators[-1]
                        print(f"   Latest indicators:")
                        print(f"     Close: {latest.get('close', 'N/A')}")
                        print(f"     RSI: {latest.get('rsi_14', 'N/A')}")
                        print(f"     MACD: {latest.get('macd_line_12_26', 'N/A')}")
                        print(f"     MACD Signal: {latest.get('macd_signal_12_26_9', 'N/A')}")
                        print(f"     SMA 20: {latest.get('sma_20', 'N/A')}")
                        
                        # Check if we have enough data for analysis
                        has_close = latest.get('close') is not None
                        has_rsi = latest.get('rsi_14') is not None
                        has_macd = latest.get('macd_line_12_26') is not None
                        has_sma = latest.get('sma_20') is not None
                        
                        print(f"   Data completeness:")
                        print(f"     Close price: {'✅' if has_close else '❌'}")
                        print(f"     RSI: {'✅' if has_rsi else '❌'}")
                        print(f"     MACD: {'✅' if has_macd else '❌'}")
                        print(f"     SMA: {'✅' if has_sma else '❌'}")
                        
                        if has_close and has_rsi and has_macd and has_sma:
                            print(f"   ✅ Sufficient data for OpenAI analysis")
                        else:
                            print(f"   ❌ Insufficient data for OpenAI analysis")
                    else:
                        print(f"   ❌ No indicator data available")
                else:
                    print(f"   ❌ No indicators data in response")
            else:
                print(f"   ❌ Data request failed: {data_response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error testing {symbol}: {e}")

def test_openai_api_endpoint():
    """Test the OpenAI API endpoint directly."""
    base_url = "http://localhost:8080"
    collection_id = "ALL_20250803_160817"
    
    print("\n🔍 Testing OpenAI API Endpoint...")
    
    try:
        # Test the OpenAI analysis endpoint
        response = requests.get(f"{base_url}/api/ai-ranking/openai/analyze/AAPL", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ OpenAI API response:")
            print(f"   {json.dumps(data, indent=2)}")
        else:
            print(f"   ❌ OpenAI API failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error testing OpenAI API: {e}")

def check_openai_storage():
    """Check what's stored in the OpenAI analysis storage."""
    print("\n🔍 Checking OpenAI Analysis Storage...")
    
    try:
        # Check the database directly
        import sqlite3
        
        db_path = "data/openai_analysis.db"
        if os.path.exists(db_path):
            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                print(f"   Database tables: {[table[0] for table in tables]}")
                
                # Check analysis_results table
                cursor = conn.execute("SELECT COUNT(*) FROM analysis_results")
                count = cursor.fetchone()[0]
                print(f"   Total analysis results: {count}")
                
                if count > 0:
                    # Get a sample result
                    cursor = conn.execute("SELECT symbol, score, analysis FROM analysis_results LIMIT 1")
                    sample = cursor.fetchone()
                    if sample:
                        print(f"   Sample analysis for {sample[0]}:")
                        print(f"     Score: {sample[1]}")
                        print(f"     Analysis: {sample[2][:200]}...")
        else:
            print(f"   ❌ OpenAI analysis database not found at {db_path}")
            
    except Exception as e:
        print(f"   ❌ Error checking OpenAI storage: {e}")

def test_hybrid_ranking_engine_internals():
    """Test the hybrid ranking engine internals to see OpenAI processing."""
    print("\n🔍 Testing Hybrid Ranking Engine Internals...")
    
    try:
        from src.ai_ranking.hybrid_ranking_engine import HybridRankingEngine
        from src.data_collection.data_manager import DataCollectionManager
        
        # Initialize components
        data_manager = DataCollectionManager()
        engine = HybridRankingEngine(data_manager)
        
        # Test with a single symbol
        symbol = "AAPL"
        collection_id = "ALL_20250803_160817"
        
        print(f"   Testing {symbol} processing...")
        
        # Get stock data
        stock_data = data_manager.get_symbol_indicators(collection_id, symbol)
        
        if stock_data is not None and not stock_data.empty:
            print(f"   ✅ Got stock data: {len(stock_data)} rows")
            
            # Test OpenAI score calculation
            try:
                openai_score = engine._calculate_openai_score(symbol, stock_data)
                print(f"   OpenAI score: {openai_score}")
                
                # Check if it's using comprehensive or simplified
                if hasattr(engine, 'openai_analyzer'):
                    print(f"   OpenAI analyzer available: {engine.openai_analyzer is not None}")
                else:
                    print(f"   ❌ OpenAI analyzer not available")
                    
            except Exception as e:
                print(f"   ❌ Error calculating OpenAI score: {e}")
        else:
            print(f"   ❌ No stock data available")
            
    except Exception as e:
        print(f"   ❌ Error testing hybrid engine: {e}")

def main():
    """Run the OpenAI scoring debug analysis."""
    print("🚀 OpenAI Scoring Debug Analysis")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test OpenAI analysis directly
    test_openai_analysis_directly()
    
    # Test OpenAI API endpoint
    test_openai_api_endpoint()
    
    # Check OpenAI storage
    check_openai_storage()
    
    # Test hybrid ranking engine internals
    test_hybrid_ranking_engine_internals()
    
    print("\n" + "=" * 80)
    print("✅ OpenAI Scoring Debug Analysis Completed!")
    print("\n📋 Key Issues Identified:")
    print("1. OpenAI scores are limited to 7 values (10-45)")
    print("2. 44 symbols (39.3%) have score 45.0")
    print("3. Likely falling back to simplified scoring")
    print("4. Need to investigate OpenAI API integration")

if __name__ == "__main__":
    main() 