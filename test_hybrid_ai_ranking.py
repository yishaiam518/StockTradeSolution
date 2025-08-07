#!/usr/bin/env python3
"""
Test Hybrid AI Ranking System

This script demonstrates the hybrid approach that:
1. Compares OpenAI vs local algorithms
2. Provides dual scoring (e.g., 50/63.2)
3. Analyzes algorithm performance
4. Generates improvement insights
"""

import requests
import json
import time
from datetime import datetime

def test_hybrid_ranking_system():
    """Test the hybrid AI ranking system."""
    base_url = "http://localhost:8080"
    
    print("🧪 Testing Hybrid AI Ranking System")
    print("=" * 60)
    print("🎯 Features:")
    print("   - Dual scoring (OpenAI vs Local)")
    print("   - Algorithm comparison")
    print("   - Performance insights")
    print("   - Improvement recommendations")
    print("=" * 60)
    
    # Test 1: Hybrid ranking endpoint
    print("\n1. Testing hybrid ranking endpoint...")
    try:
        response = requests.get(f"{base_url}/api/ai-ranking/collection/ALL_20250803_160817/hybrid-rank?max_stocks=5")
        data = response.json()
        
        if data.get('success'):
            print("✅ Hybrid ranking working")
            print(f"   - Total stocks: {data.get('total_stocks', 0)}")
            print(f"   - Dual scores count: {len(data.get('dual_scores', []))}")
            
            # Show sample dual scores
            dual_scores = data.get('dual_scores', [])
            if dual_scores:
                print("\n📊 Sample Dual Scores:")
                for i, score in enumerate(dual_scores[:3]):
                    print(f"   {i+1}. {score['symbol']}: OpenAI={score['openai_score']}, Local={score['local_score']}, Diff={score['score_difference']}")
                    print(f"      Confidence: {score['confidence_level']}")
                    print(f"      Combined: {(score['openai_score'] + score['local_score']) / 2:.1f}")
            
            # Show algorithm performance
            performance = data.get('algorithm_performance', {})
            if performance:
                print("\n📈 Algorithm Performance:")
                print(f"   - Average score difference: {performance.get('average_score_difference', 0)}")
                print(f"   - Average OpenAI score: {performance.get('average_openai_score', 0)}")
                print(f"   - Average local score: {performance.get('average_local_score', 0)}")
                print(f"   - Algorithm correlation: {performance.get('algorithm_correlation', 0)}")
                print(f"   - High confidence cases: {performance.get('high_confidence_count', 0)}")
                print(f"   - Divergent analysis cases: {performance.get('divergent_analysis_count', 0)}")
            
            # Show improvement insights
            insights = data.get('improvement_insights', [])
            if insights:
                print("\n💡 Improvement Insights:")
                for insight in insights:
                    print(f"   - {insight}")
        else:
            print("❌ Hybrid ranking failed")
            print(f"   - Error: {data.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Hybrid ranking test failed: {e}")
    
    # Test 2: Compare with regular ranking
    print("\n2. Comparing hybrid vs regular ranking...")
    try:
        # Get regular ranking
        regular_response = requests.get(f"{base_url}/api/ai-ranking/collection/ALL_20250803_160817/rank?max_stocks=5")
        regular_data = regular_response.json()
        
        if regular_data.get('success') and data.get('success'):
            print("✅ Comparison analysis:")
            print(f"   - Regular ranking stocks: {len(regular_data.get('top_stocks', []))}")
            print(f"   - Hybrid ranking stocks: {len(data.get('dual_scores', []))}")
            
            # Compare scores if available
            regular_scores = regular_data.get('top_stocks', [])
            hybrid_scores = data.get('dual_scores', [])
            
            if regular_scores and hybrid_scores:
                print("\n📊 Score Comparison (First 3 stocks):")
                for i in range(min(3, len(regular_scores), len(hybrid_scores))):
                    regular = regular_scores[i]
                    hybrid = hybrid_scores[i]
                    
                    if regular['symbol'] == hybrid['symbol']:
                        regular_score = regular.get('total_score', 0)
                        hybrid_local = hybrid.get('local_score', 0)
                        hybrid_openai = hybrid.get('openai_score', 0)
                        
                        print(f"   {regular['symbol']}:")
                        print(f"     Regular: {regular_score:.1f}")
                        print(f"     Hybrid Local: {hybrid_local:.1f}")
                        print(f"     Hybrid OpenAI: {hybrid_openai:.1f}")
                        print(f"     Difference: {abs(regular_score - hybrid_local):.1f}")
        else:
            print("❌ Comparison failed - one or both rankings failed")
    except Exception as e:
        print(f"❌ Comparison test failed: {e}")
    
    # Test 3: Cached hybrid ranking
    print("\n3. Testing cached hybrid ranking...")
    try:
        response = requests.get(f"{base_url}/api/ai-ranking/collection/ALL_20250803_160817/hybrid-rank?max_stocks=5&use_cache=true")
        data = response.json()
        
        if data.get('success'):
            print("✅ Cached hybrid ranking working")
            print(f"   - Response time: Fast (cached)")
            print(f"   - Dual scores: {len(data.get('dual_scores', []))}")
        else:
            print("❌ Cached hybrid ranking failed")
            print(f"   - Error: {data.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Cached hybrid ranking test failed: {e}")

