#!/usr/bin/env python3
"""
Test AI Backtesting Modal
Test script to verify the AI backtesting modal functionality.
"""

import requests
import json
import sys
from datetime import datetime

def test_ai_backtesting_modal():
    """Test the AI backtesting modal functionality."""
    base_url = "http://localhost:8080"
    session = requests.Session()
    
    print("🔍 AI BACKTESTING MODAL TEST")
    print("=" * 50)
    print(f"Timestamp: {datetime.now()}")
    print(f"Base URL: {base_url}")
    print("=" * 50)
    
    # Test 1: Check if dashboard is accessible
    print("\n1️⃣ Testing Dashboard Accessibility...")
    try:
        response = session.get(f"{base_url}/data-collection")
        if response.status_code == 200:
            print("✅ Dashboard is accessible")
        else:
            print(f"❌ Dashboard failed: Status {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Dashboard error: {e}")
        return
    
    # Test 2: Check AI Backtesting API endpoints
    print("\n2️⃣ Testing AI Backtesting API Endpoints...")
    
    # Test status endpoint
    try:
        response = session.get(f"{base_url}/api/ai-backtesting/status")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Status endpoint working")
                print(f"   Engine Status: {data.get('engine_status')}")
                print(f"   Has Results: {data.get('has_results')}")
                print(f"   Strategies Tested: {data.get('total_strategies_tested')}")
            else:
                print(f"❌ Status endpoint failed: {data.get('error')}")
        else:
            print(f"❌ Status endpoint failed: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Status endpoint error: {e}")
    
    # Test parameters endpoint
    try:
        response = session.get(f"{base_url}/api/ai-backtesting/parameters")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Parameters endpoint working")
                params = data.get('parameters', {})
                print(f"   Available Cash: ${params.get('available_cash', 0):,.2f}")
                print(f"   Transaction Limit: {params.get('transaction_limit_pct', 0) * 100:.1f}%")
                print(f"   Stop Loss: {params.get('stop_loss_pct', 0) * 100:.1f}%")
                print(f"   Stop Gain: {params.get('stop_gain_pct', 0) * 100:.1f}%")
            else:
                print(f"❌ Parameters endpoint failed: {data.get('error')}")
        else:
            print(f"❌ Parameters endpoint failed: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Parameters endpoint error: {e}")
    
    # Test strategies endpoint
    try:
        response = session.get(f"{base_url}/api/ai-backtesting/strategies")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                strategies = data.get('strategies', [])
                print("✅ Strategies endpoint working")
                print(f"   Available Strategies: {len(strategies)}")
                for strategy in strategies[:3]:  # Show first 3
                    print(f"     - {strategy.get('label')}")
            else:
                print(f"❌ Strategies endpoint failed: {data.get('error')}")
        else:
            print(f"❌ Strategies endpoint failed: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Strategies endpoint error: {e}")
    
    # Test combinations endpoint
    try:
        response = session.get(f"{base_url}/api/ai-backtesting/combinations?max_combinations=3")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                combinations = data.get('combinations', [])
                print("✅ Combinations endpoint working")
                print(f"   Strategy Combinations: {len(combinations)}")
                for combo in combinations[:3]:  # Show first 3
                    print(f"     - {combo.get('name')} ({combo.get('count')} strategies)")
            else:
                print(f"❌ Combinations endpoint failed: {data.get('error')}")
        else:
            print(f"❌ Combinations endpoint failed: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Combinations endpoint error: {e}")
    
    # Test 3: Check if modal template is accessible
    print("\n3️⃣ Testing Modal Template Accessibility...")
    try:
        response = session.get(f"{base_url}/templates/ai_backtesting_modal.html")
        if response.status_code == 200:
            print("✅ Modal template is accessible")
            content = response.text
            if "AI Backtesting Modal" in content:
                print("✅ Modal template contains expected content")
            else:
                print("❌ Modal template missing expected content")
        else:
            print(f"❌ Modal template failed: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Modal template error: {e}")
    
    # Test 4: Check if JavaScript file is accessible
    print("\n4️⃣ Testing JavaScript File Accessibility...")
    try:
        response = session.get(f"{base_url}/static/js/ai_backtesting.js")
        if response.status_code == 200:
            print("✅ JavaScript file is accessible")
            content = response.text
            if "AIBacktestingModal" in content:
                print("✅ JavaScript file contains expected class")
            else:
                print("❌ JavaScript file missing expected class")
        else:
            print(f"❌ JavaScript file failed: Status {response.status_code}")
    except Exception as e:
        print(f"❌ JavaScript file error: {e}")
    
    # Test 5: Test parameter update
    print("\n5️⃣ Testing Parameter Update...")
    try:
        new_params = {
            "available_cash": 2000000.0,
            "transaction_limit_pct": 0.03,
            "stop_loss_pct": 0.08,
            "stop_gain_pct": 0.25,
            "safe_net": 15000.0,
            "risk_tolerance": "aggressive",
            "recommendation_threshold": 0.25
        }
        
        response = session.put(f"{base_url}/api/ai-backtesting/parameters", json=new_params)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Parameter update successful")
                updated_params = data.get('parameters', {})
                print(f"   Updated Available Cash: ${updated_params.get('available_cash', 0):,.2f}")
                print(f"   Updated Transaction Limit: {updated_params.get('transaction_limit_pct', 0) * 100:.1f}%")
            else:
                print(f"❌ Parameter update failed: {data.get('error')}")
        else:
            print(f"❌ Parameter update failed: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Parameter update error: {e}")
    
    # Test 6: Test backtesting run (with sample data)
    print("\n6️⃣ Testing Backtesting Run...")
    try:
        backtest_data = {
            "collection_id": "test_collection_123"
        }
        
        response = session.post(f"{base_url}/api/ai-backtesting/run", json=backtest_data)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Backtesting run successful")
                summary = data.get('summary', {})
                print(f"   Strategies Tested: {summary.get('total_strategies_tested')}")
                print(f"   Best Strategy: {summary.get('best_strategy', {}).get('name')}")
                print(f"   Best Return: {summary.get('best_strategy', {}).get('total_return_pct', 0):.2f}%")
            else:
                print(f"❌ Backtesting run failed: {data.get('error')}")
        else:
            print(f"❌ Backtesting run failed: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Backtesting run error: {e}")
    
    # Test 7: Check results
    print("\n7️⃣ Testing Results Retrieval...")
    try:
        response = session.get(f"{base_url}/api/ai-backtesting/results")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                results = data.get('results', [])
                print("✅ Results retrieval successful")
                print(f"   Total Results: {len(results)}")
                if results:
                    for result in results[:2]:  # Show first 2 results
                        print(f"     - {result.get('strategy_name')}: {result.get('total_return_pct', 0):.2f}%")
            else:
                print(f"❌ Results retrieval failed: {data.get('error')}")
        else:
            print(f"❌ Results retrieval failed: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Results retrieval error: {e}")
    
    # Test 8: Check summary
    print("\n8️⃣ Testing Summary Retrieval...")
    try:
        response = session.get(f"{base_url}/api/ai-backtesting/summary")
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('summary'):
                summary = data.get('summary')
                print("✅ Summary retrieval successful")
                print(f"   Best Strategy: {summary.get('best_strategy', {}).get('name')}")
                print(f"   Average Return: {summary.get('average_return', 0):.2f}%")
                print(f"   Recommendations: {len(summary.get('recommendations', []))}")
            else:
                print("✅ Summary endpoint working (no summary available yet)")
        else:
            print(f"❌ Summary retrieval failed: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Summary retrieval error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 AI BACKTESTING MODAL TEST COMPLETED")
    print("=" * 50)
    print("\n📋 NEXT STEPS:")
    print("1. Open the dashboard in your browser")
    print("2. Go to Portfolio Management section")
    print("3. Click the 'AI Backtesting' button")
    print("4. Verify the modal opens with all functionality")
    print("5. Test parameter changes and backtesting runs")

if __name__ == "__main__":
    test_ai_backtesting_modal()
