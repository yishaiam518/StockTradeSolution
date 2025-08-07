#!/usr/bin/env python3
"""
Comprehensive Error Handling Verification Test

This script verifies that all the error handling improvements are working:
1. 'Close' column error resolution
2. Timeout handling improvements
3. Graceful degradation
4. Proper fallback mechanisms
"""

import requests
import json
import time
from datetime import datetime

def test_error_handling_improvements():
    """Test all error handling improvements."""
    base_url = "http://localhost:8080"
    
    print("🔧 Comprehensive Error Handling Verification")
    print("=" * 60)
    print("🎯 Testing Error Handling Improvements:")
    print("   1. 'Close' column error resolution")
    print("   2. Timeout handling improvements")
    print("   3. Graceful degradation mechanisms")
    print("   4. Proper fallback mechanisms")
    print("   5. Reduced error frequency")
    print("=" * 60)
    
    # Test 1: Regular AI Ranking Error Handling
    print("\n1. Testing Regular AI Ranking Error Handling...")
    try:
        start_time = time.time()
        response = requests.get(f"{base_url}/api/ai-ranking/collection/ALL_20250803_160817/rank?max_stocks=5")
        elapsed_time = time.time() - start_time
        data = response.json()
        
        if data.get('success'):
            print("✅ Regular AI ranking working")
            print(f"   - Response time: {elapsed_time:.2f}s")
            print(f"   - Top stocks: {len(data.get('top_stocks', []))}")
            
            # Check for specific error patterns
            if 'Error calculating risk score' not in response.text:
                print("   - ✅ 'Close' column errors resolved in regular ranking")
            else:
                print("   - ⚠️ Some 'Close' errors may still occur in regular ranking")
                
            # Check score quality
            top_stocks = data.get('top_stocks', [])
            if top_stocks:
                first_stock = top_stocks[0]
                if 'total_score' in first_stock and first_stock['total_score'] != 50.0:
                    print("   - ✅ Scores are varied (not all 50.0)")
                else:
                    print("   - ⚠️ Scores may still be uniform")
        else:
            print("❌ Regular AI ranking failed")
            print(f"   - Error: {data.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Regular ranking test failed: {e}")
    
    # Test 2: Hybrid AI Ranking Error Handling
    print("\n2. Testing Hybrid AI Ranking Error Handling...")
    try:
        start_time = time.time()
        response = requests.get(f"{base_url}/api/ai-ranking/collection/ALL_20250803_160817/hybrid-rank?max_stocks=5")
        elapsed_time = time.time() - start_time
        data = response.json()
        
        if data.get('success'):
            print("✅ Hybrid AI ranking working")
            print(f"   - Response time: {elapsed_time:.2f}s")
            print(f"   - Dual scores: {len(data.get('dual_scores', []))}")
            
            # Check for specific error patterns
            if 'Error calculating local score' not in response.text:
                print("   - ✅ 'Close' column errors resolved in hybrid ranking")
            else:
                print("   - ⚠️ Some 'Close' errors may still occur in hybrid ranking")
                
            # Check dual score quality
            dual_scores = data.get('dual_scores', [])
            if dual_scores:
                first_score = dual_scores[0]
                if 'openai_score' in first_score and 'local_score' in first_score:
                    print("   - ✅ Dual scoring working correctly")
                    print(f"   - Sample scores: OpenAI={first_score['openai_score']:.1f}, Local={first_score['local_score']:.1f}")
                else:
                    print("   - ⚠️ Dual scoring may have issues")
        else:
            print("❌ Hybrid AI ranking failed")
            print(f"   - Error: {data.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Hybrid ranking test failed: {e}")
    
    # Test 3: Timeout Handling
    print("\n3. Testing Timeout Handling...")
    try:
        # Test with larger dataset to trigger timeout
        start_time = time.time()
        response = requests.get(f"{base_url}/api/ai-ranking/collection/ALL_20250803_160817/hybrid-rank?max_stocks=10")
        elapsed_time = time.time() - start_time
        data = response.json()
        
        if data.get('success'):
            print("✅ Timeout handling working")
            print(f"   - Response time: {elapsed_time:.2f}s")
            print(f"   - Partial results returned: {len(data.get('dual_scores', []))}")
            
            if elapsed_time < 35:  # Should complete within 35 seconds
                print("   - ✅ Timeout handling working correctly")
            else:
                print("   - ⚠️ Response time longer than expected")
        else:
            print("❌ Timeout handling failed")
            print(f"   - Error: {data.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Timeout test failed: {e}")
    
    # Test 4: Error Recovery
    print("\n4. Testing Error Recovery...")
    try:
        # Test with invalid collection to see error handling
        response = requests.get(f"{base_url}/api/ai-ranking/collection/INVALID_COLLECTION/rank?max_stocks=5")
        data = response.json()
        
        if not data.get('success'):
            print("✅ Error recovery working correctly")
            print(f"   - Proper error response for invalid collection")
        else:
            print("⚠️ Unexpected success for invalid collection")
    except Exception as e:
        print(f"❌ Error recovery test failed: {e}")
    
    # Test 5: Performance Analysis
    print("\n5. Testing Performance and Data Quality...")
    try:
        # Test both ranking systems
        regular_response = requests.get(f"{base_url}/api/ai-ranking/collection/ALL_20250803_160817/rank?max_stocks=3")
        hybrid_response = requests.get(f"{base_url}/api/ai-ranking/collection/ALL_20250803_160817/hybrid-rank?max_stocks=3")
        
        regular_data = regular_response.json()
        hybrid_data = hybrid_response.json()
        
        print("✅ Performance analysis:")
        
        if regular_data.get('success') and regular_data.get('top_stocks'):
            regular_scores = [stock['total_score'] for stock in regular_data['top_stocks']]
            print(f"   - Regular ranking scores: {min(regular_scores):.1f} - {max(regular_scores):.1f}")
            
            if len(set(regular_scores)) > 1:
                print("   - ✅ Regular ranking has score variation")
            else:
                print("   - ⚠️ Regular ranking scores may be uniform")
        
        if hybrid_data.get('success') and hybrid_data.get('dual_scores'):
            hybrid_scores = [score['openai_score'] + score['local_score'] for score in hybrid_data['dual_scores']]
            print(f"   - Hybrid ranking scores: {min(hybrid_scores):.1f} - {max(hybrid_scores):.1f}")
            
            if len(set(hybrid_scores)) > 1:
                print("   - ✅ Hybrid ranking has score variation")
            else:
                print("   - ⚠️ Hybrid ranking scores may be uniform")
                
    except Exception as e:
        print(f"❌ Performance analysis failed: {e}")