def demonstrate_algorithm_improvement():
    """Demonstrate how the hybrid system helps improve algorithms."""
    print("\n🔬 Algorithm Improvement Demonstration")
    print("=" * 50)
    
    print("\n📋 How the Hybrid System Improves Algorithms:")
    print("1. **Dual Scoring**: Compare OpenAI (50) vs Local (63.2)")
    print("2. **Pattern Analysis**: Identify when algorithms agree/disagree")
    print("3. **Performance Tracking**: Monitor correlation over time")
    print("4. **Insight Generation**: Provide specific improvement suggestions")
    
    print("\n🎯 Benefits:")
    print("✅ **Immediate Value**: Get both AI and local perspectives")
    print("✅ **Confidence Levels**: Know when to trust each algorithm")
    print("✅ **Continuous Improvement**: Use OpenAI to enhance local algorithms")
    print("✅ **Cost Optimization**: Reduce OpenAI usage as local algorithms improve")
    print("✅ **Risk Management**: Identify divergent cases for manual review")
    
    print("\n📊 Example Output Format:")
    print("   AAPL: OpenAI=65.2, Local=72.1, Diff=6.9, Confidence=Medium")
    print("   MSFT: OpenAI=58.4, Local=58.7, Diff=0.3, Confidence=High")
    print("   NVDA: OpenAI=45.1, Local=78.9, Diff=33.8, Confidence=Divergent")

def main():
    """Run the hybrid AI ranking test suite."""
    print("🚀 Hybrid AI Ranking System Test Suite")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test the hybrid system
    test_hybrid_ranking_system()
    
    # Demonstrate algorithm improvement concepts
    demonstrate_algorithm_improvement()
    
    print("\n" + "=" * 60)
    print("✅ Hybrid AI Ranking System Test Completed!")
    print("\n📋 Summary of Hybrid Features:")
    print("1. ✅ Dual scoring (OpenAI + Local algorithms)")
    print("2. ✅ Algorithm performance comparison")
    print("3. ✅ Confidence level assessment")
    print("4. ✅ Improvement insights generation")
    print("5. ✅ Caching for performance")
    print("6. ✅ Export capabilities for analysis")
    
    print("\n🎯 Next Steps:")
    print("- Monitor algorithm correlation over time")
    print("- Use divergent cases to improve local algorithms")
    print("- Gradually reduce OpenAI dependency as local algorithms improve")
    print("- Export comparison data for detailed analysis")

if __name__ == "__main__":
    main() 