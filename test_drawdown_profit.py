#!/usr/bin/env python3
"""
Test script to verify MACD strategy with new drawdown and profit parameters.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.backtesting.backtest_engine import BacktestEngine
from src.strategies.macd_strategy import MACDStrategy
from src.data_engine.data_engine import DataEngine

def test_macd_with_new_params():
    """Test MACD strategy with 7% drawdown and 20% profit parameters."""
    print("Testing MACD strategy with new parameters:")
    print("- max_drawdown_pct: 7.0%")
    print("- take_profit_pct: 20.0%")
    print()
    
    # Initialize components
    data_engine = DataEngine()
    backtest_engine = BacktestEngine()
    
    # Run backtest with relaxed entry conditions and 3-year period
    results = backtest_engine.run_backtest(
        ticker="AAPL",
        strategy=MACDStrategy(config_dict={
            'entry_conditions': {
                'macd_crossover_up': True,
                'price_above_ema': True,
                'rsi_range': [40, 60],
                'threshold': 0.1,
                'weights': {
                    'macd_crossover_up': 0.5,
                    'rsi_neutral': 0.3,
                    'price_above_ema_short': 0.1,
                    'price_above_ema_long': 0.1
                }
            },
            'exit_conditions': {
                'macd_crossover_down': True,
                'price_below_ema_short': True,
                'stop_loss_pct': 3.0,
                'take_profit_pct': 20.0,
                'max_drawdown_pct': 7.0,
                'max_hold_days': 252,
                'threshold': 0.5
            }
        }),
        start_date="2021-01-01",
        end_date="2023-12-31",
        initial_capital=10000
    )
    
    print("=== BACKTEST RESULTS ===")
    print(f"Total Trades: {results.get('total_trades', 0)}")
    print(f"Total Return: {results.get('total_return', 0):.2f}%")
    print(f"Sharpe Ratio: {results.get('sharpe_ratio', 0):.2f}")
    print(f"Max Drawdown: {results.get('max_drawdown', 0):.2f}%")
    print(f"Win Rate: {results.get('win_rate', 0):.2f}%")
    print()
    
    # Show trade details
    trade_log = results.get('trade_log', [])
    if trade_log:
        print("=== TRADE DETAILS ===")
        for i, trade in enumerate(trade_log, 1):
            entry_price = trade.get('entry_price', 0)
            exit_price = trade.get('exit_price', 0)
            shares = trade.get('shares', 0)
            pnl = trade.get('pnl', 0)
            entry_date = trade.get('entry_date', 'Unknown')
            exit_date = trade.get('exit_date', 'Unknown')
            
            print(f"Trade {i}:")
            print(f"  Entry: {shares:.2f} shares at ${entry_price:.2f} on {entry_date}")
            print(f"  Exit: ${exit_price:.2f} on {exit_date}")
            print(f"  PnL: {pnl*100:.2f}%")
            print()
    else:
        print("No trades generated.")
    
    return results

if __name__ == "__main__":
    test_macd_with_new_params() 