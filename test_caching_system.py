#!/usr/bin/env python3
"""
Test Caching System

Demonstrates the local database caching system for stock data and transaction logging.
"""

import sys
import os
import time
from datetime import datetime, timedelta
import pandas as pd

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.backtesting.backtest_engine import BacktestEngine
from src.data_engine.data_cache import DataCache
from src.utils.logger import get_logger

def test_caching_system():
    """Test the caching system with performance comparison."""
    
    logger = get_logger(__name__)
    logger.info("🧪 Testing Caching System")
    
    # Initialize components
    cache = DataCache()
    backtest_engine = BacktestEngine()
    
    # Test parameters
    strategy = "MACD"
    profile = "moderate"
    start_date = "2023-01-01"
    end_date = "2023-12-31"
    
    logger.info(f"Testing with {strategy}_{profile} from {start_date} to {end_date}")
    
    # First run - should fetch data and cache it
    logger.info("🔄 First run - fetching and caching data...")
    start_time = time.time()
    
    results1 = backtest_engine.run_historical_backtest(
        strategy=strategy,
        profile=profile,
        start_date=start_date,
        end_date=end_date
    )
    
    first_run_time = time.time() - start_time
    logger.info(f"✅ First run completed in {first_run_time:.2f} seconds")
    
    # Second run - should use cached data
    logger.info("🔄 Second run - using cached data...")
    start_time = time.time()
    
    results2 = backtest_engine.run_historical_backtest(
        strategy=strategy,
        profile=profile,
        start_date=start_date,
        end_date=end_date
    )
    
    second_run_time = time.time() - start_time
    logger.info(f"✅ Second run completed in {second_run_time:.2f} seconds")
    
    # Performance comparison
    speedup = first_run_time / second_run_time if second_run_time > 0 else 0
    logger.info(f"🚀 Performance improvement: {speedup:.1f}x faster with caching")
    
    # Show cache statistics
    cache_stats = cache.get_cache_stats()
    logger.info("📊 Cache Statistics:")
    for key, value in cache_stats.items():
        logger.info(f"   {key}: {value}")
    
    # Show transaction history
    logger.info("📈 Transaction History:")
    if 'backtest_id' in results1:
        transactions = cache.get_transaction_history(backtest_id=results1['backtest_id'])
        if not transactions.empty:
            logger.info(f"   Total transactions: {len(transactions)}")
            
            # Show P&L summary
            buy_trades = transactions[transactions['action'] == 'BUY']
            sell_trades = transactions[transactions['action'] == 'SELL']
            
            logger.info(f"   BUY trades: {len(buy_trades)}")
            logger.info(f"   SELL trades: {len(sell_trades)}")
            
            # Show some sample transactions
            if not sell_trades.empty:
                logger.info("   Sample SELL transactions with P&L:")
                sample_sells = sell_trades.head(5)
                for _, trade in sample_sells.iterrows():
                    pnl = trade.get('pnl', 0)
                    pnl_percent = trade.get('pnl_percent', 0)
                    logger.info(f"     {trade['symbol']}: ${pnl:.2f} ({pnl_percent:.2f}%)")
    
    # Show backtest history
    logger.info("📋 Backtest History:")
    backtest_history = cache.get_backtest_history()
    if not backtest_history.empty:
        logger.info(f"   Total backtests: {len(backtest_history)}")
        logger.info("   Recent backtests:")
        recent_backtests = backtest_history.head(3)
        for _, backtest in recent_backtests.iterrows():
            logger.info(f"     {backtest['backtest_id']}: {backtest['strategy']}_{backtest['profile']}")
            logger.info(f"       Return: {backtest['total_return']:.2f}%")
            logger.info(f"       Trades: {backtest['total_trades']}")
    
    return {
        'first_run_time': first_run_time,
        'second_run_time': second_run_time,
        'speedup': speedup,
        'cache_stats': cache_stats,
        'results1': results1,
        'results2': results2
    }

