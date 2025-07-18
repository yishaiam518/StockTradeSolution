#!/usr/bin/env python3
"""
Test script to verify the improved MACD strategy with drawdown protection.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.backtesting.backtest_engine import BacktestEngine
from src.strategies.macd_strategy import MACDStrategy
from src.data_engine.data_engine import DataEngine

def test_improved_strategy():
    """Test the improved strategy with drawdown protection."""
    print("Testing improved MACD strategy with drawdown protection...")
    
    # Initialize components
    data_engine = DataEngine()
    backtest_engine = BacktestEngine()
    
    # Test with different configurations
    test_configs = [
        {
            'name': 'Standard MACD',
            'config': {
                'entry_conditions': {
                    'macd_crossover_up': True,
                    'price_above_ema': True,
                    'rsi_range': [20, 80],
                    'threshold': 0.05  # More relaxed threshold
                },
                'exit_conditions': {
                    'macd_crossover_down': True,
                    'price_below_ema_short': True,
                    'stop_loss_pct': 3.0,
                    'take_profit_pct': 10.0,
                    'max_drawdown_pct': 5.0,  # New: Drawdown protection
                    'max_hold_days': 252,
                    'threshold': 0.5
                }
            }
        },
        {
            'name': 'Conservative with Tight Drawdown',
            'config': {
                'entry_conditions': {
                    'macd_crossover_up': True,
                    'price_above_ema': True,
                    'rsi_range': [25, 75],  # More relaxed RSI range
                    'threshold': 0.2  # More relaxed threshold
                },
                'exit_conditions': {
                    'macd_crossover_down': True,
                    'price_below_ema_short': True,
                    'stop_loss_pct': 2.0,
                    'take_profit_pct': 8.0,
                    'max_drawdown_pct': 3.0,  # Conservative drawdown
                    'max_hold_days': 365,
                    'threshold': 0.6
                }
            }
        }
    ]
    
    for test_config in test_configs:
        print(f"\n=== Testing {test_config['name']} ===")
        
        # Create strategy with custom config
        strategy = MACDStrategy(config_dict=test_config['config'])
        
        # Run backtest
        results = backtest_engine.run_backtest(
            ticker="AAPL",
            strategy=strategy,
            start_date="2020-01-01",  # Longer period to get more trades
            end_date="2023-12-31",
            initial_capital=10000
        )
        
        # Display results
        print(f"Total trades: {results.get('total_trades', 0)}")
        print(f"Total return: {results.get('total_return_pct', 0):.2f}%")
        print(f"Final equity: ${results.get('final_equity', 0):.2f}")
        
        # Show trade details if available
        trade_log = results.get('trade_log', [])
        if trade_log:
            print(f"Trade details:")
            for i, trade in enumerate(trade_log[:3]):  # Show first 3 trades
                entry_price = trade.get('entry_price', 0)
                exit_price = trade.get('exit_price', 0)
                pnl = trade.get('pnl', 0) * 100
                entry_date = trade.get('entry_date', 'Unknown')
                exit_date = trade.get('exit_date', 'Unknown')
                
                print(f"  Trade {i+1}: BUY ${entry_price:.2f} on {entry_date} → SELL ${exit_price:.2f} on {exit_date} ({pnl:.2f}%)")
        
        print("-" * 50)

if __name__ == "__main__":
    test_improved_strategy() 