#!/usr/bin/env python3
"""
Trade Analysis Script

Analyzes all trades from the backtest and shows detailed P&L information.
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.data_engine.data_cache import DataCache
from src.utils.logger import get_logger

def analyze_trades():
    """Analyze all trades and show detailed P&L information."""
    logger = get_logger(__name__)
    
    # Get data cache
    cache = DataCache()
    
    # Get all transactions
    all_transactions = cache.get_transaction_history()
    
    if all_transactions.empty:
        logger.info("No transactions found in database")
        return
    
    logger.info(f"📊 Total transactions in database: {len(all_transactions)}")
    
    # Filter for meaningful trades (shares > 0)
    meaningful_trades = all_transactions[all_transactions['shares'] > 0]
    logger.info(f"📈 Meaningful trades (shares > 0): {len(meaningful_trades)}")
    
    # Filter for a specific stock (AAPL) - meaningful trades only
    aapl_trades = meaningful_trades[meaningful_trades['symbol'] == 'AAPL']
    
    if not aapl_trades.empty:
        logger.info(f"\n🍎 AAPL Trade Analysis (Meaningful Trades Only):")
        logger.info(f"Total AAPL meaningful trades: {len(aapl_trades)}")
        
        # Show first 10 AAPL trades
        logger.info(f"\n📋 First 10 AAPL trades:")
        for idx, trade in aapl_trades.head(10).iterrows():
            action = trade['action']
            shares = trade['shares']
            price = trade['price']
            date = trade['date']
            reason = trade.get('reason', 'N/A')
            
            if action == 'BUY':
                logger.info(f"📈 {date}: BUY {shares:.2f} shares at ${price:.2f} - {reason}")
            else:
                pnl = trade.get('pnl', 0)
                pnl_pct = trade.get('pnl_percent', 0)
                logger.info(f"📉 {date}: SELL {shares:.2f} shares at ${price:.2f} - P&L: ${pnl:.2f} ({pnl_pct:.2f}%) - {reason}")
        
        # Show last 10 AAPL trades
        logger.info(f"\n📋 Last 10 AAPL trades:")
        for idx, trade in aapl_trades.tail(10).iterrows():
            action = trade['action']
            shares = trade['shares']
            price = trade['price']
            date = trade['date']
            reason = trade.get('reason', 'N/A')
            
            if action == 'BUY':
                logger.info(f"📈 {date}: BUY {shares:.2f} shares at ${price:.2f} - {reason}")
            else:
                pnl = trade.get('pnl', 0)
                pnl_pct = trade.get('pnl_percent', 0)
                logger.info(f"📉 {date}: SELL {shares:.2f} shares at ${price:.2f} - P&L: ${pnl:.2f} ({pnl_pct:.2f}%) - {reason}")
    
    # Overall summary - meaningful trades only
    logger.info(f"\n📋 Overall Trade Summary (Meaningful Trades Only):")
    
    # Count by action
    buy_trades = meaningful_trades[meaningful_trades['action'] == 'BUY']
    sell_trades = meaningful_trades[meaningful_trades['action'] == 'SELL']
    
    logger.info(f"Total BUY trades: {len(buy_trades)}")
    logger.info(f"Total SELL trades: {len(sell_trades)}")
    
    # Calculate total P&L if column exists
    if 'pnl' in meaningful_trades.columns:
        total_pnl = meaningful_trades['pnl'].sum()
        avg_pnl = meaningful_trades['pnl'].mean()
        logger.info(f"Total P&L: ${total_pnl:.2f}")
        logger.info(f"Average P&L per trade: ${avg_pnl:.2f}")
    else:
        logger.info("⚠️  P&L column not found in transactions")
    
    # Show trades by symbol (meaningful only)
    symbol_counts = meaningful_trades['symbol'].value_counts()
    logger.info(f"\n📈 Trades by Symbol (Meaningful Only):")
    for symbol, count in symbol_counts.head(10).items():
        logger.info(f"  {symbol}: {count} trades")
    
    # Check for issues
    logger.info(f"\n🔍 Issues Found:")
    
    # Check for 0.00 share trades
    zero_share_trades = all_transactions[all_transactions['shares'] == 0]
    logger.info(f"  ❌ Zero share trades: {len(zero_share_trades)}")
    
    # Check for same buy/sell prices if pnl column exists
    if 'pnl' in meaningful_trades.columns and not sell_trades.empty:
        same_price_trades = sell_trades[sell_trades['pnl'] == 0]
        logger.info(f"  ❌ SELL trades with $0.00 P&L: {len(same_price_trades)}")
        
        # Check for different prices
        different_price_trades = sell_trades[sell_trades['pnl'] != 0]
        logger.info(f"  ✅ SELL trades with different prices: {len(different_price_trades)}")
    else:
        logger.info(f"  ⚠️  Cannot check P&L - column missing or no SELL trades")
    
    # Show some sample trades to verify logic
    logger.info(f"\n🔍 Sample Trade Analysis:")
    
    # Show a few BUY and SELL trades for comparison
    sample_buys = buy_trades.head(3)
    sample_sells = sell_trades.head(3)
    
    logger.info(f"Sample BUY trades:")
    for idx, trade in sample_buys.iterrows():
        logger.info(f"  {trade['date']}: BUY {trade['shares']:.2f} {trade['symbol']} at ${trade['price']:.2f}")
    
    logger.info(f"Sample SELL trades:")
    for idx, trade in sample_sells.iterrows():
        pnl = trade.get('pnl', 'N/A')
        logger.info(f"  {trade['date']}: SELL {trade['shares']:.2f} {trade['symbol']} at ${trade['price']:.2f} (P&L: {pnl})")

if __name__ == "__main__":
    analyze_trades() 