def test_transaction_analysis():
    """Test transaction analysis capabilities."""
    
    logger = get_logger(__name__)
    logger.info("📊 Testing Transaction Analysis")
    
    cache = DataCache()
    
    # Get all transactions
    all_transactions = cache.get_transaction_history()
    
    if all_transactions.empty:
        logger.info("No transactions found in database")
        return
    
    logger.info(f"📈 Total transactions in database: {len(all_transactions)}")
    
    # Check which columns exist
    available_columns = all_transactions.columns.tolist()
    logger.info(f"Available columns: {available_columns}")
    
    # Analyze by symbol
    agg_dict = {'action': 'count'}
    
    # Add P&L columns if they exist
    if 'pnl' in available_columns:
        agg_dict['pnl'] = ['sum', 'mean']
    if 'pnl_percent' in available_columns:
        agg_dict['pnl_percent'] = 'mean'
    
    symbol_stats = all_transactions.groupby('symbol').agg(agg_dict).round(2)
    
    logger.info("📊 Symbol Performance Summary:")
    for symbol in symbol_stats.index:
        # Handle different aggregation structures
        if isinstance(symbol_stats.columns, pd.MultiIndex):
            total_trades = symbol_stats.loc[symbol, ('action', 'count')]
        else:
            total_trades = symbol_stats.loc[symbol, 'action']
        
        if 'pnl' in available_columns:
            if isinstance(symbol_stats.columns, pd.MultiIndex):
                total_pnl = symbol_stats.loc[symbol, ('pnl', 'sum')]
                avg_pnl = symbol_stats.loc[symbol, ('pnl', 'mean')]
                avg_pnl_percent = symbol_stats.loc[symbol, ('pnl_percent', 'mean')] if 'pnl_percent' in available_columns else 0
            else:
                total_pnl = symbol_stats.loc[symbol, 'pnl']
                avg_pnl = symbol_stats.loc[symbol, 'pnl']
                avg_pnl_percent = symbol_stats.loc[symbol, 'pnl_percent'] if 'pnl_percent' in available_columns else 0
            logger.info(f"   {symbol}: {total_trades} trades, ${total_pnl:.2f} total P&L, {avg_pnl_percent:.2f}% avg")
        else:
            logger.info(f"   {symbol}: {total_trades} trades")
    
    # Analyze by strategy
    strategy_stats = all_transactions.groupby('strategy').agg(agg_dict).round(2)
    
    logger.info("📊 Strategy Performance Summary:")
    for strategy in strategy_stats.index:
        # Handle different aggregation structures
        if isinstance(strategy_stats.columns, pd.MultiIndex):
            total_trades = strategy_stats.loc[strategy, ('action', 'count')]
        else:
            total_trades = strategy_stats.loc[strategy, 'action']
        
        if 'pnl' in available_columns:
            if isinstance(strategy_stats.columns, pd.MultiIndex):
                total_pnl = strategy_stats.loc[strategy, ('pnl', 'sum')]
                avg_pnl = strategy_stats.loc[strategy, ('pnl', 'mean')]
                avg_pnl_percent = strategy_stats.loc[strategy, ('pnl_percent', 'mean')] if 'pnl_percent' in available_columns else 0
            else:
                total_pnl = strategy_stats.loc[strategy, 'pnl']
                avg_pnl = strategy_stats.loc[strategy, 'pnl']
                avg_pnl_percent = strategy_stats.loc[strategy, 'pnl_percent'] if 'pnl_percent' in available_columns else 0
            logger.info(f"   {strategy}: {total_trades} trades, ${total_pnl:.2f} total P&L, {avg_pnl_percent:.2f}% avg")
        else:
            logger.info(f"   {strategy}: {total_trades} trades")
    
    # Show action distribution
    action_dist = all_transactions['action'].value_counts()
    logger.info("📊 Action Distribution:")
    for action, count in action_dist.items():
        logger.info(f"   {action}: {count} trades")
    
    # Show recent transactions
    logger.info("📊 Recent Transactions:")
    recent_transactions = all_transactions.head(10)
    for _, transaction in recent_transactions.iterrows():
        logger.info(f"   {transaction['date']} - {transaction['action']} {transaction['symbol']} at ${transaction['price']:.2f}")

if __name__ == "__main__":
    print("🧪 Testing StockTradeSolution Caching System")
    print("=" * 50)
    
    # Test caching performance
    results = test_caching_system()
    
    print("\n" + "=" * 50)
    
    # Test transaction analysis
    test_transaction_analysis()
    
    print("\n✅ Caching system test completed!")
    print(f"🚀 Performance improvement: {results['speedup']:.1f}x faster with caching") 