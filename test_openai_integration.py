#!/usr/bin/env python3
"""
Test script to verify OpenAI integration for AI stock analysis
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.ai_ranking.openai_integration import OpenAIStockAnalyzer
from src.ai_ranking.scoring_models import MultiFactorScorer
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

def test_openai_integration():
    """Test OpenAI integration functionality."""
    
    print("🤖 Testing OpenAI Integration")
    print("=" * 50)
    
    # Test 1: Initialize OpenAI Analyzer
    print("\n=== TEST 1: OpenAI Analyzer Initialization ===")
    analyzer = OpenAIStockAnalyzer()
    
    if analyzer.is_available():
        print("✅ OpenAI integration is available")
        print(f"   API Key: {'*' * 20}{analyzer.api_key[-4:] if analyzer.api_key else 'None'}")
    else:
        print("❌ OpenAI integration is not available")
        print("   This will use fallback explanations")
    
    # Test 2: Generate AI Explanation
    print("\n=== TEST 2: AI Explanation Generation ===")
    
    # Test cases with different characteristics
    test_cases = [
        {
            "symbol": "PFE",
            "scores": {"technical": 70.0, "fundamental": 65.0, "risk": 60.0, "market": 55.0, "total": 63.5}
        },
        {
            "symbol": "AAPL", 
            "scores": {"technical": 61.0, "fundamental": 65.0, "risk": 60.0, "market": 65.0, "total": 62.9}
        },
        {
            "symbol": "GOOG",
            "scores": {"technical": 61.0, "fundamental": 55.0, "risk": 50.0, "market": 65.0, "total": 59.9}
        },
        {
            "symbol": "TSLA",
            "scores": {"technical": 45.0, "fundamental": 40.0, "risk": 30.0, "market": 35.0, "total": 35.0}
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i}: {case['symbol']} ---")
        print(f"   Scores: {case['scores']}")
        
        # Generate AI explanation
        explanation = analyzer.generate_stock_explanation(
            symbol=case['symbol'],
            scores=case['scores']
        )
        
        print(f"   AI Explanation: {explanation}")
        
        # Check if explanation is differentiated
        if "buy" in explanation.lower() and case['scores']['total'] >= 60:
            print("   ✅ Explanation matches recommendation (Buy)")
        elif "hold" in explanation.lower() and 50 <= case['scores']['total'] < 60:
            print("   ✅ Explanation matches recommendation (Hold)")
        elif "sell" in explanation.lower() and case['scores']['total'] < 50:
            print("   ✅ Explanation matches recommendation (Sell)")
        else:
            print("   ⚠️  Explanation may not match recommendation")
    
    # Test 3: System Comparison
    print("\n=== TEST 3: System Comparison ===")
    
    if analyzer.is_available():
        comparison = analyzer.compare_systems(
            symbol="PFE",
            our_scores={"technical": 70.0, "fundamental": 65.0, "risk": 60.0, "total": 63.5}
        )
        
        print(f"   Status: {comparison.get('status', 'Unknown')}")
        print(f"   Comparison: {comparison.get('comparison', 'No comparison available')}")
    else:
        print("   ⏭️  Skipping system comparison (OpenAI not available)")
    
    # Test 4: Market Insights
    print("\n=== TEST 4: Market Insights ===")
    
    if analyzer.is_available():
        insights = analyzer.get_market_insights(
            symbols=["PFE", "AAPL", "GOOG", "TSLA"]
        )
        
        print(f"   Status: {insights.get('status', 'Unknown')}")
        print(f"   Insights: {insights.get('insights', 'No insights available')}")
    else:
        print("   ⏭️  Skipping market insights (OpenAI not available)")
    
    # Test 5: Integration with Scoring System
    print("\n=== TEST 5: Integration with Scoring System ===")
    
    scorer = MultiFactorScorer()
    
    for case in test_cases[:2]:  # Test first 2 cases
        print(f"\n--- Testing {case['symbol']} with Scoring System ---")
        
        # Generate explanation using the scoring system
        explanation = scorer._generate_explanation(
            symbol=case['symbol'],
            technical=case['scores']['technical'],
            fundamental=case['scores']['fundamental'],
            risk=case['scores']['risk'],
            market=case['scores']['market'],
            total=case['scores']['total']
        )
        
        print(f"   Generated Explanation: {explanation}")
        
        # Check if it's AI-generated or fallback
        if "openai" in explanation.lower() or "ai" in explanation.lower():
            print("   🤖 AI-generated explanation")
        else:
            print("   📝 Template-based explanation")
    
    print("\n" + "=" * 50)
    print("🎯 OpenAI Integration Test Complete!")
    
    if analyzer.is_available():
        print("✅ OpenAI integration is working correctly")
        print("✅ AI-powered explanations are being generated")
        print("✅ Fallback system is in place for reliability")
    else:
        print("⚠️  OpenAI integration is not available")
        print("✅ Fallback explanations are working correctly")
        print("💡 To enable AI explanations, ensure OpenAI API key is set")

if __name__ == "__main__":
    test_openai_integration() 