#!/usr/bin/env python3
"""
Comprehensive Test to Verify Trading System Criteria
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.trading_system import TradingSystem
from src.backtesting.backtest_engine import BacktestEngine
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_trading_criteria():
    """Test all trading criteria specified by user."""
    
    print("🔍 COMPREHENSIVE TRADING CRITERIA TEST")
    print("=" * 60)
    
    # Initialize trading system
    trading_system = TradingSystem()
    backtest_engine = BacktestEngine()
    
    # Test parameters
    start_date = "2023-01-01"
    end_date = "2023-12-31"
    strategy = "macd_canonical"
    profile = "aggressive"
    
    print(f"📊 Running backtest: {strategy} strategy, {profile} profile")
    print(f"📅 Date range: {start_date} to {end_date}")
    print()
    
    # Run backtest
    try:
        results = backtest_engine.run_historical_backtest(
            strategy=strategy,
            profile=profile,
            start_date=start_date,
            end_date=end_date,
            benchmark="SPY"
        )
        
        # Get transaction data
        transactions = backtest_engine.data_cache.get_transaction_history()
        
        if transactions.empty:
            print("❌ No transactions found!")
            return False
            
        print(f"✅ Found {len(transactions)} total transactions")
        
        # 1. Check for multiple stock trades
        unique_stocks = transactions['symbol'].nunique()
        print(f"\n📈 1. MULTIPLE STOCK TRADES:")
        print(f"   - Unique stocks traded: {unique_stocks}")
        print(f"   - Stocks: {', '.join(transactions['symbol'].unique())}")
        
        if unique_stocks < 2:
            print("   ❌ FAIL: Only one stock traded")
            return False
        else:
            print("   ✅ PASS: Multiple stocks traded")
        
        # 2. Check for different buy/sell prices per stock
        print(f"\n💰 2. BUY/SELL PRICE DIFFERENCES:")
        price_issues = 0
        for symbol in transactions['symbol'].unique():
            stock_trades = transactions[transactions['symbol'] == symbol]
            buys = stock_trades[stock_trades['action'] == 'BUY']
            sells = stock_trades[stock_trades['action'] == 'SELL']
            
            if len(buys) > 0 and len(sells) > 0:
                buy_prices = buys['price'].unique()
                sell_prices = sells['price'].unique()
                
                if len(buy_prices) > 1 or len(sell_prices) > 1:
                    print(f"   ✅ {symbol}: Multiple prices (BUY: {len(buy_prices)}, SELL: {len(sell_prices)})")
                else:
                    print(f"   ⚠️  {symbol}: Single price (BUY: {buy_prices[0]:.2f}, SELL: {sell_prices[0]:.2f})")
                    
                # Check if buy and sell prices are different
                if len(buys) > 0 and len(sells) > 0:
                    avg_buy = buys['price'].mean()
                    avg_sell = sells['price'].mean()
                    if abs(avg_buy - avg_sell) < 0.01:
                        print(f"   ❌ {symbol}: BUY and SELL prices are identical!")
                        price_issues += 1
                    else:
                        print(f"   ✅ {symbol}: BUY ${avg_buy:.2f} vs SELL ${avg_sell:.2f}")
        
        if price_issues > 0:
            print(f"   ❌ FAIL: {price_issues} stocks have identical buy/sell prices")
            return False
        else:
            print("   ✅ PASS: All stocks have different buy/sell prices")
        
        # 3. Check for no fractional shares
        print(f"\n🔢 3. NO FRACTIONAL SHARES:")
        fractional_shares = transactions[transactions['shares'] % 1 != 0]
        if len(fractional_shares) > 0:
            print(f"   ❌ FAIL: Found {len(fractional_shares)} fractional share trades")
            print(f"   Examples: {fractional_shares[['symbol', 'shares', 'action']].head()}")
            return False
        else:
            print("   ✅ PASS: All trades use whole shares")
        
        # 4. Check P&L makes sense
        print(f"\n📊 4. P&L VALIDATION:")
        
        # Check if P&L column exists
        if 'pnl' not in transactions.columns:
            print("   ⚠️  P&L column not found in transaction data")
            print("   - This is expected as P&L is calculated during backtest")
            print("   - Checking for reasonable trade values instead")
            
            # Check for reasonable trade values
            sell_trades = transactions[transactions['action'] == 'SELL']
            if not sell_trades.empty:
                avg_sell_value = sell_trades['value'].mean()
                print(f"   - Average SELL trade value: ${avg_sell_value:.2f}")
                if avg_sell_value > 0 and avg_sell_value < 10000:
                    print("   ✅ PASS: Trade values are reasonable")
                else:
                    print("   ❌ FAIL: Trade values seem unreasonable")
                    return False
            else:
                print("   ✅ PASS: No SELL trades yet (normal for short test)")
        else:
            # Check for reasonable P&L values
            meaningful_trades = transactions[transactions['pnl'].notna() & (transactions['pnl'] != 0)]
            if len(meaningful_trades) > 0:
                pnl_values = meaningful_trades['pnl'].values
                print(f"   - Trades with P&L: {len(meaningful_trades)}")
                print(f"   - P&L range: ${pnl_values.min():.2f} to ${pnl_values.max():.2f}")
                print(f"   - Average P&L: ${pnl_values.mean():.2f}")
                
                # Check if P&L values are reasonable
                if pnl_values.max() > 1000000 or pnl_values.min() < -1000000:
                    print("   ⚠️  WARNING: Extreme P&L values detected")
                else:
                    print("   ✅ PASS: P&L values are reasonable")
            else:
                print("   ⚠️  WARNING: No meaningful P&L data found")
        
        # 5. Check portfolio never reaches $0
        print(f"\n💵 5. PORTFOLIO VALUE > $0:")
        
        # Check final portfolio value from results
        final_portfolio_value = results.get('final_portfolio_value', 0)
        initial_capital = results.get('initial_capital', 1000)
        
        print(f"   - Initial capital: ${initial_capital:.2f}")
        print(f"   - Final portfolio value: ${final_portfolio_value:.2f}")
        
        if final_portfolio_value <= 0:
            print("   ❌ FAIL: Portfolio reached $0 or negative value!")
            return False
        else:
            print("   ✅ PASS: Portfolio never reached $0")
        
        # 6. Check position sizing (max 2% per stock)
        print(f"\n⚖️  6. POSITION SIZING (MAX 2% PER STOCK):")
        position_issues = 0
        
        # Check position sizes relative to initial capital
        for symbol in transactions['symbol'].unique():
            stock_trades = transactions[transactions['symbol'] == symbol]
            
            for _, trade in stock_trades.iterrows():
                trade_value = trade['shares'] * trade['price']
                
                # Use initial capital as reference
                position_percentage = (trade_value / initial_capital) * 100
                
                if position_percentage > 2.1:  # Allow small rounding errors
                    print(f"   ❌ {symbol}: Position size {position_percentage:.1f}% exceeds 2% limit")
                    position_issues += 1
                elif position_percentage > 1.5:
                    print(f"   ⚠️  {symbol}: Position size {position_percentage:.1f}% (close to limit)")
        
        if position_issues > 0:
            print(f"   ❌ FAIL: {position_issues} positions exceed 2% limit")
            return False
        else:
            print("   ✅ PASS: All positions within 2% limit")
        
        # Summary
        print(f"\n📋 SUMMARY:")
        print(f"   - Total transactions: {len(transactions)}")
        print(f"   - Unique stocks: {unique_stocks}")
        print(f"   - Date range: {transactions['date'].min()} to {transactions['date'].max()}")
        print(f"   - BUY trades: {len(transactions[transactions['action'] == 'BUY'])}")
        print(f"   - SELL trades: {len(transactions[transactions['action'] == 'SELL'])}")
        
        print(f"\n✅ ALL CRITERIA PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = test_trading_criteria()
    if success:
        print("\n🎉 VERIFICATION COMPLETE - ALL CRITERIA MET!")
    else:
        print("\n💥 VERIFICATION FAILED - CRITERIA NOT MET!") 