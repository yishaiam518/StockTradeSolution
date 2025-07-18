#!/usr/bin/env python3
"""
Debug script to test backtest functionality and identify why it's returning 0 trades.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data_engine.data_engine import DataEngine
from src.indicators.indicators import TechnicalIndicators
from src.strategies.macd_strategy import MACDStrategy
from src.backtesting.backtest_engine import BacktestEngine
from src.utils.logger import logger

def debug_backtest():
    """Debug the backtest functionality."""
    print("=== DEBUGGING BACKTEST ===")
    
    # Initialize components
    data_engine = DataEngine()
    indicators = TechnicalIndicators()
    strategy = MACDStrategy()
    backtest_engine = BacktestEngine()
    
    # Test data fetching
    print("\n1. Testing data fetching...")
    try:
        data = data_engine.fetch_data("AAPL", "2023-01-01", "2023-12-31")
        print(f"   Data shape: {data.shape}")
        print(f"   Data columns: {list(data.columns)}")
        print(f"   Date range: {data.index[0]} to {data.index[-1]}")
    except Exception as e:
        print(f"   Error fetching data: {e}")
        return
    
    # Test indicator calculation
    print("\n2. Testing indicator calculation...")
    try:
        data_with_indicators = indicators.calculate_all_indicators(data)
        print(f"   Data with indicators shape: {data_with_indicators.shape}")
        print(f"   Indicator columns: {[col for col in data_with_indicators.columns if col not in data.columns]}")
        
        # Check for required indicators
        required_indicators = [
            'macd_line', 'macd_signal', 'macd_crossover_up', 'macd_crossover_down',
            'rsi', 'ema_short', 'ema_long', 'price_above_ema_short', 'price_above_ema_long'
        ]
        
        missing_indicators = [ind for ind in required_indicators if ind not in data_with_indicators.columns]
        if missing_indicators:
            print(f"   MISSING INDICATORS: {missing_indicators}")
        else:
            print("   All required indicators present")
            
        # Show some sample values
        sample_row = data_with_indicators.iloc[100]
        print(f"   Sample values at index 100:")
        for ind in required_indicators:
            print(f"     {ind}: {sample_row.get(ind, 'MISSING')}")
            
    except Exception as e:
        print(f"   Error calculating indicators: {e}")
        return
    
    # Test strategy validation
    print("\n3. Testing strategy validation...")
    try:
        is_valid = strategy.validate_data_requirements(data_with_indicators)
        print(f"   Strategy validation: {is_valid}")
    except Exception as e:
        print(f"   Error validating strategy: {e}")
        return
    
    # Test strategy signals with detailed scoring
    print("\n4. Testing strategy signals with detailed scoring...")
    try:
        # Test entry signals with detailed scoring
        entry_signals = 0
        exit_signals = 0
        
        print("   Testing entry signals...")
        for i in range(50, min(100, len(data_with_indicators))):
            should_entry, entry_reason = strategy.should_entry(data_with_indicators, i)
            
            # Show detailed scoring for first few attempts
            if i < 60:
                score = entry_reason.get('score', 0)
                threshold = entry_reason.get('threshold', 0)
                print(f"     Index {i}: Score={score:.3f}, Threshold={threshold}, Should_Entry={should_entry}")
                print(f"       MACD Crossover Up: {entry_reason.get('macd_crossover_up', False)}")
                print(f"       RSI Neutral: {entry_reason.get('rsi_neutral', False)} (RSI: {entry_reason.get('rsi_value', 0):.1f})")
                print(f"       Price Above EMA Short: {entry_reason.get('price_above_ema_short', False)}")
                print(f"       Price Above EMA Long: {entry_reason.get('price_above_ema_long', False)}")
            
            if should_entry:
                entry_signals += 1
                print(f"   ENTRY SIGNAL at index {i}: {entry_reason}")
        
        print(f"   Total entry signals in range: {entry_signals}")
        
        # Test exit signals (simulate having a position)
        print("\n   Testing exit signals...")
        strategy.current_position = {
            'entry_price': 150.0,
            'entry_date': '2023-01-15',
            'shares': 10
        }
        
        for i in range(50, min(100, len(data_with_indicators))):
            should_exit, exit_reason = strategy.should_exit(data_with_indicators, i, 150.0, '2023-01-15')
            
            # Show detailed scoring for first few attempts
            if i < 60:
                score = exit_reason.get('score', 0)
                threshold = exit_reason.get('threshold', 0)
                pnl_pct = exit_reason.get('pnl_pct', 0)
                print(f"     Index {i}: Score={score:.3f}, Threshold={threshold}, PnL={pnl_pct:.2f}%, Should_Exit={should_exit}")
                print(f"       Take Profit Hit: {exit_reason.get('take_profit_hit', False)}")
                print(f"       Stop Loss Hit: {exit_reason.get('stop_loss_hit', False)}")
                print(f"       MACD Crossover Down: {exit_reason.get('macd_crossover_down', False)}")
                print(f"       Price Below EMA Short: {exit_reason.get('price_below_ema_short', False)}")
            
            if should_exit:
                exit_signals += 1
                print(f"   EXIT SIGNAL at index {i}: {exit_reason}")
        
        print(f"   Total exit signals in range: {exit_signals}")
        
    except Exception as e:
        print(f"   Error testing strategy signals: {e}")
        return
    
    # Test full backtest
    print("\n5. Testing full backtest...")
    try:
        results = backtest_engine.run_backtest(
            symbol="AAPL",
            strategy_name="MACDStrategy",
            start_date="2023-01-01",
            end_date="2023-12-31"
        )
        
        print(f"   Backtest results:")
        print(f"     Total trades: {results.get('total_trades', 0)}")
        print(f"     Total return: {results.get('total_return_pct', 0):.2f}%")
        print(f"     Final capital: ${results.get('final_capital', 0):.2f}")
        
        if results.get('trade_log'):
            print(f"     First trade: {results['trade_log'][0]}")
            print(f"     Last trade: {results['trade_log'][-1]}")
        else:
            print("     No trades executed")
            
    except Exception as e:
        print(f"   Error running backtest: {e}")
        return
    
    print("\n=== DEBUG COMPLETE ===")

if __name__ == "__main__":
    debug_backtest() 