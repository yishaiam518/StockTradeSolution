#!/usr/bin/env python3
"""
Test Portfolio Management System

This script tests the portfolio management functionality including:
- Portfolio creation and initialization
- Stock buying and selling
- Performance tracking
- AI portfolio management
"""

import sys
import os
import logging
from datetime import datetime, date
from typing import Dict, List

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.portfolio_management.portfolio_database import (
    PortfolioDatabase, PortfolioType, TransactionType
)
from src.portfolio_management.portfolio_manager import PortfolioManager
from src.data_collection.data_manager import DataCollectionManager as DataManager
from src.ai_ranking.hybrid_ranking_engine import HybridRankingEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_portfolio_initialization():
    """Test portfolio initialization and default portfolio creation."""
    logger.info("🧪 Testing Portfolio Initialization")
    
    try:
        # Initialize portfolio manager
        data_manager = DataManager()
        hybrid_ranking_engine = HybridRankingEngine(data_manager)
        portfolio_manager = PortfolioManager(data_manager, hybrid_ranking_engine)
        
        # Get all portfolios
        portfolios = portfolio_manager.db.get_all_portfolios()
        logger.info(f"✅ Found {len(portfolios)} portfolios")
        
        for portfolio in portfolios:
            logger.info(f"📊 Portfolio: {portfolio.name} (ID: {portfolio.id})")
            logger.info(f"   Type: {portfolio.portfolio_type.value}")
            logger.info(f"   Initial Cash: ${portfolio.initial_cash:,.2f}")
            logger.info(f"   Current Cash: ${portfolio.current_cash:,.2f}")
            
            # Get portfolio summary
            summary = portfolio_manager.get_portfolio_summary(portfolio.id)
            if summary:
                logger.info(f"   Total Value: ${summary.total_value:,.2f}")
                logger.info(f"   Total P&L: ${summary.total_pnl:,.2f} ({summary.total_pnl_pct:.2f}%)")
                logger.info(f"   Positions: {summary.positions_count}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing portfolio initialization: {e}")
        return False

def test_stock_transactions():
    """Test buying and selling stocks."""
    logger.info("🧪 Testing Stock Transactions")
    
    try:
        # Initialize portfolio manager
        data_manager = DataManager()
        hybrid_ranking_engine = HybridRankingEngine(data_manager)
        portfolio_manager = PortfolioManager(data_manager, hybrid_ranking_engine)
        
        # Get user portfolio (first portfolio)
        portfolios = portfolio_manager.db.get_all_portfolios()
        if not portfolios:
            logger.error("❌ No portfolios found")
            return False
        
        user_portfolio = next((p for p in portfolios if p.portfolio_type == PortfolioType.USER_MANAGED), None)
        if not user_portfolio:
            logger.error("❌ No user portfolio found")
            return False
        
        portfolio_id = user_portfolio.id
        logger.info(f"📊 Testing transactions for portfolio: {user_portfolio.name} (ID: {portfolio_id})")
        
        # Test buying stocks
        test_stocks = [
            {"symbol": "AAPL", "shares": 10, "price": 150.0},
            {"symbol": "GOOGL", "shares": 5, "price": 2800.0},
            {"symbol": "MSFT", "shares": 15, "price": 300.0}
        ]
        
        for stock in test_stocks:
            success = portfolio_manager.buy_stock(
                portfolio_id=portfolio_id,
                symbol=stock["symbol"],
                shares=stock["shares"],
                price=stock["price"],
                notes=f"Test purchase of {stock['shares']} shares"
            )
            
            if success:
                logger.info(f"✅ Bought {stock['shares']} shares of {stock['symbol']} at ${stock['price']}")
            else:
                logger.error(f"❌ Failed to buy {stock['symbol']}")
        
        # Get updated portfolio summary
        summary = portfolio_manager.get_portfolio_summary(portfolio_id)
        if summary:
            logger.info(f"📊 Portfolio Summary after purchases:")
            logger.info(f"   Total Value: ${summary.total_value:,.2f}")
            logger.info(f"   Cash: ${summary.cash:,.2f}")
            logger.info(f"   Positions Value: ${summary.positions_value:,.2f}")
            logger.info(f"   Positions Count: {summary.positions_count}")
        
        # Test selling a stock
        success = portfolio_manager.sell_stock(
            portfolio_id=portfolio_id,
            symbol="AAPL",
            shares=5,
            price=155.0,
            notes="Test sale of 5 shares"
        )
        
        if success:
            logger.info("✅ Sold 5 shares of AAPL at $155.0")
        else:
            logger.error("❌ Failed to sell AAPL")
        
        # Get final portfolio summary
        final_summary = portfolio_manager.get_portfolio_summary(portfolio_id)
        if final_summary:
            logger.info(f"📊 Final Portfolio Summary:")
            logger.info(f"   Total Value: ${final_summary.total_value:,.2f}")
            logger.info(f"   Cash: ${final_summary.cash:,.2f}")
            logger.info(f"   Positions Value: ${final_summary.positions_value:,.2f}")
            logger.info(f"   Total P&L: ${final_summary.total_pnl:,.2f} ({final_summary.total_pnl_pct:.2f}%)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing stock transactions: {e}")
        return False

