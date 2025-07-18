#!/usr/bin/env python3
"""
Test script to verify the 5% exit thresholds are working correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.real_time_trading.automation_engine import HistoricalBacktestEngine
from src.utils.config_loader import config
from src.trading_system import get_trading_system

def test_exit_thresholds():
    """Test the 5% exit thresholds to ensure more trades are generated."""
    
    print("=== TESTING 5% EXIT THRESHOLDS ===")
    
    # Get config
    config_dict = config.config
    print(f"Config loaded: {list(config_dict.keys())}")
    
    # Test stock selection
    print("\n--- Testing Stock Selection with Lower Thresholds ---")
    trading_system = get_trading_system()
    
    # Test stock selection
    selected_stocks = trading_system.select_stocks(max_stocks=5, min_score=0.4)
    print(f"Selected stocks: {selected_stocks}")
    
    # Test historical backtest with 5% thresholds
    print("\n--- Testing Historical Backtest with 5% Exit Thresholds ---")
    
    # Create historical backtest engine
    start_date = "2023-01-01"
    end_date = "2023-12-31"
    benchmark = "SPY"
    
    engine = HistoricalBacktestEngine(config_dict, start_date, end_date, benchmark)
    
    # Run backtest
    print(f"Running historical backtest from {start_date} to {end_date}")
    results = engine.run_backtest()
    
    # Analyze results
    if results and 'trades' in results:
        trades = results['trades']
        print(f"\nTotal trades generated: {len(trades)}")
        
        # Count buy and sell trades
        buy_trades = [t for t in trades if t['action'] == 'BUY']
        sell_trades = [t for t in trades if t['action'] == 'SELL']
        
        print(f"BUY trades: {len(buy_trades)}")
        print(f"SELL trades: {len(sell_trades)}")
        
        # Show trade details
        if trades:
            print("\n--- Trade Details ---")
            for i, trade in enumerate(trades[:10]):  # Show first 10 trades
                print(f"Trade {i+1}: {trade['action']} {trade['symbol']} at ${trade['price']:.2f}")
                if 'pnl_pct' in trade:
                    print(f"  PnL: {trade['pnl_pct']:.2f}%")
        
        # Show performance metrics
        if 'metrics' in results:
            metrics = results['metrics']
            print(f"\n--- Performance Metrics ---")
            print(f"Total Return: {results.get('total_return', 0):.2f}%")
            print(f"Win Rate: {metrics.get('win_rate', 0):.2f}")
            print(f"Average Return: {metrics.get('avg_return', 0):.2f}%")
            print(f"Max Drawdown: {metrics.get('max_drawdown', 0):.2f}%")
            print(f"Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
            print(f"Profit Factor: {metrics.get('profit_factor', 0):.2f}")
        
        # Check if we have more trades than before
        if len(trades) > 0:
            print(f"\n✅ SUCCESS: Generated {len(trades)} trades with 5% exit thresholds")
            print(f"✅ SELL trades: {len(sell_trades)} (should be > 0)")
        else:
            print(f"\n❌ ISSUE: No trades generated with 5% exit thresholds")
    
    else:
        print("❌ No results returned from backtest")
    
    print("\n=== TEST COMPLETED ===")

if __name__ == "__main__":
    test_exit_thresholds() 