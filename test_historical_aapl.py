#!/usr/bin/env python3
"""
Test script to specifically test historical backtest with AAPL only.
This will help identify the exact issue between regular backtest and historical backtest.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.trading_system import get_trading_system
from src.backtesting.backtest_engine import BacktestEngine
import pandas as pd
from datetime import datetime, timedelta

def test_historical_aapl():
    """Test historical backtest with AAPL only to identify the issue."""
    print("=== Testing Historical Backtest with AAPL Only ===\n")
    
    # Initialize the centralized trading system
    trading_system = get_trading_system()
    
    # Test parameters
    symbol = 'AAPL'
    strategy_name = 'MACDStrategy'
    start_date = '2023-01-01'
    end_date = '2023-12-31'
    benchmark = 'SPY'
    
    print(f"Testing Parameters:")
    print(f"  - Symbol: {symbol}")
    print(f"  - Strategy: {strategy_name}")
    print(f"  - Start Date: {start_date}")
    print(f"  - End Date: {end_date}")
    print(f"  - Benchmark: {benchmark}")
    print()
    
    # Test 1: Direct trading system backtest
    print("1. Testing Direct Trading System Backtest...")
    trading_system.reset_strategy(strategy_name)
    
    # Prepare data using trading system
    data = trading_system.prepare_data(symbol, start_date, end_date)
    print(f"   - Prepared data: {len(data)} data points")
    print(f"   - Data columns: {list(data.columns)}")
    
    # Run backtest using trading system
    backtest_engine = BacktestEngine()
    results = backtest_engine.run_historical_backtest(
        strategy=strategy_name,
        profile='moderate',
        start_date=start_date,
        end_date=end_date,
        benchmark=benchmark
    )
    
    if results:
        print(f"   - Total trades: {len(results.get('trades', []))}")
        print(f"   - Portfolio values: {len(results.get('portfolio_values', []))}")
        
        # Show first few trades
        trades = results.get('trades', [])
        if trades:
            print(f"   - First trade: {trades[0]}")
            if len(trades) > 1:
                print(f"   - Second trade: {trades[1]}")
    else:
        print("   - No results returned")
    
    print()
    
    # Test 2: Manual simulation using trading system
    print("2. Testing Manual Simulation...")
    trading_system.reset_strategy(strategy_name)
    
    trades = []
    portfolio_values = []
    capital = 10000
    current_capital = capital
    
    # Use correct column name
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
                'date': data.index[i],
                'capital': current_capital
            })
            current_capital = 0
        
        elif signal_generated and signal_details.get('action') == 'SELL':
            # Simulate sell
            if trades and trades[-1]['action'] == 'BUY':
                current_price = data.iloc[i][close_col]
                shares = trades[-1]['shares']
                sell_value = shares * current_price
                pnl = ((sell_value - trades[-1]['capital']) / trades[-1]['capital']) * 100
                
                trades.append({
                    'action': 'SELL',
                    'price': current_price,
                    'shares': shares,
                    'date': data.index[i],
                    'pnl': pnl,
                    'sell_value': sell_value
                })
                current_capital = sell_value
    
    print(f"   - Manual simulation trades: {len(trades)}")
    if trades:
        print(f"   - First trade: {trades[0]}")
        if len(trades) > 1:
            print(f"   - Second trade: {trades[1]}")
    
    print()
    
    # Test 3: Check strategy configuration
    print("3. Testing Strategy Configuration...")
    strategy = trading_system.get_strategy(strategy_name)
    if strategy:
        print(f"   - Strategy type: {type(strategy).__name__}")
        print(f"   - Strategy config: {strategy.config if hasattr(strategy, 'config') else 'No config'}")
        
        # Test entry signal generation
        print("   - Testing entry signal generation...")
        entry_signals = 0
        for i in range(min(50, len(data))):  # Test first 50 data points
            signal_generated, signal_details = trading_system.run_strategy_signal(
                strategy_name, data, i
            )
            if signal_generated and signal_details.get('action') == 'BUY':
                entry_signals += 1
                print(f"     Entry signal at index {i}: {signal_details}")
        
        print(f"   - Entry signals found: {entry_signals}")
    
    print()
    
    # Test 4: Compare with regular backtest
    print("4. Comparing with Regular Backtest...")
    print("   - Regular backtest should use the same trading system")
    print("   - Historical backtest should use the same trading system")
    print("   - Both should produce identical results for the same parameters")
    
    return results

if __name__ == "__main__":
    test_historical_aapl() 