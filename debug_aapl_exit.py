#!/usr/bin/env python3
"""
Debug AAPL Exit Logic

Investigates why AAPL positions aren't being sold.
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.data_engine.data_cache import DataCache
from src.utils.logger import get_logger
from src.trading_system import TradingSystem
from src.strategies.macd_strategy import MACDStrategy

def debug_aapl_exit():
    """Debug why AAPL positions aren't being sold."""
    logger = get_logger(__name__)
    
    # Get data cache
    cache = DataCache()
    
    # Get all transactions
    all_transactions = cache.get_transaction_history()
    
    # Filter for AAPL trades only
    aapl_trades = all_transactions[all_transactions['symbol'] == 'AAPL']
    
    logger.info(f"📊 AAPL trades found: {len(aapl_trades)}")
    
    # Check if AAPL has any SELL trades
    aapl_sells = aapl_trades[aapl_trades['action'] == 'SELL']
    logger.info(f"📉 AAPL SELL trades: {len(aapl_sells)}")
    
    if len(aapl_sells) == 0:
        logger.error("❌ AAPL has NO SELL trades - exit logic is not working!")
        
        # Check what other stocks have SELL trades
        all_sells = all_transactions[all_transactions['action'] == 'SELL']
        logger.info(f"📉 Total SELL trades in database: {len(all_sells)}")
        
        if not all_sells.empty:
            sell_symbols = all_sells['symbol'].value_counts()
            logger.info(f"📈 Stocks with SELL trades:")
            for symbol, count in sell_symbols.head(10).items():
                logger.info(f"  {symbol}: {count} SELL trades")
        
        # Check if AAPL has BUY trades
        aapl_buys = aapl_trades[aapl_trades['action'] == 'BUY']
        logger.info(f"📈 AAPL BUY trades: {len(aapl_buys)}")
        
        if len(aapl_buys) > 0:
            logger.info(f"📋 Sample AAPL BUY trades:")
            for idx, trade in aapl_buys.head(5).iterrows():
                shares = trade['shares']
                price = trade['price']
                date = trade['date']
                logger.info(f"  {date}: BUY {shares} shares at ${price:.2f}")
        
        # Test the strategy directly
        logger.info(f"\n🔍 Testing AAPL Strategy Directly:")
        
        try:
            # Initialize trading system
            trading_system = TradingSystem()
            
            # Get AAPL data
            aapl_data = trading_system.prepare_data('AAPL', '2023-01-01', '2023-12-31')
            
            if aapl_data is not None and not aapl_data.empty:
                logger.info(f"✅ AAPL data loaded: {len(aapl_data)} rows")
                
                # Create strategy instance directly
                strategy = MACDStrategy(profile="moderate")
                
                # Test entry signals
                logger.info(f"🔍 Testing entry signals for AAPL:")
                entry_signals = 0
                for i in range(len(aapl_data)):
                    should_entry, reason = strategy.should_entry(aapl_data, i)
                    if should_entry:
                        entry_signals += 1
                        if entry_signals <= 3:  # Show first 3
                            logger.info(f"  Entry signal at index {i}: {reason.get('summary', 'N/A')}")
                
                logger.info(f"  Total entry signals: {entry_signals}")
                
                # Test exit signals (simulate a position)
                logger.info(f"🔍 Testing exit signals for AAPL:")
                exit_signals = 0
                
                # Use a sample entry price and date
                sample_entry_price = 191.13
                sample_entry_date = '2023-04-12'
                
                for i in range(len(aapl_data)):
                    should_exit, reason = strategy.should_exit(aapl_data, i, sample_entry_price, sample_entry_date)
                    if should_exit:
                        exit_signals += 1
                        if exit_signals <= 3:  # Show first 3
                            logger.info(f"  Exit signal at index {i}: {reason.get('summary', 'N/A')}")
                
                logger.info(f"  Total exit signals: {exit_signals}")
                
                if exit_signals == 0:
                    logger.error("❌ No exit signals generated for AAPL!")
                    logger.error("  This explains why AAPL positions are never sold.")
                    
                    # Check the exit conditions
                    logger.info(f"🔍 Checking exit conditions:")
                    logger.info(f"  Take profit: {strategy.exit_conditions.get('take_profit_pct', 'N/A')}%")
                    logger.info(f"  Stop loss: {strategy.exit_conditions.get('stop_loss_pct', 'N/A')}%")
                    logger.info(f"  Max hold days: {strategy.exit_conditions.get('max_hold_days', 'N/A')}")
                    logger.info(f"  Max drawdown: {strategy.exit_conditions.get('max_drawdown_pct', 'N/A')}%")
                    
                    # Test with different entry prices
                    logger.info(f"🔍 Testing with different entry prices:")
                    test_prices = [150.0, 180.0, 200.0, 220.0]
                    for test_price in test_prices:
                        exit_count = 0
                        for i in range(len(aapl_data)):
                            should_exit, reason = strategy.should_exit(aapl_data, i, test_price, sample_entry_date)
                            if should_exit:
                                exit_count += 1
                        logger.info(f"  Entry price ${test_price}: {exit_count} exit signals")
                    
                else:
                    logger.info("✅ Exit signals are being generated for AAPL")
                    logger.info("  The issue might be in the backtest engine logic.")
                
            else:
                logger.error("❌ Could not load AAPL data")
                
        except Exception as e:
            logger.error(f"❌ Error testing strategy: {str(e)}")
            import traceback
            traceback.print_exc()
    
    else:
        logger.info("✅ AAPL has SELL trades - exit logic is working")
        
        # Show sample SELL trades
        logger.info(f"📋 Sample AAPL SELL trades:")
        for idx, trade in aapl_sells.head(5).iterrows():
            shares = trade['shares']
            price = trade['price']
            date = trade['date']
            pnl = trade.get('pnl', 'N/A')
            logger.info(f"  {date}: SELL {shares} shares at ${price:.2f} (P&L: {pnl})")

if __name__ == "__main__":
    debug_aapl_exit() 