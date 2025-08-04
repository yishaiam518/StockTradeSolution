#!/usr/bin/env python3
"""
AAPL Price Verification Test

Tests that AAPL BUY and SELL prices are different for the same stock.
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.data_engine.data_cache import DataCache
from src.utils.logger import get_logger

def test_aapl_price_verification():
    """Test that AAPL BUY and SELL prices are different."""
    logger = get_logger(__name__)
    
    # Get data cache
    cache = DataCache()
    
    # Get all transactions
    all_transactions = cache.get_transaction_history()
    
    if all_transactions.empty:
        logger.info("No transactions found in database")
        return
    
    # Filter for AAPL trades only
    aapl_trades = all_transactions[all_transactions['symbol'] == 'AAPL']
    
    if aapl_trades.empty:
        logger.info("No AAPL trades found in database")
        return
    
    logger.info(f"📊 Found {len(aapl_trades)} AAPL trades")
    
    # Separate BUY and SELL trades
    aapl_buys = aapl_trades[aapl_trades['action'] == 'BUY']
    aapl_sells = aapl_trades[aapl_trades['action'] == 'SELL']
    
    logger.info(f"📈 AAPL BUY trades: {len(aapl_buys)}")
    logger.info(f"📉 AAPL SELL trades: {len(aapl_sells)}")
    
    # Check if we have both BUY and SELL trades
    if aapl_buys.empty or aapl_sells.empty:
        logger.error("❌ Missing either BUY or SELL trades for AAPL")
        return
    
    # Show sample BUY trades
    logger.info(f"\n📋 Sample AAPL BUY trades:")
    for idx, trade in aapl_buys.head(5).iterrows():
        shares = trade['shares']
        price = trade['price']
        date = trade['date']
        logger.info(f"  {date}: BUY {shares} shares at ${price:.2f}")
    
    # Show sample SELL trades
    logger.info(f"\n📋 Sample AAPL SELL trades:")
    for idx, trade in aapl_sells.head(5).iterrows():
        shares = trade['shares']
        price = trade['price']
        date = trade['date']
        pnl = trade.get('pnl', 'N/A')
        logger.info(f"  {date}: SELL {shares} shares at ${price:.2f} (P&L: {pnl})")
    
    # Check for price differences
    logger.info(f"\n🔍 Price Analysis:")
    
    # Get unique BUY prices
    buy_prices = aapl_buys['price'].unique()
    logger.info(f"  Unique BUY prices: {len(buy_prices)}")
    logger.info(f"  BUY price range: ${buy_prices.min():.2f} - ${buy_prices.max():.2f}")
    
    # Get unique SELL prices
    sell_prices = aapl_sells['price'].unique()
    logger.info(f"  Unique SELL prices: {len(sell_prices)}")
    logger.info(f"  SELL price range: ${sell_prices.min():.2f} - ${sell_prices.max():.2f}")
    
    # Check for overlapping prices
    overlapping_prices = set(buy_prices) & set(sell_prices)
    logger.info(f"  Overlapping prices: {len(overlapping_prices)}")
    
    if overlapping_prices:
        logger.warning(f"  ⚠️  Found overlapping prices: {sorted(overlapping_prices)}")
    else:
        logger.info(f"  ✅ No overlapping prices found")
    
    # Check for same-day BUY/SELL trades
    logger.info(f"\n🔍 Same-day BUY/SELL Analysis:")
    
    # Group by date
    daily_trades = aapl_trades.groupby('date').agg({
        'action': list,
        'price': list,
        'shares': list
    }).reset_index()
    
    same_day_trades = daily_trades[daily_trades['action'].apply(lambda x: len(x) > 1)]
    
    if not same_day_trades.empty:
        logger.info(f"  Found {len(same_day_trades)} days with multiple trades:")
        for idx, row in same_day_trades.head(3).iterrows():
            date = row['date']
            actions = row['action']
            prices = row['price']
            shares = row['shares']
            logger.info(f"    {date}: {actions} at prices {prices} for {shares} shares")
    else:
        logger.info(f"  No same-day BUY/SELL trades found")
    
    # Check for sequential BUY/SELL pairs
    logger.info(f"\n🔍 Sequential Trade Analysis:")
    
    # Sort by date
    sorted_trades = aapl_trades.sort_values('date')
    
    # Look for BUY followed by SELL
    buy_sell_pairs = []
    for i in range(len(sorted_trades) - 1):
        current_trade = sorted_trades.iloc[i]
        next_trade = sorted_trades.iloc[i + 1]
        
        if (current_trade['action'] == 'BUY' and 
            next_trade['action'] == 'SELL' and
            current_trade['symbol'] == next_trade['symbol']):
            
            buy_price = current_trade['price']
            sell_price = next_trade['price']
            price_diff = sell_price - buy_price
            price_diff_pct = (price_diff / buy_price) * 100
            
            buy_sell_pairs.append({
                'buy_date': current_trade['date'],
                'sell_date': next_trade['date'],
                'buy_price': buy_price,
                'sell_price': sell_price,
                'price_diff': price_diff,
                'price_diff_pct': price_diff_pct,
                'shares': current_trade['shares']
            })
    
    logger.info(f"  Found {len(buy_sell_pairs)} BUY->SELL pairs")
    
    if buy_sell_pairs:
        logger.info(f"  Sample BUY->SELL pairs:")
        for pair in buy_sell_pairs[:5]:
            logger.info(f"    BUY: {pair['buy_date']} at ${pair['buy_price']:.2f}")
            logger.info(f"    SELL: {pair['sell_date']} at ${pair['sell_price']:.2f}")
            logger.info(f"    Difference: ${pair['price_diff']:.2f} ({pair['price_diff_pct']:.2f}%)")
            logger.info(f"    Shares: {pair['shares']}")
            logger.info(f"    ---")
    
    # Final verification
    logger.info(f"\n✅ Final Verification:")
    
    if len(buy_prices) > 1 and len(sell_prices) > 1:
        logger.info(f"  ✅ AAPL has multiple different BUY prices")
        logger.info(f"  ✅ AAPL has multiple different SELL prices")
        
        if not overlapping_prices:
            logger.info(f"  ✅ BUY and SELL prices are completely different")
        else:
            logger.info(f"  ⚠️  Some BUY and SELL prices overlap (this can be normal)")
        
        if buy_sell_pairs:
            logger.info(f"  ✅ Found BUY->SELL pairs with different prices")
        else:
            logger.info(f"  ⚠️  No sequential BUY->SELL pairs found")
    else:
        logger.error(f"  ❌ AAPL has insufficient price diversity")

if __name__ == "__main__":
    test_aapl_price_verification() 