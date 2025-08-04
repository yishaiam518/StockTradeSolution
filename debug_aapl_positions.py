#!/usr/bin/env python3
"""
Debug AAPL Position Tracking

Debug why AAPL positions aren't being sold in the backtest.
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.data_engine.data_cache import DataCache
from src.utils.logger import get_logger
from src.backtesting.backtest_engine import BacktestEngine

def debug_aapl_positions():
    """Debug AAPL position tracking."""
    logger = get_logger(__name__)
    
    # Initialize backtest engine
    engine = BacktestEngine()
    
    # Run a focused backtest on AAPL only
    logger.info("🔍 Running focused AAPL backtest...")
    
    # Get AAPL data
    aapl_data = engine._get_cached_or_fetch_data('AAPL', '2023-01-01', '2023-12-31')
    
    if aapl_data is None or aapl_data.empty:
        logger.error("❌ Could not get AAPL data")
        return
    
    logger.info(f"✅ AAPL data loaded: {len(aapl_data)} rows")
    
    # Run simulation on AAPL only
    stock_data = {'AAPL': aapl_data}
    
    # Add debug logging to the backtest engine
    original_run_progressive = engine._run_progressive_simulation
    
    def debug_run_progressive_simulation(*args, **kwargs):
        """Debug version of progressive simulation with extra logging."""
        logger.info("🔍 Starting debug progressive simulation...")
        
        # Call the original method
        result = original_run_progressive(*args, **kwargs)
        
        if result['success']:
            trades = result['trades']
            aapl_trades = [t for t in trades if t['symbol'] == 'AAPL']
            aapl_buys = [t for t in aapl_trades if t['action'] == 'BUY']
            aapl_sells = [t for t in aapl_trades if t['action'] == 'SELL']
            
            logger.info(f"🔍 DEBUG RESULTS:")
            logger.info(f"  Total AAPL trades: {len(aapl_trades)}")
            logger.info(f"  AAPL BUY trades: {len(aapl_buys)}")
            logger.info(f"  AAPL SELL trades: {len(aapl_sells)}")
            
            if len(aapl_buys) > len(aapl_sells):
                logger.error(f"❌ ISSUE FOUND: {len(aapl_buys) - len(aapl_sells)} AAPL positions were never sold!")
                
                # Show the last few BUY trades to see if positions were created
                if aapl_buys:
                    logger.info(f"📋 Last 3 AAPL BUY trades:")
                    for trade in aapl_buys[-3:]:
                        logger.info(f"  {trade['date']}: BUY {trade['shares']} shares at ${trade['price']:.2f}")
        
        return result
    
    # Replace the method temporarily
    engine._run_progressive_simulation = debug_run_progressive_simulation
    
    # Run progressive simulation
    result = engine._run_progressive_simulation(
        stock_data=stock_data,
        strategy='MACDStrategy',
        profile='moderate',
        start_date='2023-01-01',
        end_date='2023-12-31',
        backtest_id='debug_aapl'
    )
    
    # Restore original method
    engine._run_progressive_simulation = original_run_progressive
    
    if result['success']:
        trades = result['trades']
        logger.info(f"✅ Backtest completed successfully")
        logger.info(f"📊 Total trades: {len(trades)}")
        
        # Filter AAPL trades
        aapl_trades = [t for t in trades if t['symbol'] == 'AAPL']
        logger.info(f"📈 AAPL trades: {len(aapl_trades)}")
        
        # Separate BUY and SELL
        aapl_buys = [t for t in aapl_trades if t['action'] == 'BUY']
        aapl_sells = [t for t in aapl_trades if t['action'] == 'SELL']
        
        logger.info(f"📈 AAPL BUY trades: {len(aapl_buys)}")
        logger.info(f"📉 AAPL SELL trades: {len(aapl_sells)}")
        
        # Show sample trades
        if aapl_buys:
            logger.info(f"📋 Sample AAPL BUY trades:")
            for trade in aapl_buys[:3]:
                logger.info(f"  {trade['date']}: BUY {trade['shares']} shares at ${trade['price']:.2f}")
        
        if aapl_sells:
            logger.info(f"📋 Sample AAPL SELL trades:")
            for trade in aapl_sells[:3]:
                logger.info(f"  {trade['date']}: SELL {trade['shares']} shares at ${trade['price']:.2f} (P&L: ${trade['pnl']:.2f})")
        
        # Check if we have positions that should have been sold
        if len(aapl_buys) > len(aapl_sells):
            logger.warning(f"⚠️  AAPL has {len(aapl_buys)} BUY trades but only {len(aapl_sells)} SELL trades")
            logger.warning(f"   This means {len(aapl_buys) - len(aapl_sells)} positions were never sold")
        
        # Check final portfolio value
        final_value = result['final_portfolio_value']
        logger.info(f"💰 Final portfolio value: ${final_value:.2f}")
        
    else:
        logger.error("❌ Backtest failed")
        logger.error(f"Error: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    debug_aapl_positions() 