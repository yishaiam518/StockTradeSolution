#!/usr/bin/env python3
"""
Test script for the backtesting framework
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.backtesting.backtest_engine import BacktestEngine
from src.backtesting.strategies.macd_strategy import MACDStrategy
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_backtesting_framework():
    """Test the backtesting framework"""
    print("🧪 TESTING BACKTESTING FRAMEWORK")
    print("=" * 50)
    
    try:
        # Initialize backtesting engine
        print("1. Initializing backtesting engine...")
        engine = BacktestEngine(initial_capital=100000.0)
        print("✅ Backtesting engine initialized")
        
        # Create MACD strategy
        print("\n2. Creating MACD strategy...")
        strategy_params = {
            'fast_period': 12,
            'slow_period': 26,
            'signal_period': 9,
            'position_size': 0.1,
            'enable_short': False
        }
        strategy = MACDStrategy(strategy_params)
        print("✅ MACD strategy created")
        print(f"   Parameters: {strategy.parameters}")
        
        # Test data loading
        print("\n3. Testing data loading...")
        collection_id = "AMEX_20250803_161652"
        symbol = "BND"
        
        data = engine.load_data(collection_id, symbol)
        if data.empty:
            print("❌ No data available for testing")
            return
        
        print(f"✅ Data loaded successfully")
        print(f"   Data points: {len(data)}")
        print(f"   Columns: {len(data.columns)}")
        print(f"   Date range: {data['Date'].min()} to {data['Date'].max()}")
        
        # Check for required indicator columns
        required_indicators = ['macd_line_12_26', 'macd_signal_12_26_9', 'rsi_14', 'ema_20', 'atr_14']
        available_indicators = [col for col in required_indicators if col in data.columns]
        print(f"   Available indicators: {len(available_indicators)}/{len(required_indicators)}")
        
        if len(available_indicators) < len(required_indicators):
            print("⚠️  Some indicators missing, calculating them...")
            # Calculate missing indicators
            from src.indicators import indicator_manager
            data = indicator_manager.calculate_all_indicators(data)
            print("✅ Indicators calculated")
        
        # Run backtest
        print("\n4. Running backtest...")
        results = engine.run_backtest(
            strategy=strategy,
            collection_id=collection_id,
            symbol=symbol,
            start_date="2023-01-01",
            end_date="2024-12-31"
        )
        
        if "error" in results:
            print(f"❌ Backtest failed: {results['error']}")
            return
        
        print("✅ Backtest completed successfully!")
        print("\n📊 BACKTEST RESULTS:")
        print(f"   Strategy: {results['strategy']}")
        print(f"   Symbol: {results['symbol']}")
        print(f"   Initial Capital: ${results['initial_capital']:,.2f}")
        print(f"   Final Capital: ${results['final_capital']:,.2f}")
        print(f"   Total Return: {results['total_return']:.2f}%")
        print(f"   Total Trades: {results['trades']}")
        
        performance = results['performance']
        print(f"\n📈 PERFORMANCE METRICS:")
        print(f"   Sharpe Ratio: {performance['sharpe_ratio']:.2f}")
        print(f"   Max Drawdown: {performance['max_drawdown']:.2f}%")
        print(f"   Win Rate: {performance['win_rate']:.2f}%")
        print(f"   Profit Factor: {performance['profit_factor']:.2f}")
        print(f"   Winning Trades: {performance['winning_trades']}")
        print(f"   Losing Trades: {performance['losing_trades']}")
        
        # Test strategy signals
        print("\n5. Testing strategy signals...")
        test_signals(data, strategy)
        
        print("\n🎉 BACKTESTING FRAMEWORK TEST COMPLETE!")
        print("=" * 50)
        print("✅ All components working correctly")
        print("✅ Ready for Phase 3.2: Strategy Framework")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

def test_signals(data, strategy):
    """Test strategy signal generation"""
    print("   Testing signal generation...")
    
    long_signals = 0
    exit_signals = 0
    
    for i in range(26, len(data)):  # Start after MACD warmup period
        current_data = data.iloc[:i+1]
        
        if strategy.should_enter_long(current_data, i):
            long_signals += 1
        
        if strategy.should_exit_long(current_data, i):
            exit_signals += 1
    
    print(f"   Long entry signals: {long_signals}")
    print(f"   Exit signals: {exit_signals}")
    print(f"   Signal frequency: {long_signals/len(data)*100:.2f}%")

if __name__ == "__main__":
    test_backtesting_framework() 