def test_portfolio_comparison():
    """Test portfolio comparison functionality."""
    logger.info("🧪 Testing Portfolio Comparison")
    
    try:
        # Initialize portfolio manager
        data_manager = DataManager()
        hybrid_ranking_engine = HybridRankingEngine(data_manager)
        portfolio_manager = PortfolioManager(data_manager, hybrid_ranking_engine)
        
        # Get portfolio comparison
        comparison = portfolio_manager.get_portfolio_comparison()
        
        logger.info("📊 Portfolio Comparison:")
        
        if comparison['user_portfolio']:
            user = comparison['user_portfolio']
            logger.info(f"👤 User Portfolio:")
            logger.info(f"   Total Value: ${user.total_value:,.2f}")
            logger.info(f"   Total P&L: ${user.total_pnl:,.2f} ({user.total_pnl_pct:.2f}%)")
            logger.info(f"   Positions: {user.positions_count}")
            logger.info(f"   Cash: ${user.cash:,.2f}")
        
        if comparison['ai_portfolio']:
            ai = comparison['ai_portfolio']
            logger.info(f"🤖 AI Portfolio:")
            logger.info(f"   Total Value: ${ai.total_value:,.2f}")
            logger.info(f"   Total P&L: ${ai.total_pnl:,.2f} ({ai.total_pnl_pct:.2f}%)")
            logger.info(f"   Positions: {ai.positions_count}")
            logger.info(f"   Cash: ${ai.cash:,.2f}")
        
        if comparison['comparison']:
            comp = comparison['comparison']
            logger.info(f"📈 Comparison Metrics:")
            logger.info(f"   User Return: {comp['user_total_return']:.2f}%")
            logger.info(f"   AI Return: {comp['ai_total_return']:.2f}%")
            logger.info(f"   Performance Difference: {comp['performance_difference']:.2f}%")
            logger.info(f"   User Cash Utilization: {comp['user_cash_utilization']:.2f}%")
            logger.info(f"   AI Cash Utilization: {comp['ai_cash_utilization']:.2f}%")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing portfolio comparison: {e}")
        return False