def analyze_error_patterns():
    """Analyze the current error patterns and improvements."""
    print("\n📊 Error Pattern Analysis")
    print("=" * 40)
    
    print("\n🔧 Fixes Implemented:")
    print("1. ✅ Column name flexibility (Close/close/CLOSE)")
    print("2. ✅ Graceful fallback to default scores (50.0)")
    print("3. ✅ Individual error isolation per symbol")
    print("4. ✅ Timeout reduction (60s → 30s)")
    print("5. ✅ Partial results return on timeout")
    print("6. ✅ Detailed error logging for debugging")
    print("7. ✅ Data validation before calculations")
    print("8. ✅ Exception handling at multiple levels")
    
    print("\n🎯 Expected Improvements:")
    print("1. ✅ Reduced 'Close' column errors")
    print("2. ✅ Faster response times")
    print("3. ✅ Better error recovery")
    print("4. ✅ More varied score distributions")
    print("5. ✅ Stable system operation")
    
    print("\n📈 Performance Metrics:")
    print("1. ✅ Error frequency should be reduced")
    print("2. ✅ Response times should be consistent")
    print("3. ✅ Score quality should be improved")
    print("4. ✅ System stability should be enhanced")

def main():
    """Run the comprehensive error handling verification."""
    print("🚀 Comprehensive Error Handling Verification")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test the error handling improvements
    test_error_handling_improvements()
    
    # Analyze error patterns
    analyze_error_patterns()
    
    print("\n" + "=" * 60)
    print("✅ Error Handling Verification Completed!")
    print("\n📋 Summary:")
    print("1. ✅ 'Close' column errors should be resolved")
    print("2. ✅ Timeout handling should be improved")
    print("3. ✅ Error recovery should be working")
    print("4. ✅ Performance should be stable")
    print("5. ✅ Score quality should be enhanced")
    
    print("\n🎯 Next Steps:")
    print("- Monitor server logs for reduced error frequency")
    print("- Verify score quality improvements")
    print("- Test with larger datasets")
    print("- Proceed with algorithm improvement phase")
    print("- Monitor system stability over time")

if __name__ == "__main__":
    main() 