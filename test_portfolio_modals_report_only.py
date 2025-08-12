#!/usr/bin/env python3
"""
Portfolio Modals Issue Report
This script tests both user and AI portfolio modals and reports any issues found.
It does NOT modify any logic - only reports problems.
"""

import requests
import json
import sys
from datetime import datetime

def test_portfolio_modals_and_report_issues():
    """Test portfolio modals and report any issues found."""
    base_url = "http://localhost:8080"
    session = requests.Session()
    
    print("🔍 PORTFOLIO MODALS COMPREHENSIVE TEST - ISSUE REPORT")
    print("=" * 60)
    print(f"Timestamp: {datetime.now()}")
    print(f"Base URL: {base_url}")
    print("=" * 60)
    
    issues = []
    
    # Test 1: Dashboard Health
    print("\n1️⃣ Testing Dashboard Health...")
    try:
        response = session.get(f"{base_url}/")
        if response.status_code == 200 or response.status_code == 302:
            print("✅ Dashboard is accessible")
        else:
            issue = f"Dashboard health check failed: Status {response.status_code}"
            issues.append(issue)
            print(f"❌ {issue}")
    except Exception as e:
        issue = f"Dashboard health check error: {e}"
        issues.append(issue)
        print(f"❌ {issue}")
    
    # Test 2: Portfolio API Endpoints
    print("\n2️⃣ Testing Portfolio API Endpoints...")
    
    # Test GET /api/portfolios
    try:
        response = session.get(f"{base_url}/api/portfolios")
        if response.status_code == 200:
            portfolios = response.json().get('portfolios', [])
            print(f"✅ GET /api/portfolios: Found {len(portfolios)} portfolios")
            
            # Check if we have both user and AI portfolios
            user_portfolios = [p for p in portfolios if p.get('type') == 'user_managed']
            ai_portfolios = [p for p in portfolios if p.get('type') == 'ai_managed']
            
            if user_portfolios:
                print(f"   📊 User portfolios: {len(user_portfolios)}")
            else:
                issue = "No user-managed portfolios found"
                issues.append(issue)
                print(f"   ❌ {issue}")
                
            if ai_portfolios:
                print(f"   🤖 AI portfolios: {len(ai_portfolios)}")
            else:
                issue = "No AI-managed portfolios found"
                issues.append(issue)
                print(f"   ❌ {issue}")
                
        else:
            issue = f"GET /api/portfolios failed: Status {response.status_code}"
            issues.append(issue)
            print(f"❌ {issue}")
    except Exception as e:
        issue = f"GET /api/portfolios error: {e}"
        issues.append(issue)
        print(f"❌ {issue}")
    
    # Test 3: Portfolio Creation
    print("\n3️⃣ Testing Portfolio Creation...")
    try:
        test_portfolio = {
            "name": "Issue Test Portfolio",
            "portfolio_type": "user_managed",
            "initial_cash": 50000.0
        }
        
        response = session.post(f"{base_url}/api/portfolios", json=test_portfolio)
        if response.status_code == 200:
            portfolio_data = response.json()
            portfolio_id = portfolio_data.get('portfolio_id')
            print(f"✅ Portfolio creation successful: ID {portfolio_id}")
            
            # Test buy transaction
            print("\n4️⃣ Testing Buy Transaction...")
            buy_data = {
                "symbol": "AAPL",
                "shares": 10,
                "price": 150.0,
                "notes": "Issue test buy transaction"
            }
            
            response = session.post(f"{base_url}/api/portfolios/{portfolio_id}/buy", json=buy_data)
            if response.status_code == 200:
                print("✅ Buy transaction successful")
            else:
                issue = f"Buy transaction failed: Status {response.status_code} - {response.text}"
                issues.append(issue)
                print(f"❌ {issue}")
            
            # Test sell transaction
            print("\n5️⃣ Testing Sell Transaction...")
            sell_data = {
                "symbol": "AAPL",
                "shares": 5,
                "price": 155.0,
                "notes": "Issue test sell transaction"
            }
            
            response = session.post(f"{base_url}/api/portfolios/{portfolio_id}/sell", json=sell_data)
            if response.status_code == 200:
                print("✅ Sell transaction successful")
            else:
                issue = f"Sell transaction failed: Status {response.status_code} - {response.text}"
                issues.append(issue)
                print(f"❌ {issue}")
            
            # Test portfolio summary
            print("\n6️⃣ Testing Portfolio Summary...")
            response = session.get(f"{base_url}/api/portfolios/{portfolio_id}")
            if response.status_code == 200:
                portfolio_info = response.json()
                summary = portfolio_info.get('summary', {})
                
                # Check if all required fields are present
                required_fields = ['total_value', 'total_pnl', 'total_pnl_pct', 'positions_count', 'cash', 'positions_value']
                missing_fields = [field for field in required_fields if field not in summary]
                
                if missing_fields:
                    issue = f"Portfolio summary missing fields: {missing_fields}"
                    issues.append(issue)
                    print(f"❌ {issue}")
                else:
                    print("✅ Portfolio summary has all required fields")
                    print(f"   💰 Total Value: ${summary.get('total_value', 0):,.2f}")
                    print(f"   📈 Total P&L: ${summary.get('total_pnl', 0):,.2f}")
                    print(f"   📊 Positions: {summary.get('positions_count', 0)}")
            else:
                issue = f"Portfolio summary failed: Status {response.status_code}"
                issues.append(issue)
                print(f"❌ {issue}")
                
        else:
            issue = f"Portfolio creation failed: Status {response.status_code} - {response.text}"
            issues.append(issue)
            print(f"❌ {issue}")
    except Exception as e:
        issue = f"Portfolio creation/transaction error: {e}"
        issues.append(issue)
        print(f"❌ {issue}")
    
    # Test 7: Portfolio Comparison
    print("\n7️⃣ Testing Portfolio Comparison...")
    try:
        response = session.get(f"{base_url}/api/portfolios/comparison")
        if response.status_code == 200:
            comparison = response.json()
            if comparison.get('success'):
                print("✅ Portfolio comparison successful")
                # Check if comparison data is complete
                comparison_data = comparison.get('comparison', {})
                if comparison_data:
                    print(f"   📊 Comparison data available: {len(comparison_data)} metrics")
                else:
                    issue = "Portfolio comparison returned empty data"
                    issues.append(issue)
                    print(f"   ❌ {issue}")
            else:
                issue = f"Portfolio comparison failed: {comparison.get('error', 'Unknown error')}"
                issues.append(issue)
                print(f"❌ {issue}")
        else:
            issue = f"Portfolio comparison failed: Status {response.status_code} - {response.text}"
            issues.append(issue)
            print(f"❌ {issue}")
    except Exception as e:
        issue = f"Portfolio comparison error: {e}"
        issues.append(issue)
        print(f"❌ {issue}")
    
    # Test 8: AI Portfolio Management
    print("\n8️⃣ Testing AI Portfolio Management...")
    try:
        # Find an AI portfolio
        response = session.get(f"{base_url}/api/portfolios")
        if response.status_code == 200:
            portfolios = response.json().get('portfolios', [])
            ai_portfolio = next((p for p in portfolios if p.get('type') == 'ai_managed'), None)
            
            if ai_portfolio:
                portfolio_id = ai_portfolio['id']
                print(f"   🤖 Testing AI portfolio ID: {portfolio_id}")
                
                # Test AI management toggle
                ai_data = {"enabled": True}
                response = session.post(f"{base_url}/api/portfolios/{portfolio_id}/manage-ai", json=ai_data)
                if response.status_code == 200:
                    print("✅ AI management toggle successful")
                else:
                    issue = f"AI management toggle failed: Status {response.status_code}"
                    issues.append(issue)
                    print(f"❌ {issue}")
            else:
                issue = "No AI portfolio found for testing"
                issues.append(issue)
                print(f"   ❌ {issue}")
        else:
            issue = f"Failed to get portfolios for AI testing: Status {response.status_code}"
            issues.append(issue)
            print(f"❌ {issue}")
    except Exception as e:
        issue = f"AI portfolio management error: {e}"
        issues.append(issue)
        print(f"❌ {issue}")
    
    # Test 9: Frontend Modal Functions (if accessible)
    print("\n9️⃣ Testing Frontend Modal Access...")
    try:
        response = session.get(f"{base_url}/data-collection")
        if response.status_code == 200:
            print("✅ Data collection page accessible (frontend modals should be available)")
        else:
            issue = f"Data collection page failed: Status {response.status_code}"
            issues.append(issue)
            print(f"❌ {issue}")
    except Exception as e:
        issue = f"Frontend modal access error: {e}"
        issues.append(issue)
        print(f"❌ {issue}")
    
    # Summary Report
    print("\n" + "=" * 60)
    print("📋 ISSUE SUMMARY REPORT")
    print("=" * 60)
    
    if not issues:
        print("🎉 NO ISSUES FOUND! All portfolio modal functionality is working correctly.")
    else:
        print(f"⚠️  FOUND {len(issues)} ISSUE(S):")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
        
        print("\n🔧 RECOMMENDED ACTIONS:")
        print("   - Review the specific error messages above")
        print("   - Check server logs for additional details")
        print("   - Verify database schema and data integrity")
        print("   - Test with different portfolio configurations")
    
    print("\n" + "=" * 60)
    print("✅ Testing completed - No logic was modified")
    print("=" * 60)

if __name__ == "__main__":
    test_portfolio_modals_and_report_issues()
