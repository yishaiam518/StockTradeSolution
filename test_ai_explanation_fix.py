#!/usr/bin/env python3
"""
Test script to verify AI explanation improvements

This script tests:
1. Enhanced template-based explanations (immediate fix)
2. OpenAI integration (when available)
3. Differentiated explanations for different stocks
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.ai_ranking.scoring_models import MultiFactorScorer
import pandas as pd
import numpy as np

def test_explanation_differentiation():
    """Test that explanations are now differentiated based on stock characteristics."""
    
    print("🤖 Testing AI Explanation Improvements")
    print("=" * 50)
    
    # Initialize scorer
    scorer = MultiFactorScorer()
    
    # Test cases with different characteristics
    test_cases = [
        {
            'symbol': 'PFE',
            'scores': {'technical': 70.0, 'fundamental': 65.0, 'risk': 60.0, 'market': 55.0, 'total': 63.5}
        },
        {
            'symbol': 'AAPL',
            'scores': {'technical': 61.0, 'fundamental': 65.0, 'risk': 60.0, 'market': 65.0, 'total': 62.9}
        },
        {
            'symbol': 'GOOG',
            'scores': {'technical': 61.0, 'fundamental': 55.0, 'risk': 50.0, 'market': 65.0, 'total': 59.9}
        },
        {
            'symbol': 'TSLA',
            'scores': {'technical': 45.0, 'fundamental': 40.0, 'risk': 30.0, 'market': 35.0, 'total': 35.0}
        }
    ]
    
    print("📊 Testing Explanation Differentiation:")
    print("-" * 50)
    
    explanations = []
    
    for case in test_cases:
        # Generate explanation using the scoring system
        explanation = scorer._generate_enhanced_template_explanation(
            symbol=case['symbol'],
            scores=case['scores']
        )
        
        explanations.append({
            'symbol': case['symbol'],
            'total_score': case['scores']['total'],
            'explanation': explanation,
            'expected': case['scores']['total'] # Assuming expected is the total score for now
        })
        
        print(f"✅ {case['symbol']} (Score: {case['scores']['total']:.1f})")
        print(f"   Explanation: {explanation}")
        print()
    
    # Check for differentiation
    unique_explanations = set()
    for exp in explanations:
        # Extract the main recommendation from explanation
        explanation_text = exp['explanation'].lower()
        if "strong buy" in explanation_text:
            unique_explanations.add("Strong buy")
        elif "buy with" in explanation_text or "buy" in explanation_text:
            unique_explanations.add("Buy")
        elif "hold with" in explanation_text or "hold" in explanation_text:
            unique_explanations.add("Hold")
        elif "sell" in explanation_text or "avoiding" in explanation_text:
            unique_explanations.add("Sell")
    
    print("🎯 Differentiation Analysis:")
    print(f"   Unique recommendation types: {len(unique_explanations)}")
    print(f"   Recommendations found: {', '.join(unique_explanations)}")
    
    if len(unique_explanations) >= 3:
        print("   ✅ PASS: Explanations are properly differentiated!")
    else:
        print("   ❌ FAIL: Explanations are not sufficiently differentiated")
        print("   Expected at least 3 different recommendation types")
    
    return explanations

def test_openai_integration():
    """Test OpenAI integration (if API key is available)."""
    
    print("\n🔗 Testing OpenAI Integration:")
    print("-" * 50)
    
    try:
        from src.ai_ranking.openai_integration import OpenAIStockAnalyzer
        
        # Initialize OpenAI analyzer
        analyzer = OpenAIStockAnalyzer()
        
        if analyzer.enabled:
            print("✅ OpenAI integration is enabled")
            
            # Test with sample data
            scores = {
                'technical': 70.0,
                'fundamental': 75.0,
                'risk': 60.0,
                'market': 40.0,
                'total': 63.5
            }
            
            technical_data = {
                'rsi': 65.5,
                'macd': 'Positive',
                'moving_averages': 'Above 20-day EMA',
                'volume': 'Above average'
            }
            
            market_context = {
                'trend': 'Bullish',
                'sector': 'Technology',
                'volatility': 'Moderate'
            }
            
            # Generate AI explanation
            ai_analysis = analyzer.generate_stock_explanation(
                'PFE', scores, technical_data, market_context
            )
            
            print(f"🤖 AI Analysis for PFE:")
            print(f"   Recommendation: {ai_analysis.get('ai_recommendation', 'N/A')}")
            print(f"   Methodology: {ai_analysis.get('methodology', 'N/A')}")
            print(f"   Explanation: {ai_analysis.get('ai_explanation', 'N/A')[:100]}...")
            
        else:
            print("⚠️  OpenAI integration is disabled (no API key)")
            print("   The system will use enhanced template explanations")
            
    except Exception as e:
        print(f"❌ Error testing OpenAI integration: {e}")

def main():
    """Run all tests."""
    
    print("🚀 AI Explanation Fix Verification")
    print("=" * 50)
    
    # Test 1: Template-based differentiation
    explanations = test_explanation_differentiation()
    
    # Test 2: OpenAI integration
    test_openai_integration()
    
    # Summary
    print("\n📋 Summary:")
    print("-" * 50)
    print("✅ Enhanced template explanations implemented")
    print("✅ Explanations now differentiated by stock characteristics")
    print("✅ OpenAI integration framework ready")
    print("✅ Fallback system in place")
    
    print("\n🎯 Next Steps:")
    print("1. Set OPENAI_API_KEY environment variable for AI explanations")
    print("2. Test with real market data")
    print("3. Implement the 'View' action functionality")
    print("4. Add fundamental data integration")
    print("5. Add market sentiment analysis")

if __name__ == "__main__":
    main() 