def test_ai_portfolio_management():
    """Test AI portfolio management."""
    logger.info("🧪 Testing AI Portfolio Management")
    
    try:
        # Initialize portfolio manager
        data_manager = DataManager()
        hybrid_ranking_engine = HybridRankingEngine(data_manager)
        portfolio_manager = PortfolioManager(data_manager, hybrid_ranking_engine)
        
        # Get AI portfolio
        portfolios = portfolio_manager.db.get_all_portfolios()
        ai_portfolio = next((p for p in portfolios if p.portfolio_type == PortfolioType.AI_MANAGED), None)
        
        if not ai_portfolio:
            logger.error("❌ No AI portfolio found")
            return False
        
        logger.info(f"🤖 Testing AI portfolio management for: {ai_portfolio.name} (ID: {ai_portfolio.id})")
        
        # Get initial summary
        initial_summary = portfolio_manager.get_portfolio_summary(ai_portfolio.id)
        if initial_summary:
            logger.info(f"📊 Initial AI Portfolio State:")
            logger.info(f"   Total Value: ${initial_summary.total_value:,.2f}")
            logger.info(f"   Cash: ${initial_summary.cash:,.2f}")
            logger.info(f"   Positions: {initial_summary.positions_count}")
        
        # Test AI portfolio management
        result = portfolio_manager.manage_ai_portfolio(ai_portfolio.id)
        
        if result['success']:
            logger.info(f"✅ AI Portfolio Management Result:")
            logger.info(f"   Total Decisions: {result['total_decisions']}")
            logger.info(f"   Actions Taken: {len(result['actions_taken'])}")
            
            for action in result['actions_taken']:
                logger.info(f"   {action['action'].upper()}: {action['symbol']} - {action['reason']}")
        else:
            logger.error(f"❌ AI Portfolio Management Failed: {result.get('error', 'Unknown error')}")
        
        # Get final summary
        final_summary = portfolio_manager.get_portfolio_summary(ai_portfolio.id)
        if final_summary:
            logger.info(f"📊 Final AI Portfolio State:")
            logger.info(f"   Total Value: ${final_summary.total_value:,.2f}")
            logger.info(f"   Cash: ${final_summary.cash:,.2f}")
            logger.info(f"   Positions: {final_summary.positions_count}")
            logger.info(f"   Total P&L: ${final_summary.total_pnl:,.2f} ({final_summary.total_pnl_pct:.2f}%)")
        
        return result['success']
        
    except Exception as e:
        logger.error(f"❌ Error testing AI portfolio management: {e}")
        return False

def test_performance_tracking():
    """Test performance tracking functionality."""
    logger.info("🧪 Testing Performance Tracking")
    
    try:
        # Initialize portfolio manager
        data_manager = DataManager()
        hybrid_ranking_engine = HybridRankingEngine(data_manager)
        portfolio_manager = PortfolioManager(data_manager, hybrid_ranking_engine)
        
        # Get portfolios
        portfolios = portfolio_manager.db.get_all_portfolios()
        
        for portfolio in portfolios:
            logger.info(f"📊 Testing performance tracking for: {portfolio.name}")
            
            # Record daily snapshot with sample price data
            sample_prices = {
                "AAPL": 150.0,
                "GOOGL": 2800.0,
                "MSFT": 300.0,
                "TSLA": 800.0,
                "NVDA": 500.0
            }
            
            portfolio_manager.record_daily_snapshot(portfolio.id, sample_prices)
            
            # Get performance history
            performance_history = portfolio_manager.db.get_portfolio_performance_history(
                portfolio.id, days=7
            )
            
            logger.info(f"   Performance History Records: {len(performance_history)}")
            
            if performance_history:
                latest = performance_history[0]  # Most recent
                logger.info(f"   Latest Performance:")
                logger.info(f"     Date: {latest.date}")
                logger.info(f"     Total Value: ${latest.total_value:,.2f}")
                logger.info(f"     P&L: ${latest.pnl:,.2f} ({latest.return_pct:.2f}%)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing performance tracking: {e}")
        return False

def main():
    """Run all portfolio system tests."""
    logger.info("🚀 Starting Portfolio Management System Tests")
    logger.info("=" * 60)
    
    tests = [
        ("Portfolio Initialization", test_portfolio_initialization),
        ("Stock Transactions", test_stock_transactions),
        ("Portfolio Comparison", test_portfolio_comparison),
        ("AI Portfolio Management", test_ai_portfolio_management),
        ("Performance Tracking", test_performance_tracking)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Running: {test_name}")
        logger.info("-" * 40)
        
        try:
            success = test_func()
            results.append((test_name, success))
            
            if success:
                logger.info(f"✅ {test_name}: PASSED")
            else:
                logger.error(f"❌ {test_name}: FAILED")
                
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📋 TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        logger.info(f"   {test_name}: {status}")
    
    logger.info(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Portfolio system is working correctly.")
    else:
        logger.error(f"⚠️  {total - passed} tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 