#!/usr/bin/env python3
"""
Debug script for progressive historical backtest to test the new day-by-day simulation.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.machine_learning.stock_scorer import UnifiedStockScorer, ScoringMode
from src.backtesting.backtest_engine import BacktestEngine
from src.utils.logger import get_logger

def test_progressive_historical_backtest():
    """Test the progressive historical backtest with day-by-day simulation."""
    logger = get_logger(__name__)
    
    print("🔍 Testing Progressive Historical Backtest...")
    print("=" * 60)
    
    # Test stock scorer
    print("\n1. Testing Stock Scorer...")
    scorer = UnifiedStockScorer()
    
    # Test stock selection
    print("\n2. Testing Stock Selection...")
    all_stocks = scorer._get_all_stocks()
    print(f"Found {len(all_stocks)} unique stocks from config")
    
    # Test backtest engine
    print("\n3. Testing Backtest Engine...")
    backtest_engine = BacktestEngine()
    
    # Test progressive historical backtest
    print("\n4. Testing Progressive Historical Backtest...")
    print("This will simulate day-by-day trading over 1 year...")
    
    result = backtest_engine.run_historical_backtest(
        strategy="MACD",
        profile="balanced",
        start_date="2024-07-18",
        end_date="2025-07-18",
        benchmark="SPY"
    )
    
    print(f"\nProgressive Backtest Result:")
    print(f"  Total Trades: {result.get('total_trades', 0)}")
    print(f"  Strategy Return: {result.get('total_return', 0):.2f}%")
    print(f"  Benchmark Return: {result.get('benchmark_return', 0):.2f}%")
    print(f"  Sharpe Ratio: {result.get('sharpe_ratio', 0):.2f}")
    print(f"  Max Drawdown: {result.get('max_drawdown', 0):.2f}%")
    print(f"  Win Rate: {result.get('win_rate', 0):.2f}%")
    print(f"  Alpha: {result.get('alpha', 0):.2f}%")
    
    # Show performance metrics if available
    if 'performance' in result:
        perf = result['performance']
        print(f"\nDetailed Performance:")
        print(f"  Final Value: ${perf.get('final_value', 0):,.2f}")
        print(f"  Volatility: {perf.get('volatility', 0):.2f}%")
        print(f"  Winning Trades: {perf.get('winning_trades', 0)}")
        print(f"  Average Trade Return: {perf.get('avg_trade_return', 0):.2f}%")
    
    # Show some trades if available
    if 'trades' in result and result['trades']:
        print(f"\nSample Trades (first 5):")
        for i, trade in enumerate(result['trades'][:5]):
            print(f"  {i+1}. {trade['action']} {trade['shares']:.2f} shares of {trade['symbol']} at ${trade['price']:.2f}")
            if 'pnl' in trade:
                print(f"     P&L: ${trade['pnl']:.2f} ({trade['pnl_pct']:.2f}%)")
    
    print(f"\n✅ Progressive Historical Backtest completed!")
    print("=" * 60)

if __name__ == "__main__":
    test_progressive_historical_backtest() 