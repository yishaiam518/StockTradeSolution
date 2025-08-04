#!/usr/bin/env python3
"""
Comprehensive 1-Year Test

Tests the trading system for 1 year and examines:
1. Multiple buy/sell transactions with different prices
2. Portfolio behavior (no unnatural resets)
3. Error and warning logs
4. Detailed reports per stock
"""

import sys
import os
import pandas as pd
from datetime import datetime
import logging

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.backtesting.backtest_engine import BacktestEngine
from src.data_engine.data_cache import DataCache
from src.utils.logger import get_logger

def run_comprehensive_test():
    """Run comprehensive 1-year test."""
    logger = get_logger(__name__)
    
    logger.info("🚀 Starting Comprehensive 1-Year Test")
    logger.info("=" * 60)
    
    # Initialize backtest engine
    engine = BacktestEngine()
    
    # Run 1-year backtest
    start_date = "2023-01-01"
    end_date = "2023-12-31"
    
    logger.info(f"📅 Test Period: {start_date} to {end_date}")
    logger.info("🔄 Running historical backtest...")
    
    # Capture logs for error analysis
    log_capture = []
    
    try:
        # Run the backtest
        results = engine.run_historical_backtest(
            strategy="MACDStrategy",
            profile="moderate",
            start_date=start_date,
            end_date=end_date
        )
        
        logger.info("✅ Backtest completed successfully")
        
        # Get transaction data
        cache = DataCache()
        all_transactions = cache.get_transaction_history()
        
        if all_transactions.empty:
            logger.error("❌ No transactions found in database")
            return
        
        # Analyze results
        analyze_results(all_transactions, results, logger)
        
    except Exception as e:
        logger.error(f"❌ Backtest failed: {e}")
        return

def analyze_results(transactions, results, logger):
    """Analyze the backtest results comprehensively."""
    
    logger.info("\n📊 COMPREHENSIVE ANALYSIS")
    logger.info("=" * 60)
    
    # 1. Check for different buy/sell prices
    check_price_differences(transactions, logger)
    
    # 2. Check portfolio behavior
    check_portfolio_behavior(results, logger)
    
    # 3. Check for errors and warnings
    check_errors_and_warnings(logger)
    
    # 4. Generate detailed stock reports
    generate_stock_reports(transactions, logger)
    
    # 5. Overall summary
    generate_overall_summary(transactions, results, logger)

def check_price_differences(transactions, logger):
    """Check that buy and sell prices are different for the same stock."""
    logger.info("\n🔍 1. PRICE DIFFERENCE ANALYSIS")
    logger.info("-" * 40)
    
    # Group by symbol
    for symbol in transactions['symbol'].unique():
        symbol_trades = transactions[transactions['symbol'] == symbol]
        
        buy_prices = symbol_trades[symbol_trades['action'] == 'BUY']['price'].unique()
        sell_prices = symbol_trades[symbol_trades['action'] == 'SELL']['price'].unique()
        
        logger.info(f"\n📈 {symbol}:")
        logger.info(f"   BUY prices: {len(buy_prices)} unique prices")
        logger.info(f"   SELL prices: {len(sell_prices)} unique prices")
        
        # Check for price overlap
        price_overlap = set(buy_prices) & set(sell_prices)
        if price_overlap:
            logger.warning(f"   ⚠️  Price overlap: {len(price_overlap)} prices used for both BUY and SELL")
        else:
            logger.info(f"   ✅ No price overlap - different BUY/SELL prices")
        
        # Show sample prices
        if len(buy_prices) > 0:
            logger.info(f"   Sample BUY prices: {sorted(buy_prices)[:5]}")
        if len(sell_prices) > 0:
            logger.info(f"   Sample SELL prices: {sorted(sell_prices)[:5]}")

def check_portfolio_behavior(results, logger):
    """Check that portfolio doesn't reset to 0 unnaturally."""
    logger.info("\n💰 2. PORTFOLIO BEHAVIOR ANALYSIS")
    logger.info("-" * 40)
    
    if 'portfolio_values' in results:
        portfolio_values = results['portfolio_values']
        
        # Check for sudden drops to 0
        zero_count = sum(1 for pv in portfolio_values if pv['value'] == 0)
        logger.info(f"Portfolio value = 0 on {zero_count} days")
        
        if zero_count > 0:
            logger.warning("⚠️  Portfolio reset to 0 detected - may be natural depletion")
        else:
            logger.info("✅ No unnatural portfolio resets to 0")
        
        # Show portfolio progression
        if len(portfolio_values) > 0:
            initial_value = portfolio_values[0]['value']
            final_value = portfolio_values[-1]['value']
            logger.info(f"Initial portfolio: ${initial_value:,.2f}")
            logger.info(f"Final portfolio: ${final_value:,.2f}")
            logger.info(f"Total change: ${final_value - initial_value:,.2f}")

