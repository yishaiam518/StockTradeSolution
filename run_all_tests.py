#!/usr/bin/env python3
"""
Master Test Runner for StockTradeSolution
Runs all test types and provides comprehensive reporting
"""

import sys
import os
import subprocess
import time
from datetime import datetime

def run_test_script(script_name, description):
    """Run a test script and return results"""
    print(f"\n{'='*60}")
    print(f"🧪 Running {description}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        # Run the test script
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, text=True, timeout=300)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Print output
        if result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:", result.stderr)
        
        success = result.returncode == 0
        
        print(f"\n⏱️  Duration: {duration:.2f} seconds")
        print(f"✅ Status: {'PASSED' if success else 'FAILED'}")
        
        return {
            'script': script_name,
            'description': description,
            'success': success,
            'duration': duration,
            'return_code': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
        
    except subprocess.TimeoutExpired:
        print(f"\n⏰ Test timed out after 5 minutes")
        return {
            'script': script_name,
            'description': description,
            'success': False,
            'duration': 300,
            'return_code': -1,
            'stdout': '',
            'stderr': 'Test timed out'
        }
    except Exception as e:
        print(f"\n❌ Error running test: {e}")
        return {
            'script': script_name,
            'description': description,
            'success': False,
            'duration': 0,
            'return_code': -1,
            'stdout': '',
            'stderr': str(e)
        }

def run_all_tests():
    """Run all test scripts"""
    print("🚀 StockTradeSolution - Master Test Runner")
    print("=" * 60)
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Define test scripts
    test_scripts = [
        ('test_quick_verification.py', 'Quick Verification Tests'),
        ('test_comprehensive_system.py', 'Comprehensive System Tests'),
        ('test_performance_benchmark.py', 'Performance Benchmarks')
    ]
    
    results = []
    total_start_time = time.time()
    
    # Run each test script
    for script_name, description in test_scripts:
        if os.path.exists(script_name):
            result = run_test_script(script_name, description)
            results.append(result)
        else:
            print(f"\n⚠️  Script not found: {script_name}")
            results.append({
                'script': script_name,
                'description': description,
                'success': False,
                'duration': 0,
                'return_code': -1,
                'stdout': '',
                'stderr': 'Script not found'
            })
    
    total_duration = time.time() - total_start_time
    
    # Generate comprehensive report
    print_report(results, total_duration)
    
    return results

def print_report(results, total_duration):
    """Print comprehensive test report"""
    print(f"\n{'='*80}")
    print("📊 COMPREHENSIVE TEST REPORT")
    print(f"{'='*80}")
    
    # Summary statistics
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r['success'])
    failed_tests = total_tests - passed_tests
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"📈 SUMMARY:")
    print(f"   Total Tests: {total_tests}")
    print(f"   Passed: {passed_tests}")
    print(f"   Failed: {failed_tests}")
    print(f"   Success Rate: {success_rate:.1f}%")
    print(f"   Total Duration: {total_duration:.2f} seconds")
    
    # Detailed results
    print(f"\n📋 DETAILED RESULTS:")
    print(f"{'='*80}")
    
    for i, result in enumerate(results, 1):
        status = "✅ PASSED" if result['success'] else "❌ FAILED"
        print(f"{i:2d}. {result['description']:35s} {status:10s} "
              f"({result['duration']:6.2f}s)")
        
        if not result['success'] and result['stderr']:
            print(f"    Error: {result['stderr'][:100]}...")
    
    # Performance analysis
    print(f"\n⚡ PERFORMANCE ANALYSIS:")
    print(f"{'='*80}")
    
    if results:
        avg_duration = sum(r['duration'] for r in results) / len(results)
        max_duration = max(r['duration'] for r in results)
        min_duration = min(r['duration'] for r in results)
        
        print(f"   Average Duration: {avg_duration:.2f} seconds")
        print(f"   Fastest Test: {min_duration:.2f} seconds")
        print(f"   Slowest Test: {max_duration:.2f} seconds")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    print(f"{'='*80}")
    
    if success_rate == 100:
        print("   🎉 All tests passed! Your system is working perfectly.")
        print("   🚀 Ready for production use.")
    elif success_rate >= 80:
        print("   ✅ Most tests passed. System is mostly functional.")
        print("   🔧 Review failed tests and fix issues.")
    elif success_rate >= 50:
        print("   ⚠️  Some tests passed. System has issues that need attention.")
        print("   🔧 Focus on fixing failed tests before production use.")
    else:
        print("   ❌ Many tests failed. System needs significant work.")
        print("   🔧 Review and fix all issues before continuing.")
    
    # Next steps
    print(f"\n🔄 NEXT STEPS:")
    print(f"{'='*80}")
    
    if failed_tests > 0:
        print("   1. Review failed test outputs above")
        print("   2. Fix issues in the corresponding modules")
        print("   3. Re-run tests to verify fixes")
        print("   4. Consider running individual test scripts for detailed debugging")
    else:
        print("   1. All tests passed - system is ready!")
        print("   2. Consider running performance benchmarks for optimization")
        print("   3. Test with real market data")
        print("   4. Deploy to production environment")

def main():
    """Main function"""
    try:
        results = run_all_tests()
        
        # Determine overall success
        overall_success = all(r['success'] for r in results)
        
        print(f"\n{'='*80}")
        if overall_success:
            print("🎉 ALL TESTS PASSED! System is working correctly.")
        else:
            print("⚠️  SOME TESTS FAILED. Please review the report above.")
        print(f"{'='*80}")
        
        return 0 if overall_success else 1
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Test run interrupted by user.")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 