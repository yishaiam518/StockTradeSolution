#!/usr/bin/env python3
"""
Test API Price Fetching

Tests the API endpoints for buy/sell operations with optional price parameters.
"""

import sys
import os
import json
import requests
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_api_price_fetching():
    """Test API endpoints with automatic price fetching."""
    logger.info("🧪 Testing API Price Fetching")
    logger.info("=" * 50)
    
    # Base URL for the Flask app
    base_url = "http://localhost:5000"
    
    try:
        # Test 1: Get all portfolios
        logger.info("📊 Test 1: Getting portfolios")
        logger.info("-" * 30)
        
        response = requests.get(f"{base_url}/api/portfolios")
        if response.status_code == 200:
            portfolios = response.json()
            logger.info(f"✅ Found {len(portfolios.get('portfolios', []))} portfolios")
            
            # Find user portfolio
            user_portfolio = None
            for portfolio in portfolios.get('portfolios', []):
                if portfolio.get('type') == 'user_managed':
                    user_portfolio = portfolio
                    break
            
            if not user_portfolio:
                logger.error("❌ No user portfolio found")
                return False
            
            portfolio_id = user_portfolio['id']
            logger.info(f"📈 Using portfolio: {user_portfolio['name']} (ID: {portfolio_id})")
        else:
            logger.error(f"❌ Failed to get portfolios: {response.status_code}")
            return False
        
        # Test 2: Buy stock without price (API should fetch automatically)
        logger.info("\n📊 Test 2: Buying stock via API without price")
        logger.info("-" * 30)
        
        buy_data = {
            "symbol": "AAPL",
            "shares": 3,
            # "price" is intentionally omitted to test automatic fetching
            "notes": "API test - automatic price fetching"
        }
        
        logger.info(f"🔄 Sending buy request: {json.dumps(buy_data, indent=2)}")
        
        response = requests.post(
            f"{base_url}/api/portfolios/{portfolio_id}/buy",
            json=buy_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Buy successful: {result.get('message', 'No message')}")
        else:
            logger.error(f"❌ Buy failed: {response.status_code} - {response.text}")
            return False
        
        # Test 3: Sell stock without price (API should fetch automatically)
        logger.info("\n📊 Test 3: Selling stock via API without price")
        logger.info("-" * 30)
        
        sell_data = {
            "symbol": "AAPL",
            "shares": 2,
            # "price" is intentionally omitted to test automatic fetching
            "notes": "API test - automatic price fetching for sell"
        }
        
        logger.info(f"🔄 Sending sell request: {json.dumps(sell_data, indent=2)}")
        
        response = requests.post(
            f"{base_url}/api/portfolios/{portfolio_id}/sell",
            json=sell_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Sell successful: {result.get('message', 'No message')}")
        else:
            logger.error(f"❌ Sell failed: {response.status_code} - {response.text}")
            return False
        
        # Test 4: Get portfolio transactions to verify
        logger.info("\n📊 Test 4: Verifying transactions")
        logger.info("-" * 30)
        
        response = requests.get(f"{base_url}/api/portfolios/{portfolio_id}/transactions")
        if response.status_code == 200:
            transactions = response.json()
            logger.info(f"✅ Retrieved {len(transactions.get('transactions', []))} transactions")
            
            # Show the latest transactions
            for i, transaction in enumerate(transactions.get('transactions', [])[:3]):
                logger.info(f"📊 Transaction {i+1}: {transaction.get('symbol')} - {transaction.get('transaction_type')} - {transaction.get('shares')} shares at ${transaction.get('price', 0):.2f}")
        else:
            logger.error(f"❌ Failed to get transactions: {response.status_code}")
            return False
        
        # Test 5: Test with explicit price (should still work)
        logger.info("\n📊 Test 5: Buying with explicit price")
        logger.info("-" * 30)
        
        buy_with_price_data = {
            "symbol": "MSFT",
            "shares": 2,
            "price": 300.00,  # Explicit price
            "notes": "API test - explicit price"
        }
        
        logger.info(f"🔄 Sending buy request with explicit price: {json.dumps(buy_with_price_data, indent=2)}")
        
        response = requests.post(
            f"{base_url}/api/portfolios/{portfolio_id}/buy",
            json=buy_with_price_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Buy with explicit price successful: {result.get('message', 'No message')}")
        else:
            logger.error(f"❌ Buy with explicit price failed: {response.status_code} - {response.text}")
            return False
        
        logger.info("\n🎉 All API price fetching tests completed!")
        return True
        
    except requests.exceptions.ConnectionError:
        logger.error("❌ Could not connect to Flask app. Make sure it's running on http://localhost:5000")
        return False
    except Exception as e:
        logger.error(f"❌ Error during API price fetching test: {e}")
        import traceback
        logger.error(f"🔍 Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Starting API Price Fetching Test")
    logger.info("=" * 50)
    logger.info("⚠️  Make sure the Flask app is running on http://localhost:5000")
    logger.info("=" * 50)
    
    success = test_api_price_fetching()
    
    if success:
        logger.info("✅ All API tests passed! Automatic price fetching via API is working correctly.")
    else:
        logger.error("❌ Some API tests failed. Please check the logs above.")
        sys.exit(1) 