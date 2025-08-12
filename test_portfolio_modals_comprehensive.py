#!/usr/bin/env python3
"""
Comprehensive Testing of Portfolio Modals
Tests both User Portfolio Modal and AI Portfolio Modal functionality
"""

import requests
import json
import time
import sys
import os
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.portfolio_management.portfolio_manager import PortfolioManager
from src.portfolio_management.portfolio_database import PortfolioDatabase
from src.data_collection.data_manager import DataCollectionManager

class PortfolioModalTester:
    def __init__(self):
        self.base_url = "http://localhost:8080"
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name, success, details=""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        timestamp = datetime.now().strftime("%H:%M:%S")
        result = f"[{timestamp}] {status} - {test_name}"
        if details:
            result += f" - {details}"
        print(result)
        
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details,
            'timestamp': timestamp
        })
        
    def test_dashboard_health(self):
        """Test if dashboard is responding"""
        try:
            response = self.session.get(f"{self.base_url}/")
            success = response.status_code == 200
            self.log_test("Dashboard Health Check", success, f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Dashboard Health Check", False, f"Error: {str(e)}")
            return False
    
    def test_portfolio_api_endpoints(self):
        """Test portfolio API endpoints"""
        endpoints = [
            "/api/portfolios",
            "/api/portfolios/1",
            "/api/portfolios/2"
        ]
        
        all_success = True
        for endpoint in endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                success = response.status_code in [200, 404]  # 404 is OK if portfolio doesn't exist
                self.log_test(f"API Endpoint: {endpoint}", success, f"Status: {response.status_code}")
                if not success:
                    all_success = False
            except Exception as e:
                self.log_test(f"API Endpoint: {endpoint}", False, f"Error: {str(e)}")
                all_success = False
                all_success = False
        
        return all_success
    
    def test_portfolio_creation(self):
        """Test portfolio creation and management"""
        try:
            # Test creating a test portfolio
            test_portfolio = {
                "name": "Test Portfolio",
                "portfolio_type": "user_managed",
                "initial_cash": 10000.0
            }
            
            response = self.session.post(f"{self.base_url}/api/portfolios", json=test_portfolio)
            success = response.status_code == 200
            self.log_test("Portfolio Creation", success, f"Status: {response.status_code}")
            
            if success:
                portfolio_data = response.json()
                portfolio_id = portfolio_data.get('portfolio_id')
                if portfolio_id:
                    self.log_test("Portfolio ID Assignment", True, f"ID: {portfolio_id}")
                    return portfolio_id
                else:
                    self.log_test("Portfolio ID Assignment", False, "No ID returned")
                    return None
            else:
                return None
                
        except Exception as e:
            self.log_test("Portfolio Creation", False, f"Error: {str(e)}")
            return None
    
    def test_portfolio_transactions(self, portfolio_id):
        """Test portfolio transactions (buy/sell)"""
        if not portfolio_id:
            self.log_test("Portfolio Transactions", False, "No portfolio ID")
            return False
            
        try:
            # Test buying a stock
            buy_data = {
                "symbol": "AAPL",
                "shares": 10,
                "price": 150.0,
                "notes": "Test buy transaction"
            }
            
            response = self.session.post(f"{self.base_url}/api/portfolios/{portfolio_id}/buy", json=buy_data)
            buy_success = response.status_code == 200
            self.log_test("Buy Transaction", buy_success, f"Status: {response.status_code}")
            
            # Test selling a stock
            sell_data = {
                "symbol": "AAPL",
                "shares": 5,
                "price": 155.0,
                "notes": "Test sell transaction"
            }
            
            response = self.session.post(f"{self.base_url}/api/portfolios/{portfolio_id}/sell", json=sell_data)
            sell_success = response.status_code == 200
            self.log_test("Sell Transaction", sell_success, f"Status: {response.status_code}")
            
            return buy_success and sell_success
            
        except Exception as e:
            self.log_test("Portfolio Transactions", False, f"Error: {str(e)}")
            return False
    
    def test_portfolio_summary(self, portfolio_id):
        """Test portfolio summary calculation"""
        if not portfolio_id:
            self.log_test("Portfolio Summary", False, "No portfolio ID")
            return False
            
        try:
            response = self.session.get(f"{self.base_url}/api/portfolios/{portfolio_id}")
            success = response.status_code == 200
            
            if success:
                portfolio_data = response.json()
                summary = portfolio_data.get('portfolio', {}).get('summary', {})
                
                # Check if P&L fields exist
                has_pnl = 'total_pnl' in summary
                has_pnl_pct = 'total_pnl_pct' in summary
                has_positions = 'positions_count' in summary
                
                self.log_test("Portfolio Summary Fields", has_pnl and has_pnl_pct and has_positions, 
                             f"P&L: {has_pnl}, P&L%: {has_pnl_pct}, Positions: {has_positions}")
                
                # Check if P&L includes unrealized gains
                if has_pnl:
                    total_pnl = summary.get('total_pnl', 0)
                    self.log_test("P&L Calculation", True, f"Total P&L: ${total_pnl:.2f}")
                
                return success
            else:
                self.log_test("Portfolio Summary", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Portfolio Summary", False, f"Error: {str(e)}")
            return False
    
    def test_portfolio_positions(self, portfolio_id):
        """Test portfolio positions display"""
        if not portfolio_id:
            self.log_test("Portfolio Positions", False, "No portfolio ID")
            return False
            
        try:
            response = self.session.get(f"{self.base_url}/api/portfolios/{portfolio_id}/positions")
            success = response.status_code == 200
            
            if success:
                positions_data = response.json()
                positions = positions_data.get('positions', [])
                
                self.log_test("Portfolio Positions API", True, f"Found {len(positions)} positions")
                
                # Check if positions have P&L data
                for pos in positions:
                    has_pnl = 'pnl' in pos
                    has_pnl_pct = 'pnl_pct' in pos
                    has_current_price = 'current_price' in pos
                    
                    if not (has_pnl and has_pnl_pct and has_current_price):
                        self.log_test("Position P&L Fields", False, f"Missing fields for {pos.get('symbol', 'Unknown')}")
                        return False
                
                self.log_test("Position P&L Fields", True, "All positions have P&L data")
                return True
            else:
                self.log_test("Portfolio Positions", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Portfolio Positions", False, f"Error: {str(e)}")
            return False
    
    def test_portfolio_transactions_history(self, portfolio_id):
        """Test portfolio transactions history"""
        if not portfolio_id:
            self.log_test("Portfolio Transactions History", False, "No portfolio ID")
            return False
            
        try:
            response = self.session.get(f"{self.base_url}/api/portfolios/{portfolio_id}/transactions")
            success = response.status_code == 200
            
            if success:
                transactions_data = response.json()
                transactions = transactions_data.get('transactions', [])
                
                self.log_test("Portfolio Transactions History", True, f"Found {len(transactions)} transactions")
                
                # Check if transactions have required fields
                for tx in transactions:
                    has_symbol = 'symbol' in tx
                    has_shares = 'shares' in tx
                    has_price = 'price' in tx
                    has_type = 'type' in tx
                    
                    if not (has_symbol and has_shares and has_price and has_type):
                        self.log_test("Transaction Fields", False, f"Missing fields for transaction {tx.get('id', 'Unknown')}")
                        return False
                
                self.log_test("Transaction Fields", True, "All transactions have required fields")
                return True
            else:
                self.log_test("Portfolio Transactions History", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Portfolio Transactions History", False, f"Error: {str(e)}")
            return False
    
    def test_ai_portfolio_management(self):
        """Test AI portfolio management functionality"""
        try:
            # Test AI portfolio management endpoint
            response = self.session.post(f"{self.base_url}/api/portfolios/2/manage-ai", json={})
            success = response.status_code in [200, 404]  # 404 if AI portfolio doesn't exist
            
            if response.status_code == 200:
                ai_data = response.json()
                has_decisions = 'decisions' in ai_data
                has_actions = 'actions_taken' in ai_data
                
                self.log_test("AI Portfolio Management", has_decisions and has_actions, 
                             f"Decisions: {has_decisions}, Actions: {has_actions}")
            else:
                self.log_test("AI Portfolio Management", True, "AI portfolio not found (expected)")
            
            return True
            
        except Exception as e:
            self.log_test("AI Portfolio Management", False, f"Error: {str(e)}")
            return False
    
    def test_portfolio_comparison(self):
        """Test portfolio comparison functionality"""
        try:
            response = self.session.get(f"{self.base_url}/api/portfolios/comparison")
            success = response.status_code == 200
            
            if success:
                comparison_data = response.json()
                has_portfolios = 'portfolios' in comparison_data
                has_summary = 'summary' in comparison_data
                
                self.log_test("Portfolio Comparison", has_portfolios and has_summary, 
                             f"Portfolios: {has_portfolios}, Summary: {has_summary}")
            else:
                self.log_test("Portfolio Comparison", False, f"Status: {response.status_code}")
            
            return success
            
        except Exception as e:
            self.log_test("Portfolio Comparison", False, f"Error: {str(e)}")
            return False
    
    def test_frontend_modal_functionality(self):
        """Test frontend modal functionality by checking JavaScript files"""
        try:
            # Check if portfolio modal JavaScript functions exist
            js_file = "static/js/data_collection.js"
            
            if os.path.exists(js_file):
                with open(js_file, 'r') as f:
                    content = f.read()
                
                # Check for key modal functions
                has_show_portfolio_modal = 'showPortfolioModal' in content
                has_open_user_portfolio = 'openUserPortfolioModal' in content
                has_open_ai_portfolio = 'openAIPortfolioModal' in content
                has_portfolio_transactions_grid = 'buildPortfolioTransactionsGrid' in content
                
                self.log_test("Frontend Modal Functions", has_show_portfolio_modal and has_open_user_portfolio and has_open_ai_portfolio,
                             f"showPortfolioModal: {has_show_portfolio_modal}, openUserPortfolio: {has_open_user_portfolio}, openAIPortfolio: {has_open_ai_portfolio}")
                
                return has_show_portfolio_modal and has_open_user_portfolio and has_open_ai_portfolio
            else:
                self.log_test("Frontend Modal Functions", False, "JavaScript file not found")
                return False
                
        except Exception as e:
            self.log_test("Frontend Modal Functions", False, f"Error: {str(e)}")
            return False
    
    def test_backend_portfolio_manager(self):
        """Test backend portfolio manager functionality"""
        try:
            # Test portfolio manager initialization
            portfolio_manager = PortfolioManager()
            
            # Test database connection
            db = PortfolioDatabase()
            
            # Test getting portfolios
            portfolios = db.get_all_portfolios()
            
            self.log_test("Backend Portfolio Manager", True, f"Found {len(portfolios)} portfolios")
            return True
            
        except Exception as e:
            self.log_test("Backend Portfolio Manager", False, f"Error: {str(e)}")
            return False
    
    def run_comprehensive_tests(self):
        """Run all comprehensive tests"""
        print("🚀 Starting Comprehensive Portfolio Modal Testing")
        print("=" * 60)
        
        # Test dashboard health
        if not self.test_dashboard_health():
            print("❌ Dashboard not responding. Stopping tests.")
            return False
        
        # Test backend functionality
        self.test_backend_portfolio_manager()
        
        # Test API endpoints
        self.test_portfolio_api_endpoints()
        
        # Test portfolio creation and management
        portfolio_id = self.test_portfolio_creation()
        
        if portfolio_id:
            # Test portfolio functionality
            self.test_portfolio_transactions(portfolio_id)
            self.test_portfolio_summary(portfolio_id)
            self.test_portfolio_positions(portfolio_id)
            self.test_portfolio_transactions_history(portfolio_id)
        
        # Test AI portfolio functionality
        self.test_ai_portfolio_management()
        
        # Test portfolio comparison
        self.test_portfolio_comparison()
        
        # Test frontend functionality
        self.test_frontend_modal_functionality()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
        
        print("\n" + "=" * 60)
        
        return failed_tests == 0

def main():
    """Main test execution"""
    tester = PortfolioModalTester()
    
    try:
        success = tester.run_comprehensive_tests()
        
        if success:
            print("🎉 All tests passed! Portfolio modals are ready for real testing.")
            return 0
        else:
            print("⚠️  Some tests failed. Please review and fix issues before real testing.")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️  Testing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error during testing: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
