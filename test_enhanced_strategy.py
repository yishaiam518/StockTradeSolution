#!/usr/bin/env python3
"""
Test script for the Enhanced MACD Strategy.
Tests the new strategy with improved entry/exit logic, volume filters, and trend filters.
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.backtesting.backtest_engine import BacktestEngine
from src.utils.logger import get_logger

def test_enhanced_strategy():
    """Test the enhanced MACD strategy with improved filters."""
    logger = get_logger(__name__)
    
    logger.info("🧪 Testing Enhanced MACD Strategy...")
    
    # Initialize backtest engine
    engine = BacktestEngine()
    
    # First test with regular MACD to ensure system works
    logger.info("🔍 Testing regular MACD strategy first...")
    regular_results = engine.run_historical_backtest(
        strategy="MACD",
        profile="balanced", 
        start_date="2023-01-01",
        end_date="2023-12-31",
        benchmark="SPY"
    )
    
    logger.info("📊 Regular MACD Results:")
    logger.info(f"   Total trades: {regular_results.get('total_trades', 0)}")
    logger.info(f"   Final portfolio value: ${regular_results.get('final_portfolio_value', 0):.2f}")
    logger.info(f"   Strategy return: {regular_results.get('strategy_return', 0):.2f}%")
    
    # Now test the enhanced strategy
    logger.info("\n🔍 Testing Enhanced MACD Strategy...")
    enhanced_results = engine.run_historical_backtest(
        strategy="MACD_ENHANCED",
        profile="balanced", 
        start_date="2023-01-01",
        end_date="2023-12-31",
        benchmark="SPY"
    )
    
    # Analyze results
    logger.info("📊 Enhanced Strategy Results:")
    logger.info(f"   Total trades: {enhanced_results.get('total_trades', 0)}")
    logger.info(f"   Final portfolio value: ${enhanced_results.get('final_portfolio_value', 0):.2f}")
    logger.info(f"   Strategy return: {enhanced_results.get('strategy_return', 0):.2f}%")
    logger.info(f"   Benchmark return: {enhanced_results.get('benchmark_return', 0):.2f}%")
    logger.info(f"   Win rate: {enhanced_results.get('win_rate', 0):.2f}%")
    logger.info(f"   Max drawdown: {enhanced_results.get('max_drawdown', 0):.2f}%")
    logger.info(f"   Sharpe ratio: {enhanced_results.get('sharpe_ratio', 0):.2f}")
    
    # Check for enhanced strategy features
    trades = enhanced_results.get('trades', [])
    if trades:
        logger.info(f"\n🔍 Enhanced Strategy Features Analysis:")
        
        # Check for volume filters
        volume_filtered_trades = [t for t in trades if t.get('volume_adequate', True)]
        logger.info(f"   Volume-filtered trades: {len(volume_filtered_trades)}/{len(trades)}")
        
        # Check for volatility filters
        volatility_filtered_trades = [t for t in trades if t.get('volatility_adequate', True)]
        logger.info(f"   Volatility-filtered trades: {len(volatility_filtered_trades)}/{len(trades)}")
        
        # Check for trend strength
        strong_trend_trades = [t for t in trades if t.get('strong_trend', False)]
        logger.info(f"   Strong trend trades: {len(strong_trend_trades)}/{len(trades)}")
        
        # Check holding periods
        min_hold_trades = [t for t in trades if t.get('days_held', 0) >= 5]
        logger.info(f"   Trades held minimum 5 days: {len(min_hold_trades)}/{len(trades)}")
        
        # Check P&L distribution
        profitable_trades = [t for t in trades if t.get('pnl', 0) > 0]
        losing_trades = [t for t in trades if t.get('pnl', 0) < 0]
        logger.info(f"   Profitable trades: {len(profitable_trades)}/{len(trades)}")
        logger.info(f"   Losing trades: {len(losing_trades)}/{len(trades)}")
        
        # Check for different buy/sell prices
        same_price_trades = [t for t in trades if t.get('buy_price') == t.get('sell_price')]
        logger.info(f"   Trades with same buy/sell price: {len(same_price_trades)}/{len(trades)}")
        
        # Check for fractional shares
        fractional_trades = [t for t in trades if isinstance(t.get('shares', 0), float) and t.get('shares', 0) % 1 != 0]
        logger.info(f"   Trades with fractional shares: {len(fractional_trades)}/{len(trades)}")
        
        # Check portfolio value doesn't reach 0
        portfolio_values = enhanced_results.get('portfolio_values', [])
        min_portfolio = min([pv.get('value', 0) for pv in portfolio_values]) if portfolio_values else 0
        logger.info(f"   Minimum portfolio value: ${min_portfolio:.2f}")
        
        # Check position sizing (no more than 2% per position)
        large_positions = [t for t in trades if t.get('value', 0) > enhanced_results.get('initial_capital', 100000) * 0.02]
        logger.info(f"   Positions > 2% of portfolio: {len(large_positions)}/{len(trades)}")
    
    logger.info("✅ Enhanced strategy test completed!")
    return enhanced_results

if __name__ == "__main__":
    test_enhanced_strategy() 