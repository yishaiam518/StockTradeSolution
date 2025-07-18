#!/usr/bin/env python3
"""
Debug script to examine trade details and understand exit reasons.
"""

import sys
import os
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from data_engine import DataEngine
from indicators import TechnicalIndicators
from strategies import MACDStrategy
from backtesting import BacktestEngine


def debug_trade():
    """Debug the specific trade to understand exit reason."""
    
    # Initialize components
    data_engine = DataEngine()
    indicators = TechnicalIndicators()
    strategy = MACDStrategy()
    backtest_engine = BacktestEngine()
    
    # Use the same parameters as the example
    ticker = "AAPL"
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    print("🔍 DEBUGGING TRADE ANALYSIS")
    print("=" * 40)
    
    # Fetch and prepare data
    data = data_engine.fetch_data(ticker, start_date, end_date)
    data_with_indicators = indicators.calculate_all_indicators(data)
    
    # Find the trade period (around 2024-10-07)
    trade_start_idx = None
    for i, (date, row) in enumerate(data_with_indicators.iterrows()):
        date_str = str(row['date'])
        if '2024-10-07' in date_str:
            trade_start_idx = i
            break
    
    if trade_start_idx is None:
        print("❌ Could not find trade start date")
        return
    
    print(f"📊 Trade Analysis for AAPL around 2024-10-07")
    print(f"Entry Index: {trade_start_idx}")
    
    # Analyze the entry
    entry_row = data_with_indicators.iloc[trade_start_idx]
    print(f"\n📈 ENTRY CONDITIONS (Index {trade_start_idx}):")
    print(f"Date: {entry_row['date']}")
    print(f"Close Price: ${entry_row['close']:.2f}")
    print(f"MACD Line: {entry_row['macd_line']:.4f}")
    print(f"MACD Signal: {entry_row['macd_signal']:.4f}")
    print(f"MACD Crossover Up: {entry_row['macd_crossover_up']}")
    print(f"RSI: {entry_row['rsi']:.2f}")
    print(f"RSI Neutral (40-60): {40 <= entry_row['rsi'] <= 60}")
    print(f"EMA Short: {entry_row['ema_short']:.2f}")
    print(f"EMA Long: {entry_row['ema_long']:.2f}")
    print(f"Price > EMA Short: {entry_row['close'] > entry_row['ema_short']}")
    print(f"Price > EMA Long: {entry_row['close'] > entry_row['ema_long']}")
    
    # Find the exit
    entry_price = 227.63  # From the trade log
    exit_found = False
    
    for i in range(trade_start_idx + 1, min(trade_start_idx + 50, len(data_with_indicators))):
        row = data_with_indicators.iloc[i]
        current_price = row['close']
        pnl_pct = ((current_price - entry_price) / entry_price) * 100
        
        # Check exit conditions
        take_profit_hit = pnl_pct >= 5.0
        stop_loss_hit = pnl_pct <= -3.0
        macd_crossover_down = row['macd_crossover_down']
        price_below_ema_short = not row['price_above_ema_short']
        
        if take_profit_hit or stop_loss_hit or macd_crossover_down or price_below_ema_short:
            print(f"\n📉 EXIT CONDITIONS (Index {i}):")
            print(f"Date: {row['date']}")
            print(f"Close Price: ${current_price:.2f}")
            print(f"PnL: {pnl_pct:.2f}%")
            print(f"Take Profit Hit (5%): {take_profit_hit}")
            print(f"Stop Loss Hit (-3%): {stop_loss_hit}")
            print(f"MACD Crossover Down: {macd_crossover_down}")
            print(f"Price Below EMA Short: {price_below_ema_short}")
            print(f"MACD Line: {row['macd_line']:.4f}")
            print(f"MACD Signal: {row['macd_signal']:.4f}")
            print(f"EMA Short: {row['ema_short']:.2f}")
            
            # Determine which condition triggered first
            if take_profit_hit:
                exit_reason = "Take Profit"
            elif stop_loss_hit:
                exit_reason = "Stop Loss"
            elif macd_crossover_down:
                exit_reason = "MACD Crossover Down"
            elif price_below_ema_short:
                exit_reason = "Price Below EMA Short"
            else:
                exit_reason = "Unknown"
            
            print(f"\n🎯 EXIT REASON: {exit_reason}")
            exit_found = True
            break
    
    if not exit_found:
        print("❌ Could not find exit point")
    
    # Show a few days before and after for context
    print(f"\n📅 CONTEXT (5 days before and after entry):")
    start_idx = max(0, trade_start_idx - 5)
    end_idx = min(len(data_with_indicators), trade_start_idx + 10)
    
    for i in range(start_idx, end_idx):
        row = data_with_indicators.iloc[i]
        if i == trade_start_idx:
            print(f"  → {row['date']}: ${row['close']:.2f} (ENTRY)")
        elif i > trade_start_idx and exit_found and i <= trade_start_idx + 10:
            print(f"    {row['date']}: ${row['close']:.2f}")
        else:
            print(f"    {row['date']}: ${row['close']:.2f}")


if __name__ == "__main__":
    debug_trade() 