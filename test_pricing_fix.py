#!/usr/bin/env python3
"""
Test script to verify the pricing fix for historical backtesting.
Checks that buy and sell prices are different and that there's no same-day exit.
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.backtesting.backtest_engine import BacktestEngine
from src.utils.logger import get_logger

def test_pricing_fix():
    """Test that buy and sell prices are different and no same-day exits."""
    logger = get_logger(__name__)
    
    logger.info("🧪 Testing pricing fix for historical backtesting...")
    
    # Initialize backtest engine
    engine = BacktestEngine()
    
    # Run a short backtest to check pricing
    results = engine.run_historical_backtest(
        strategy="macd_canonical",
        profile="aggressive", 
        start_date="2023-01-01",
        end_date="2023-12-31",  # Full year to get more trades
        benchmark="SPY"
    )
    
    if 'error' in results:
        logger.error(f"❌ Backtest failed: {results['error']}")
        return False
    
    trades = results.get('trades', [])
    logger.info(f"📊 Total trades: {len(trades)}")
    
    # Analyze trades for pricing issues
    pricing_issues = []
    same_day_exits = []
    
    for i, trade in enumerate(trades):
        if trade['action'] == 'SELL':
            # Find the corresponding BUY trade
            buy_trade = None
            for j in range(i-1, -1, -1):
                if trades[j]['symbol'] == trade['symbol'] and trades[j]['action'] == 'BUY':
                    buy_trade = trades[j]
                    break
            
            if buy_trade:
                # Check for same-day exit
                if buy_trade['date'] == trade['date']:
                    same_day_exits.append({
                        'symbol': trade['symbol'],
                        'buy_date': buy_trade['date'],
                        'sell_date': trade['date'],
                        'buy_price': buy_trade['price'],
                        'sell_price': trade['price']
                    })
                
                # Check for identical prices
                if abs(buy_trade['price'] - trade['price']) < 0.01:  # Within 1 cent
                    pricing_issues.append({
                        'symbol': trade['symbol'],
                        'buy_date': buy_trade['date'],
                        'sell_date': trade['date'],
                        'buy_price': buy_trade['price'],
                        'sell_price': trade['price'],
                        'pnl': trade.get('pnl', 0)
                    })
    
    # Report results
    logger.info(f"🔍 Analysis Results:")
    logger.info(f"   Total trades: {len(trades)}")
    logger.info(f"   Same-day exits: {len(same_day_exits)}")
    logger.info(f"   Identical prices: {len(pricing_issues)}")
    
    if same_day_exits:
        logger.warning("⚠️  Found same-day exits:")
        for issue in same_day_exits[:5]:  # Show first 5
            logger.warning(f"   {issue['symbol']}: BUY {issue['buy_date']} @ ${issue['buy_price']:.2f}, SELL {issue['sell_date']} @ ${issue['sell_price']:.2f}")
    
    if pricing_issues:
        logger.error("❌ Found trades with identical buy/sell prices:")
        for issue in pricing_issues[:5]:  # Show first 5
            logger.error(f"   {issue['symbol']}: BUY @ ${issue['buy_price']:.2f}, SELL @ ${issue['sell_price']:.2f}, P&L: ${issue['pnl']:.2f}")
    
    # Check for realistic P&L values
    sell_trades = [t for t in trades if t['action'] == 'SELL']
    realistic_pnl_count = sum(1 for t in sell_trades if abs(t.get('pnl', 0)) > 0.01)
    
    logger.info(f"   Trades with realistic P&L: {realistic_pnl_count}/{len(sell_trades)}")
    
    # Success criteria
    success = len(same_day_exits) == 0 and len(pricing_issues) == 0
    
    if success:
        logger.info("✅ Pricing fix is working correctly!")
        logger.info("   ✅ No same-day exits")
        logger.info("   ✅ No identical buy/sell prices")
        logger.info("   ✅ Buy and sell prices are different")
    else:
        logger.error("❌ Pricing issues still exist")
    
    return success

if __name__ == "__main__":
    success = test_pricing_fix()
    sys.exit(0 if success else 1) 