def check_errors_and_warnings(logger):
    """Check for errors and warnings in the logs."""
    logger.info("\n⚠️  3. ERROR AND WARNING ANALYSIS")
    logger.info("-" * 40)
    
    # Check log files for errors
    log_files = ['logs/trading_system.log', 'logs/complete_backtest_results.log']
    
    for log_file in log_files:
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as f:
                    log_content = f.read()
                
                error_count = log_content.count('ERROR')
                warning_count = log_content.count('WARNING')
                
                logger.info(f"📄 {log_file}:")
                logger.info(f"   Errors: {error_count}")
                logger.info(f"   Warnings: {warning_count}")
                
                if error_count > 0:
                    logger.error(f"   ❌ Found {error_count} errors!")
                if warning_count > 0:
                    logger.warning(f"   ⚠️  Found {warning_count} warnings!")
                
            except Exception as e:
                logger.error(f"   ❌ Could not read {log_file}: {e}")
        else:
            logger.info(f"📄 {log_file}: File not found")

def generate_stock_reports(transactions, logger):
    """Generate detailed reports per stock."""
    logger.info("\n📊 4. DETAILED STOCK REPORTS")
    logger.info("-" * 40)
    
    # Group by symbol
    for symbol in transactions['symbol'].unique():
        symbol_trades = transactions[transactions['symbol'] == symbol]
        
        buy_trades = symbol_trades[symbol_trades['action'] == 'BUY']
        sell_trades = symbol_trades[symbol_trades['action'] == 'SELL']
        
        # Calculate P&L
        total_pnl = sell_trades['pnl'].sum() if 'pnl' in sell_trades.columns else 0
        
        logger.info(f"\n📈 {symbol} REPORT:")
        logger.info(f"   Total trades: {len(symbol_trades)}")
        logger.info(f"   BUY trades: {len(buy_trades)}")
        logger.info(f"   SELL trades: {len(sell_trades)}")
        logger.info(f"   Positions held: {len(buy_trades) - len(sell_trades)}")
        logger.info(f"   Total P&L: ${total_pnl:.2f}")
        
        # Show trade distribution
        if len(buy_trades) > 0:
            avg_buy_price = buy_trades['price'].mean()
            logger.info(f"   Average BUY price: ${avg_buy_price:.2f}")
        
        if len(sell_trades) > 0:
            avg_sell_price = sell_trades['price'].mean()
            logger.info(f"   Average SELL price: ${avg_sell_price:.2f}")
            
            if 'pnl' in sell_trades.columns:
                profitable_trades = sell_trades[sell_trades['pnl'] > 0]
                losing_trades = sell_trades[sell_trades['pnl'] < 0]
                logger.info(f"   Profitable trades: {len(profitable_trades)}")
                logger.info(f"   Losing trades: {len(losing_trades)}")

def generate_overall_summary(transactions, results, logger):
    """Generate overall summary."""
    logger.info("\n📋 5. OVERALL SUMMARY")
    logger.info("-" * 40)
    
    # Overall statistics
    total_trades = len(transactions)
    buy_trades = len(transactions[transactions['action'] == 'BUY'])
    sell_trades = len(transactions[transactions['action'] == 'SELL'])
    
    logger.info(f"📊 Overall Statistics:")
    logger.info(f"   Total trades: {total_trades}")
    logger.info(f"   BUY trades: {buy_trades}")
    logger.info(f"   SELL trades: {sell_trades}")
    logger.info(f"   Net positions: {buy_trades - sell_trades}")
    
    # Stocks traded
    unique_stocks = transactions['symbol'].nunique()
    logger.info(f"   Stocks traded: {unique_stocks}")
    
    # Total P&L
    if 'pnl' in transactions.columns:
        total_pnl = transactions['pnl'].sum()
        logger.info(f"   Total P&L: ${total_pnl:.2f}")
    
    # Trading frequency
    if 'date' in transactions.columns:
        trading_days = transactions['date'].nunique()
        logger.info(f"   Trading days: {trading_days}")
        logger.info(f"   Average trades per day: {total_trades / trading_days:.2f}")
    
    logger.info("\n✅ Comprehensive test completed!")

if __name__ == "__main__":
    run_comprehensive_test() 