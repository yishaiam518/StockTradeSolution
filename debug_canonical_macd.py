#!/usr/bin/env python3
"""
Comprehensive debug script for canonical MACD strategy
Tests multiple volatile stocks and verifies the entire pipeline
"""

import pandas as pd
import numpy as np
from src.data_engine.data_engine import DataEngine
from src.indicators.indicators import TechnicalIndicators
from src.strategies.macd_canonical_strategy import MACDCanonicalStrategy
from src.backtesting.backtest_engine import BacktestEngine
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_canonical_macd_pipeline():
    """Test the entire canonical MACD pipeline with multiple stocks"""
    
    # Initialize components
    data_engine = DataEngine()
    indicators = TechnicalIndicators()
    strategy = MACDCanonicalStrategy()
    backtest_engine = BacktestEngine()  # Fixed: no parameters needed
    
    # Test stocks - more volatile ones
    test_stocks = ['TSLA', 'NVDA', 'AMD', 'AAPL', 'MSFT']
    period = ('2020-07-15', '2025-07-15')
    
    print("🔍 Testing Canonical MACD Strategy Pipeline")
    print("=" * 60)
    
    for symbol in test_stocks:
        print(f"\n📈 Testing {symbol}...")
        
        # 1. Fetch data
        print(f"  📥 Fetching {symbol} data...")
        data = data_engine.fetch_data(symbol, period[0], period[1])
        
        if data.empty:
            print(f"  ❌ No data for {symbol}")
            continue
            
        print(f"  ✅ Retrieved {len(data)} data points")
        print(f"  📅 Date range: {data['date'].min().date()} to {data['date'].max().date()}")
        
        # 2. Calculate indicators
        print(f"  🧮 Calculating indicators...")
        data_with_indicators = indicators.calculate_all_indicators(data.copy())
        
        # 3. Check MACD crossovers
        up_crossovers = data_with_indicators['macd_crossover_up'].sum()
        down_crossovers = data_with_indicators['macd_crossover_down'].sum()
        total_crossovers = up_crossovers + down_crossovers
        
        print(f"  📊 MACD Crossovers: {up_crossovers} up, {down_crossovers} down, {total_crossovers} total")
        
        # 4. Run backtest
        print(f"  🎯 Running canonical MACD backtest...")
        try:
            results = backtest_engine.run_backtest(
                symbol=symbol,
                start_date=period[0],
                end_date=period[1],
                strategy_name='MACDCanonical'
            )
            
            total_trades = len(results.get('trades', []))
            final_return = results.get('final_return', 0)
            
            print(f"  📈 Backtest Results: {total_trades} trades, {final_return:.2f}% return")
            
            # 5. Detailed trade analysis
            if total_trades > 0:
                trades = results.get('trades', [])
                print(f"  📋 Trade Details:")
                for i, trade in enumerate(trades[:5]):  # Show first 5 trades
                    entry_date = trade.get('entry_date', 'N/A')
                    exit_date = trade.get('exit_date', 'N/A')
                    pnl = trade.get('pnl', 0)
                    print(f"    Trade {i+1}: {entry_date} → {exit_date} ({pnl:.2f}%)")
                
                if len(trades) > 5:
                    print(f"    ... and {len(trades) - 5} more trades")
            
            # 6. Verify strategy logic
            print(f"  🔍 Verifying strategy logic...")
            strategy.reset()
            entry_signals = 0
            exit_signals = 0
            
            for idx, row in data_with_indicators.iterrows():
                if strategy.should_entry(row):
                    entry_signals += 1
                if strategy.should_exit(row):
                    exit_signals += 1
            
            print(f"  📊 Strategy signals: {entry_signals} entries, {exit_signals} exits")
            
        except Exception as e:
            print(f"  ❌ Backtest failed: {e}")
        
        print("-" * 40)

def test_specific_volatile_stock():
    """Test with a known volatile stock"""
    
    print("\n🎯 Testing with TSLA (known volatile stock)...")
    
    data_engine = DataEngine()
    indicators = TechnicalIndicators()
    strategy = MACDCanonicalStrategy()
    backtest_engine = BacktestEngine()  # Fixed: no parameters needed
    
    # Test TSLA with a shorter, more volatile period
    data = data_engine.fetch_data('TSLA', '2022-01-01', '2024-12-31')
    
    if not data.empty:
        print(f"✅ TSLA data: {len(data)} points")
        
        # Calculate indicators
        data_with_indicators = indicators.calculate_all_indicators(data.copy())
        
        # Count crossovers
        up_crossovers = data_with_indicators['macd_crossover_up'].sum()
        down_crossovers = data_with_indicators['macd_crossover_down'].sum()
        
        print(f"📊 TSLA MACD Crossovers: {up_crossovers} up, {down_crossovers} down")
        
        # Run backtest
        results = backtest_engine.run_backtest(
            symbol='TSLA',
            start_date='2022-01-01',
            end_date='2024-12-31',
            strategy_name='MACDCanonical'
        )
        
        total_trades = len(results.get('trades', []))
        print(f"📈 TSLA Backtest: {total_trades} trades")
        
        if total_trades > 0:
            trades = results.get('trades', [])
            for i, trade in enumerate(trades[:10]):
                entry_date = trade.get('entry_date', 'N/A')
                exit_date = trade.get('exit_date', 'N/A')
                pnl = trade.get('pnl', 0)
                print(f"  Trade {i+1}: {entry_date} → {exit_date} ({pnl:.2f}%)")

if __name__ == "__main__":
    test_canonical_macd_pipeline()
    test_specific_volatile_stock() 