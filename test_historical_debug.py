#!/usr/bin/env python3
"""
Debug script for historical backtest to see what's happening with stock selection.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.machine_learning.stock_scorer import UnifiedStockScorer, ScoringMode
from src.backtesting.backtest_engine import BacktestEngine
from src.utils.logger import get_logger

def test_historical_backtest():
    """Test the historical backtest to see what's happening."""
    logger = get_logger(__name__)
    
    print("🔍 Testing Historical Backtest Debug...")
    print("=" * 50)
    
    # Test stock scorer
    print("\n1. Testing Stock Scorer...")
    scorer = UnifiedStockScorer()
    
    # Test stock selection
    print("\n2. Testing Stock Selection...")
    all_stocks = scorer._get_all_stocks()
    print(f"Total stocks found: {len(all_stocks)}")
    print(f"Sample stocks: {all_stocks[:10]}")
    
    # Test scoring list creation
    print("\n3. Testing Scoring List Creation...")
    scoring_list = scorer.create_scoring_list(
        mode=ScoringMode.HISTORICAL,
        strategy="MACD",
        profile="balanced",
        max_stocks=20,
        min_score=0.1  # Lower threshold for testing
    )
    
    print(f"Scoring list created with {len(scoring_list)} stocks")
    for score in scoring_list[:5]:  # Show first 5
        print(f"  {score.symbol}: {score.score:.3f} (confidence: {score.confidence:.3f})")
    
    # Test backtest engine
    print("\n4. Testing Backtest Engine...")
    backtest_engine = BacktestEngine()
    
    # Run historical backtest
    print("\n5. Running Historical Backtest...")
    result = backtest_engine.run_historical_backtest(
        strategy="MACD",
        profile="balanced",
        start_date="2024-07-19",
        end_date="2025-07-19",
        benchmark="SPY"
    )
    
    print(f"\nBacktest Result:")
    print(f"  Total Trades: {result.get('total_trades', 0)}")
    print(f"  Strategy Return: {result.get('strategy_return', 0):.2f}%")
    print(f"  Benchmark Return: {result.get('benchmark_return', 0):.2f}%")
    print(f"  Sharpe Ratio: {result.get('sharpe_ratio', 0):.2f}")
    print(f"  Max Drawdown: {result.get('max_drawdown', 0):.2f}%")
    
    print("\n✅ Debug test completed!")

if __name__ == "__main__":
    test_historical_backtest() 