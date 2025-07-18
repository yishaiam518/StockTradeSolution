#!/usr/bin/env python3
"""
Test script to verify that regular backtest and historical backtest 
use the same centralized trading system and produce consistent results.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.trading_system import get_trading_system
from src.backtesting.backtest_engine import BacktestEngine
from src.real_time_trading.automation_engine import HistoricalBacktestEngine
import pandas as pd
from datetime import datetime, timedelta

def test_backtest_consistency():
    """Test that both backtest methods use the same centralized system."""
    print("=== Testing Backtest Consistency ===\n")
    
    # Initialize centralized trading system
    trading_system = get_trading_system()
    
    # Test parameters
    symbol = 'AAPL'
    start_date = '2023-01-01'
    end_date = '2023-12-31'
    strategy_name = 'MACDStrategy'
    
    print(f"Testing with symbol: {symbol}")
    print(f"Date range: {start_date} to {end_date}")
    print(f"Strategy: {strategy_name}")
    print()
    
    # Test 1: Regular backtest using centralized system
    print("1. Running regular backtest...")
    backtest_engine = BacktestEngine()
    regular_results = backtest_engine.run_backtest(
        symbol=symbol,
        strategy_name=strategy_name,
        start_date=start_date,
        end_date=end_date,
        custom_parameters={},
        benchmark='SPY'
    )
    
    print(f"   - Regular backtest trades: {len(regular_results.get('trades', []))}")
    print(f"   - Regular backtest total return: {regular_results.get('total_return', 0):.2f}%")
    
    # Test 2: Historical backtest using centralized system
    print("\n2. Running historical backtest...")
    historical_engine = HistoricalBacktestEngine(
        config=trading_system.config.config,
        start_date=start_date,
        end_date=end_date,
        benchmark='SPY'
    )
    historical_results = historical_engine.run_backtest()
    
    print(f"   - Historical backtest trades: {len(historical_results.get('trades', []))}")
    print(f"   - Historical backtest total return: {historical_results.get('total_return', 0):.2f}%")
    
    # Test 3: Direct trading system backtest
    print("\n3. Running direct trading system backtest...")
    
    # Reset strategy
    trading_system.reset_strategy(strategy_name)
    
    # Prepare data
    data = trading_system.prepare_data(symbol, start_date, end_date)
    print(f"   - Prepared {len(data)} data points")
    
    # Run simulation manually
    trades = []
    portfolio_values = []
    capital = 10000
    current_capital = capital
    
    # Check column names
    print(f"   - Data columns: {list(data.columns)}")
    
    # Use correct column name (lowercase 'close')
    close_col = 'close' if 'close' in data.columns else 'Close'
    
    for i in range(len(data)):
        signal_generated, signal_details = trading_system.run_strategy_signal(
            strategy_name, data, i
        )
        
        if signal_generated and signal_details.get('action') == 'BUY':
            # Simulate buy
            current_price = data.iloc[i][close_col]
            shares = current_capital / current_price
            trades.append({
                'action': 'BUY',
                'price': current_price,
                'shares': shares,
                'date': str(data.index[i])
            })
            current_capital = 0
        
        elif signal_generated and signal_details.get('action') == 'SELL':
            # Simulate sell
            current_price = data.iloc[i][close_col]
            if trades and trades[-1]['action'] == 'BUY':
                entry_price = trades[-1]['price']
                shares = trades[-1]['shares']
                pnl = (current_price - entry_price) * shares
                current_capital = shares * current_price
                
                trades.append({
                    'action': 'SELL',
                    'price': current_price,
                    'shares': shares,
                    'pnl': pnl,
                    'pnl_pct': (pnl / (entry_price * shares)) * 100,
                    'date': str(data.index[i])
                })
        
        # Track portfolio value
        portfolio_values.append({
            'date': str(data.index[i]),
            'value': current_capital
        })
    
    print(f"   - Direct system trades: {len([t for t in trades if t['action'] in ['BUY', 'SELL']])}")
    
    # Compare results
    print("\n=== Consistency Check ===")
    
    regular_trades = len(regular_results.get('trades', []))
    historical_trades = len(historical_results.get('trades', []))
    direct_trades = len([t for t in trades if t['action'] in ['BUY', 'SELL']])
    
    print(f"Regular backtest trades: {regular_trades}")
    print(f"Historical backtest trades: {historical_trades}")
    print(f"Direct system trades: {direct_trades}")
    
    # Check if they're using the same strategy configuration
    print(f"\nStrategy configuration check:")
    strategy = trading_system.get_strategy(strategy_name)
    if strategy:
        print(f"   - Entry threshold: {getattr(strategy, 'entry_threshold', 'N/A')}")
        print(f"   - Take profit: {getattr(strategy, 'take_profit_pct', 'N/A')}%")
        print(f"   - Stop loss: {getattr(strategy, 'stop_loss_pct', 'N/A')}%")
    
    # Check if they're using the same data
    print(f"\nData consistency check:")
    print(f"   - Data points: {len(data)}")
    print(f"   - Date range: {data.index[0]} to {data.index[-1]}")
    print(f"   - Columns: {list(data.columns)}")
    
    print("\n=== Test Complete ===")
    
    return {
        'regular_trades': regular_trades,
        'historical_trades': historical_trades,
        'direct_trades': direct_trades,
        'data_points': len(data)
    }

if __name__ == "__main__":
    results = test_backtest_consistency()
    print(f"\nSummary: {results}") 