#!/usr/bin/env python3
"""
Test Automatic Price Fetching

Tests the automatic price fetching functionality for portfolio transactions.
"""

import sys
import os
import logging
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.portfolio_management.portfolio_manager import PortfolioManager
from src.data_collection.data_manager import DataCollectionManager as DataManager
from src.ai_ranking.hybrid_ranking_engine import HybridRankingEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_automatic_price_fetching():
    """Test automatic price fetching for portfolio transactions."""
    logger.info("🧪 Testing Automatic Price Fetching")
    logger.info("=" * 50)
    
    try:
        # Initialize components
        data_manager = DataManager()
        hybrid_ranking_engine = HybridRankingEngine(data_manager)
        portfolio_manager = PortfolioManager(data_manager, hybrid_ranking_engine)
        
        # Test 1: Buy stock without price (should fetch automatically)
        logger.info("📊 Test 1: Buying stock without price")
        logger.info("-" * 30)
        
        # Get user portfolio
        portfolios = portfolio_manager.db.get_all_portfolios()
        user_portfolio = next((p for p in portfolios if p.portfolio_type.value == 'user_managed'), None)
        
        if not user_portfolio:
            logger.error("❌ No user portfolio found")
            return False
        
        logger.info(f"📈 Testing with portfolio: {user_portfolio.name} (ID: {user_portfolio.id})")
        
        # Test buying AAPL without price
        symbol = "AAPL"
        shares = 5
        
        logger.info(f"🔄 Attempting to buy {shares} shares of {symbol} without specifying price...")
        
        success = portfolio_manager.buy_stock(
            portfolio_id=user_portfolio.id,
            symbol=symbol,
            shares=shares,
            price=None,  # This should trigger automatic price fetching
            notes="Test automatic price fetching"
        )
        
        if success:
            logger.info("✅ Successfully bought stock with automatic price fetching")
            
            # Get the transaction to see what price was used
            transactions = portfolio_manager.db.get_portfolio_transactions(user_portfolio.id, limit=1)
            if transactions:
                latest_transaction = transactions[0]
                logger.info(f"💰 Transaction price: ${latest_transaction.price:.2f}")
                logger.info(f"📊 Transaction details: {latest_transaction.shares} shares at ${latest_transaction.price:.2f}")
            else:
                logger.warning("⚠️ Could not retrieve transaction details")
        else:
            logger.error("❌ Failed to buy stock with automatic price fetching")
            return False
        
        # Test 2: Sell stock without price (should fetch automatically)
        logger.info("\n📊 Test 2: Selling stock without price")
        logger.info("-" * 30)
        
        logger.info(f"🔄 Attempting to sell {shares} shares of {symbol} without specifying price...")
        
        success = portfolio_manager.sell_stock(
            portfolio_id=user_portfolio.id,
            symbol=symbol,
            shares=shares,
            price=None,  # This should trigger automatic price fetching
            notes="Test automatic price fetching for sell"
        )
        
        if success:
            logger.info("✅ Successfully sold stock with automatic price fetching")
            
            # Get the latest transaction to see what price was used
            transactions = portfolio_manager.db.get_portfolio_transactions(user_portfolio.id, limit=2)
            if len(transactions) >= 2:
                sell_transaction = transactions[0]  # Most recent transaction
                logger.info(f"💰 Sell transaction price: ${sell_transaction.price:.2f}")
                logger.info(f"📊 Sell transaction details: {sell_transaction.shares} shares at ${sell_transaction.price:.2f}")
            else:
                logger.warning("⚠️ Could not retrieve sell transaction details")
        else:
            logger.error("❌ Failed to sell stock with automatic price fetching")
            return False
        
        # Test 3: Verify price fetching method directly
        logger.info("\n📊 Test 3: Direct price fetching test")
        logger.info("-" * 30)
        
        test_symbols = ["AAPL", "MSFT", "GOOGL"]
        
        for symbol in test_symbols:
            logger.info(f"🔄 Fetching last traded price for {symbol}...")
            
            price = portfolio_manager._get_last_traded_price(symbol)
            
            if price is not None:
                logger.info(f"✅ {symbol}: ${price:.2f}")
            else:
                logger.warning(f"⚠️ Could not fetch price for {symbol}")
        
        logger.info("\n🎉 All automatic price fetching tests completed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error during automatic price fetching test: {e}")
        import traceback
        logger.error(f"🔍 Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Starting Automatic Price Fetching Test")
    logger.info("=" * 50)
    
    success = test_automatic_price_fetching()
    
    if success:
        logger.info("✅ All tests passed! Automatic price fetching is working correctly.")
    else:
        logger.error("❌ Some tests failed. Please check the logs above.")
        sys.exit(1) 