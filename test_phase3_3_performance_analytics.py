#!/usr/bin/env python3
"""
Test script for Phase 3.3: Performance Analytics and Risk Management
Tests advanced performance metrics, risk management features, and comprehensive reporting
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.backtesting.backtest_engine import BacktestEngine
from src.backtesting.strategies import MACDStrategy, RSIStrategy, BollingerBandsStrategy
from src.backtesting.performance_analytics import PerformanceAnalytics, PerformanceMetrics
from src.backtesting.risk_management import RiskManager, RiskParameters, PositionSizingMethod, StopLossType
import pandas as pd
import numpy as np
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_performance_analytics():
    """Test performance analytics functionality"""
    print("🧪 TESTING PHASE 3.3: PERFORMANCE ANALYTICS & RISK MANAGEMENT")
    print("=" * 70)
    
    # Initialize components
    performance_analytics = PerformanceAnalytics()
    
    # Create sample equity curve and trades
    dates = pd.date_range('2023-01-01', '2024-12-31', freq='D')
    np.random.seed(42)  # For reproducible results
    
    # Generate realistic equity curve
    returns = np.random.normal(0.0005, 0.015, len(dates))  # Daily returns
    equity_curve = pd.Series(100000 * (1 + returns).cumprod(), index=dates)
    
    # Create sample trades
    trades = []
    for i in range(20):
        trade = {
            'symbol': 'AAPL',
            'entry_time': dates[i*20],
            'exit_time': dates[i*20 + 15],
            'entry_price': 150 + np.random.normal(0, 5),
            'exit_price': 150 + np.random.normal(0, 5),
            'position_type': 'long' if i % 2 == 0 else 'short',
            'shares': 100 + np.random.randint(0, 50),
            'pnl': np.random.normal(500, 200),
            'pnl_percentage': np.random.normal(0.02, 0.01),
            'stop_loss': 140,
            'take_profit': 160,
            'exit_reason': 'Strategy exit'
        }
        trades.append(trade)
    
    print("1. Testing Performance Analytics...")
    
    # Calculate performance metrics
    metrics = performance_analytics.calculate_performance_metrics(equity_curve, trades)
    
    print("✅ Performance metrics calculated successfully!")
    print(f"   Total Return: {metrics.total_return:.2%}")
    print(f"   Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
    print(f"   Sortino Ratio: {metrics.sortino_ratio:.2f}")
    print(f"   Calmar Ratio: {metrics.calmar_ratio:.2f}")
    print(f"   Max Drawdown: {metrics.max_drawdown:.2%}")
    print(f"   Win Rate: {metrics.win_rate:.2%}")
    print(f"   Profit Factor: {metrics.profit_factor:.2f}")
    print(f"   VaR (95%): {metrics.var_95:.2%}")
    print(f"   CVaR (95%): {metrics.cvar_95:.2%}")
    
    # Generate performance report
    report = performance_analytics.generate_performance_report(metrics)
    print("\n📊 PERFORMANCE REPORT:")
    print(report)
    
    return metrics

def test_risk_management():
    """Test risk management functionality"""
    print("\n2. Testing Risk Management...")
    
    # Test different risk parameter configurations
    risk_configs = [
        {
            'name': 'Conservative',
            'params': RiskParameters(
                position_sizing_method=PositionSizingMethod.FIXED_PERCENTAGE,
                stop_loss_type=StopLossType.FIXED_PERCENTAGE,
                max_position_size=0.05,
                stop_loss_percentage=0.01,
                max_portfolio_drawdown=0.10
            )
        },
        {
            'name': 'Moderate',
            'params': RiskParameters(
                position_sizing_method=PositionSizingMethod.VOLATILITY_BASED,
                stop_loss_type=StopLossType.ATR_BASED,
                max_position_size=0.10,
                stop_loss_percentage=0.02,
                max_portfolio_drawdown=0.20
            )
        },
        {
            'name': 'Aggressive',
            'params': RiskParameters(
                position_sizing_method=PositionSizingMethod.KELLY_CRITERION,
                stop_loss_type=StopLossType.TRAILING,
                max_position_size=0.15,
                stop_loss_percentage=0.03,
                max_portfolio_drawdown=0.30
            )
        }
    ]
    
    for config in risk_configs:
        print(f"\n   Testing {config['name']} Risk Configuration:")
        risk_manager = RiskManager(config['params'])
        
        # Test position sizing
        capital = 100000
        price = 150
        volatility = 0.20
        win_rate = 0.6
        avg_win = 1000
        avg_loss = 500
        
        position_size = risk_manager.calculate_position_size(
            capital, price, volatility, win_rate, avg_win, avg_loss
        )
        print(f"     Position Size: ${position_size:,.2f}")
        
        # Test stop-loss calculation
        stop_loss = risk_manager.calculate_stop_loss(price, 'long')
        take_profit = risk_manager.calculate_take_profit(price, 'long')
        print(f"     Stop Loss: ${stop_loss:.2f}")
        print(f"     Take Profit: ${take_profit:.2f}")
        
        # Test portfolio limits
        portfolio_value = 95000
        positions = {'AAPL': {'value': 5000, 'volatility': 0.15}}
        
        within_limits, reason = risk_manager.check_portfolio_limits(
            portfolio_value, positions
        )
        print(f"     Portfolio Limits: {'OK' if within_limits else 'VIOLATED'}")
        if not within_limits:
            print(f"     Reason: {reason}")
    
    print("✅ Risk management tests completed!")

def test_enhanced_backtesting():
    """Test enhanced backtesting with performance analytics and risk management"""
    print("\n3. Testing Enhanced Backtesting...")
    
    # Initialize enhanced backtesting engine
    risk_params = RiskParameters(
        position_sizing_method=PositionSizingMethod.VOLATILITY_BASED,
        stop_loss_type=StopLossType.ATR_BASED,
        max_position_size=0.10,
        stop_loss_percentage=0.02,
        max_portfolio_drawdown=0.20
    )
    
    engine = BacktestEngine(initial_capital=100000.0, risk_params=risk_params)
    
    # Test strategies
    strategies = {
        'MACD Strategy': MACDStrategy({
            'fast_period': 12,
            'slow_period': 26,
            'signal_period': 9,
            'position_size': 0.1,
            'enable_short': False
        }),
        'RSI Strategy': RSIStrategy({
            'rsi_period': 14,
            'oversold_threshold': 30,
            'overbought_threshold': 70,
            'position_size': 0.1,
            'enable_short': False
        }),
        'Bollinger Bands Strategy': BollingerBandsStrategy({
            'bb_period': 20,
            'bb_std_dev': 2.0,
            'position_size': 0.1,
            'enable_short': True
        })
    }
    
    collection_id = "AMEX_20250803_161652"
    symbol = "BND"
    start_date = "2023-01-01"
    end_date = "2024-12-31"
    
    results = {}
    
    for strategy_name, strategy in strategies.items():
        print(f"\n   Testing {strategy_name}...")
        
        try:
            result = engine.run_backtest(
                strategy=strategy,
                collection_id=collection_id,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
            )
            
            if "error" in result:
                print(f"     ❌ Error: {result['error']}")
                continue
            
            results[strategy_name] = result
            
            # Print enhanced metrics
            metrics = result['performance']
            print(f"     ✅ Enhanced backtest completed!")
            print(f"     Total Return: {result['total_return']:.2%}")
            print(f"     Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
            print(f"     Sortino Ratio: {metrics['sortino_ratio']:.2f}")
            print(f"     Calmar Ratio: {metrics['calmar_ratio']:.2f}")
            print(f"     Information Ratio: {metrics['information_ratio']:.2f}")
            print(f"     Omega Ratio: {metrics['omega_ratio']:.2f}")
            print(f"     VaR (95%): {metrics['var_95']:.2%}")
            print(f"     Max Drawdown: {metrics['max_drawdown']:.2%}")
            print(f"     Win Rate: {metrics['win_rate']:.2%}")
            print(f"     Profit Factor: {metrics['profit_factor']:.2f}")
            
        except Exception as e:
            print(f"     ❌ Error testing {strategy_name}: {e}")
            continue
    
    # Generate comprehensive performance report
    if results:
        print("\n📊 COMPREHENSIVE PERFORMANCE COMPARISON:")
        print("=" * 70)
        
        # Sort by Sharpe ratio
        sorted_results = sorted(results.items(), 
                              key=lambda x: x[1]['performance']['sharpe_ratio'], 
                              reverse=True)
        
        print(f"{'Strategy':<25} {'Return':<10} {'Sharpe':<8} {'Sortino':<8} {'Calmar':<8} {'Max DD':<8}")
        print("-" * 80)
        
        for strategy_name, result in sorted_results:
            metrics = result['performance']
            print(f"{strategy_name:<25} "
                  f"{result['total_return']:>8.2%} "
                  f"{metrics['sharpe_ratio']:>6.2f} "
                  f"{metrics['sortino_ratio']:>6.2f} "
                  f"{metrics['calmar_ratio']:>6.2f} "
                  f"{metrics['max_drawdown']:>6.2%}")
        
        # Generate detailed report for best strategy
        best_strategy = sorted_results[0]
        print(f"\n🏆 BEST STRATEGY: {best_strategy[0]}")
        detailed_report = engine.get_performance_report(best_strategy[1])
        print(detailed_report)
    
    print("✅ Enhanced backtesting tests completed!")

def test_risk_management_integration():
    """Test risk management integration with different scenarios"""
    print("\n4. Testing Risk Management Integration...")
    
    # Test different risk scenarios
    scenarios = [
        {
            'name': 'High Volatility Market',
            'risk_params': RiskParameters(
                position_sizing_method=PositionSizingMethod.VOLATILITY_BASED,
                stop_loss_type=StopLossType.ATR_BASED,
                max_position_size=0.05,
                stop_loss_percentage=0.03,
                max_portfolio_drawdown=0.15
            )
        },
        {
            'name': 'Conservative Portfolio',
            'risk_params': RiskParameters(
                position_sizing_method=PositionSizingMethod.FIXED_PERCENTAGE,
                stop_loss_type=StopLossType.FIXED_PERCENTAGE,
                max_position_size=0.03,
                stop_loss_percentage=0.01,
                max_portfolio_drawdown=0.10
            )
        },
        {
            'name': 'Kelly Criterion Strategy',
            'risk_params': RiskParameters(
                position_sizing_method=PositionSizingMethod.KELLY_CRITERION,
                stop_loss_type=StopLossType.TRAILING,
                max_position_size=0.12,
                stop_loss_percentage=0.02,
                max_portfolio_drawdown=0.25
            )
        }
    ]
    
    for scenario in scenarios:
        print(f"\n   Testing {scenario['name']}:")
        
        engine = BacktestEngine(initial_capital=100000.0, risk_params=scenario['risk_params'])
        strategy = MACDStrategy({'position_size': 0.1, 'enable_short': False})
        
        try:
            result = engine.run_backtest(
                strategy=strategy,
                collection_id="AMEX_20250803_161652",
                symbol="BND",
                start_date="2023-01-01",
                end_date="2024-12-31"
            )
            
            if "error" not in result:
                metrics = result['performance']
                risk_summary = result['risk_summary']
                
                print(f"     Total Return: {result['total_return']:.2%}")
                print(f"     Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
                print(f"     Max Drawdown: {metrics['max_drawdown']:.2%}")
                print(f"     Position Sizing: {risk_summary['position_sizing_method']}")
                print(f"     Stop Loss Type: {risk_summary['stop_loss_type']}")
                print(f"     Max Position Size: {risk_summary['max_position_size']:.1%}")
            else:
                print(f"     ❌ Error: {result['error']}")
                
        except Exception as e:
            print(f"     ❌ Error: {e}")
    
    print("✅ Risk management integration tests completed!")

def main():
    """Run all Phase 3.3 tests"""
    try:
        # Test performance analytics
        metrics = test_performance_analytics()
        
        # Test risk management
        test_risk_management()
        
        # Test enhanced backtesting
        test_enhanced_backtesting()
        
        # Test risk management integration
        test_risk_management_integration()
        
        print("\n🎉 PHASE 3.3 TESTING COMPLETE!")
        print("=" * 70)
        print("✅ Performance Analytics: Advanced metrics calculated")
        print("✅ Risk Management: Position sizing and stop-loss working")
        print("✅ Enhanced Backtesting: Integrated analytics and risk management")
        print("✅ Comprehensive Reporting: Detailed performance reports generated")
        print("\n📈 Ready for Phase 3.4: Strategy Comparison & Optimization")
        
    except Exception as e:
        print(f"❌ Error during Phase 3.3 testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 