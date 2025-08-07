#!/usr/bin/env python3
"""
Test Portfolio Integration

Tests the portfolio integration with the AI ranking page.
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

def test_portfolio_integration():
    """Test portfolio integration with AI ranking."""
    logger.info("🧪 Testing Portfolio Integration with AI Ranking")
    logger.info("=" * 60)
    
    try:
        # Initialize components
        data_manager = DataManager()
        hybrid_ranking_engine = HybridRankingEngine(data_manager)
        portfolio_manager = PortfolioManager(data_manager, hybrid_ranking_engine)
        
        # Test 1: Verify portfolios exist
        logger.info("📊 Test 1: Verifying portfolios exist")
        logger.info("-" * 40)
        
        portfolios = portfolio_manager.db.get_all_portfolios()
        logger.info(f"✅ Found {len(portfolios)} portfolios")
        
        for portfolio in portfolios:
            logger.info(f"📈 Portfolio: {portfolio.name} (ID: {portfolio.id}, Type: {portfolio.portfolio_type.value})")
            summary = portfolio_manager.get_portfolio_summary(portfolio.id)
            if summary:
                logger.info(f"   💰 Total Value: ${summary.total_value:.2f}")
                logger.info(f"   💵 Cash: ${summary.cash:.2f}")
                logger.info(f"   📊 Positions: {summary.positions_count}")
                logger.info(f"   📈 P&L: ${summary.total_pnl:.2f} ({summary.total_pnl_pct:.2f}%)")
        
        # Test 2: Test buying stock from AI ranking
        logger.info("\n📊 Test 2: Testing buy stock from AI ranking")
        logger.info("-" * 40)
        
        user_portfolio = next((p for p in portfolios if p.portfolio_type.value == 'user_managed'), None)
        if not user_portfolio:
            logger.error("❌ No user portfolio found")
            return False
        
        symbol = "AAPL"
        shares = 50
        
        logger.info(f"🔄 Testing buy {shares} shares of {symbol} for portfolio {user_portfolio.id}")
        
        success = portfolio_manager.buy_stock(
            portfolio_id=user_portfolio.id,
            symbol=symbol,
            shares=shares,
            price=None,  # Test automatic price fetching
            notes="Test buy from AI ranking"
        )
        
        if success:
            logger.info("✅ Successfully bought stock from AI ranking")
            
            # Get updated portfolio summary
            updated_summary = portfolio_manager.get_portfolio_summary(user_portfolio.id)
            logger.info(f"📊 Updated Portfolio Summary:")
            logger.info(f"   💰 Total Value: ${updated_summary.total_value:.2f}")
            logger.info(f"   💵 Cash: ${updated_summary.cash:.2f}")
            logger.info(f"   📊 Positions: {updated_summary.positions_count}")
        else:
            logger.error("❌ Failed to buy stock from AI ranking")
            return False
        
        # Test 3: Test selling stock from AI ranking
        logger.info("\n📊 Test 3: Testing sell stock from AI ranking")
        logger.info("-" * 40)
        
        logger.info(f"🔄 Testing sell {shares} shares of {symbol} for portfolio {user_portfolio.id}")
        
        success = portfolio_manager.sell_stock(
            portfolio_id=user_portfolio.id,
            symbol=symbol,
            shares=shares,
            price=None,  # Test automatic price fetching
            notes="Test sell from AI ranking"
        )
        
        if success:
            logger.info("✅ Successfully sold stock from AI ranking")
            
            # Get updated portfolio summary
            final_summary = portfolio_manager.get_portfolio_summary(user_portfolio.id)
            logger.info(f"📊 Final Portfolio Summary:")
            logger.info(f"   💰 Total Value: ${final_summary.total_value:.2f}")
            logger.info(f"   💵 Cash: ${final_summary.cash:.2f}")
            logger.info(f"   📊 Positions: {final_summary.positions_count}")
        else:
            logger.error("❌ Failed to sell stock from AI ranking")
            return False
        
        # Test 4: Test portfolio API endpoints
        logger.info("\n📊 Test 4: Testing portfolio API endpoints")
        logger.info("-" * 40)
        
        # Test getting all portfolios
        try:
            import requests
            response = requests.get('http://localhost:5000/api/portfolios')
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Portfolio API working - found {len(data.get('portfolios', []))} portfolios")
            else:
                logger.warning(f"⚠️ Portfolio API returned status {response.status_code}")
        except Exception as e:
            logger.warning(f"⚠️ Could not test portfolio API (Flask app may not be running): {e}")
        
        # Test 5: Test AI portfolio management
        logger.info("\n📊 Test 5: Testing AI portfolio management")
        logger.info("-" * 40)
        
        ai_portfolio = next((p for p in portfolios if p.portfolio_type.value == 'ai_managed'), None)
        if ai_portfolio:
            logger.info(f"🤖 Testing AI portfolio management for portfolio {ai_portfolio.id}")
            
            # Test AI portfolio management
            result = portfolio_manager.manage_ai_portfolio(ai_portfolio.id)
            logger.info(f"✅ AI portfolio management result:")
            logger.info(f"   📊 Total Decisions: {result.get('total_decisions', 0)}")
            logger.info(f"   🎯 Actions Taken: {result.get('actions_taken', 0)}")
            logger.info(f"   💰 Portfolio Value: ${result.get('portfolio_value', 0):.2f}")
        else:
            logger.warning("⚠️ No AI portfolio found")
        
        logger.info("\n🎉 All portfolio integration tests completed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error during portfolio integration test: {e}")
        import traceback
        logger.error(f"🔍 Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Starting Portfolio Integration Test")
    logger.info("=" * 60)
    
    success = test_portfolio_integration()
    
    if success:
        logger.info("✅ All tests passed! Portfolio integration is working correctly.")
    else:
        logger.error("❌ Some tests failed. Please check the logs above.")
        sys.exit(1) 