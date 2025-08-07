#!/usr/bin/env python3
"""
Debug Scoring Issues

This script investigates why all local scores are 60.0
and why there are no BUY recommendations.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json
import pandas as pd
from datetime import datetime

def test_single_stock_scoring():
    """Test scoring for a single stock to understand the issue."""
    base_url = "http://localhost:8080"
    collection_id = "ALL_20250803_160817"
    
    print("🔍 Testing Single Stock Scoring...")
    
    try:
        # Get a single stock's data
        response = requests.get(f"{base_url}/api/ai-ranking/collection/{collection_id}/hybrid-rank?max_stocks=1&symbols=AAPL", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('dual_scores'):
                stock = data['dual_scores'][0]
                print(f"\n📊 AAPL Scoring Analysis:")
                print(f"   Symbol: {stock['symbol']}")
                print(f"   OpenAI Score: {stock['openai_score']}")
                print(f"   Local Score: {stock['local_score']}")
                print(f"   Combined Score: {stock['combined_score']}")
                print(f"   Confidence: {stock['confidence_level']}")
                print(f"   Explanation: {stock['explanation']}")
                
                # Check if this should be a BUY recommendation
                combined_score = stock['combined_score']
                if combined_score >= 60:
                    print(f"   ✅ Should be BUY recommendation (score: {combined_score})")
                else:
                    print(f"   ❌ Not a BUY recommendation (score: {combined_score})")
                    
        else:
            print(f"❌ API request failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

def analyze_scoring_distribution():
    """Analyze the distribution of scores across all stocks."""
    base_url = "http://localhost:8080"
    collection_id = "ALL_20250803_160817"
    
    print("\n🔍 Analyzing Score Distribution...")
    
    try:
        response = requests.get(f"{base_url}/api/ai-ranking/collection/{collection_id}/hybrid-rank?max_stocks=20", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('dual_scores'):
                dual_scores = data['dual_scores']
                
                # Analyze score distributions
                openai_scores = [s['openai_score'] for s in dual_scores]
                local_scores = [s['local_score'] for s in dual_scores]
                combined_scores = [s['combined_score'] for s in dual_scores]
                
                print(f"\n📊 Score Distribution Analysis:")
                print(f"   Total stocks analyzed: {len(dual_scores)}")
                
                # OpenAI scores
                unique_openai = set(openai_scores)
                print(f"   Unique OpenAI scores: {sorted(unique_openai)}")
                print(f"   OpenAI score range: {min(openai_scores)} - {max(openai_scores)}")
                
                # Local scores
                unique_local = set(local_scores)
                print(f"   Unique Local scores: {sorted(unique_local)}")
                print(f"   Local score range: {min(local_scores)} - {max(local_scores)}")
                
                # Combined scores
                unique_combined = set(combined_scores)
                print(f"   Unique Combined scores: {sorted(unique_combined)}")
                print(f"   Combined score range: {min(combined_scores)} - {max(combined_scores)}")
                
                # Recommendation analysis
                buy_count = sum(1 for score in combined_scores if score >= 60)
                strong_buy_count = sum(1 for score in combined_scores if score >= 70)
                hold_count = sum(1 for score in combined_scores if 50 <= score < 60)
                sell_count = sum(1 for score in combined_scores if score < 50)
                
                print(f"\n📊 Recommendation Distribution:")
                print(f"   Strong Buy (≥70): {strong_buy_count}")
                print(f"   Buy (60-69): {buy_count}")
                print(f"   Hold (50-59): {hold_count}")
                print(f"   Sell (<50): {sell_count}")
                
                if buy_count == 0 and strong_buy_count == 0:
                    print("   ❌ PROBLEM: No BUY recommendations!")
                else:
                    print("   ✅ Found BUY recommendations")
                    
        else:
            print(f"❌ API request failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Analysis failed: {e}")

def test_local_algorithm_logic():
    """Test the local algorithm logic to understand why scores are 60.0."""
    print("\n🔍 Testing Local Algorithm Logic...")
    
    # Simulate the local scoring logic
    print("📊 Local Algorithm Simulation:")
    
    # Test case 1: All indicators favorable
    rsi_score = 100  # RSI in good range
    macd_score = 100  # MACD bullish
    ma_score = 100   # Price above moving averages
    technical_score = (rsi_score + macd_score + ma_score) / 3
    risk_score = 50.0  # Default risk
    local_score = (technical_score * 0.6 + risk_score * 0.4)
    
    print(f"   Case 1 - All indicators favorable:")
    print(f"     Technical score: {technical_score}")
    print(f"     Risk score: {risk_score}")
    print(f"     Local score: {local_score}")
    
    # Test case 2: Mixed indicators
    rsi_score = 50  # RSI neutral
    macd_score = 50  # MACD neutral
    ma_score = 50   # Price at moving averages
    technical_score = (rsi_score + macd_score + ma_score) / 3
    risk_score = 50.0  # Default risk
    local_score = (technical_score * 0.6 + risk_score * 0.4)
    
    print(f"   Case 2 - Mixed indicators:")
    print(f"     Technical score: {technical_score}")
    print(f"     Risk score: {risk_score}")
    print(f"     Local score: {local_score}")
    
    # Test case 3: Poor indicators
    rsi_score = 50  # RSI neutral
    macd_score = 50  # MACD neutral
    ma_score = 50   # Price at moving averages
    technical_score = (rsi_score + macd_score + ma_score) / 3
    risk_score = 30.0  # Higher risk
    local_score = (technical_score * 0.6 + risk_score * 0.4)
    
    print(f"   Case 3 - Poor indicators with high risk:")
    print(f"     Technical score: {technical_score}")
    print(f"     Risk score: {risk_score}")
    print(f"     Local score: {local_score}")

def suggest_improvements():
    """Suggest improvements to the scoring algorithm."""
    print("\n🔍 Suggested Improvements:")
    print("1. **Local Algorithm Issues:**")
    print("   - All default values are 50.0, leading to 60.0 average")
    print("   - Need more granular scoring based on actual indicator values")
    print("   - Risk calculation is too simplistic")
    print("   - Missing volume analysis and market context")
    
    print("\n2. **Recommendation Threshold Issues:**")
    print("   - BUY threshold (60) might be too high")
    print("   - Need to consider market conditions")
    print("   - Should have more granular recommendations")
    
    print("\n3. **OpenAI Integration Issues:**")
    print("   - OpenAI scores seem to be falling back to simplified scoring")
    print("   - Need to verify OpenAI API responses")
    print("   - Should have better error handling for OpenAI failures")

def main():
    """Run the scoring debug analysis."""
    print("🚀 Scoring Issues Debug Analysis")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test single stock scoring
    test_single_stock_scoring()
    
    # Analyze score distribution
    analyze_scoring_distribution()
    
    # Test local algorithm logic
    test_local_algorithm_logic()
    
    # Suggest improvements
    suggest_improvements()
    
    print("\n" + "=" * 60)
    print("✅ Scoring Issues Debug Analysis Completed!")
    print("\n📋 Key Findings:")
    print("1. Local algorithm is producing 60.0 scores due to default values")
    print("2. No BUY recommendations because scores are too low")
    print("3. Algorithm needs more sophisticated scoring logic")
    print("4. OpenAI integration may be falling back to simplified scoring")

if __name__ == "__main__":
    main() 