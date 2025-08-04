#!/usr/bin/env python3
"""
Comprehensive P&L Analysis
Calculates realized P&L from completed trades and unrealized P&L from current positions
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data_engine.data_cache import DataCache
import pandas as pd
import numpy as np
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def calculate_comprehensive_pnl():
    """Calculate comprehensive P&L including realized and unrealized gains/losses."""
    
    print("💰 COMPREHENSIVE P&L ANALYSIS")
    print("=" * 60)
    
    # Get data cache
    cache = DataCache()
    
    # Get all transactions
    all_transactions = cache.get_transaction_history()
    
    if all_transactions.empty:
        print("❌ No transactions found!")
        return
    
    print(f"📊 Total transactions: {len(all_transactions)}")
    
    # Convert date column to datetime
    all_transactions['date'] = pd.to_datetime(all_transactions['date'])
    
    # Sort by date
    all_transactions = all_transactions.sort_values('date')
    
    # Initialize tracking
    positions = {}  # Current open positions
    realized_pnl = {}  # Realized P&L per symbol
    trade_history = {}  # All trades per symbol
    
    print(f"\n📈 ANALYZING TRADES...")
    
    # Process each transaction
    for _, trade in all_transactions.iterrows():
        symbol = trade['symbol']
        action = trade['action']
        shares = trade['shares']
        price = trade['price']
        value = trade['value']
        date = trade['date']
        
        # Initialize symbol tracking
        if symbol not in trade_history:
            trade_history[symbol] = []
            realized_pnl[symbol] = 0.0
        
        trade_record = {
            'date': date,
            'action': action,
            'shares': shares,
            'price': price,
            'value': value
        }
        trade_history[symbol].append(trade_record)
        
        if action == 'BUY':
            # Add to positions
            if symbol not in positions:
                positions[symbol] = {
                    'shares': shares,
                    'avg_price': price,
                    'total_cost': value,
                    'last_price': price,
                    'last_date': date
                }
            else:
                # Update existing position
                pos = positions[symbol]
                total_shares = pos['shares'] + shares
                total_cost = pos['total_cost'] + value
                pos['shares'] = total_shares
                pos['avg_price'] = total_cost / total_shares
                pos['total_cost'] = total_cost
                pos['last_price'] = price
                pos['last_date'] = date
                
        elif action == 'SELL':
            if symbol in positions:
                pos = positions[symbol]
                
                # Calculate realized P&L for this sell
                shares_to_sell = min(shares, pos['shares'])
                if shares_to_sell > 0:
                    # Calculate P&L
                    cost_basis = pos['avg_price'] * shares_to_sell
                    sale_proceeds = price * shares_to_sell
                    trade_pnl = sale_proceeds - cost_basis
                    realized_pnl[symbol] += trade_pnl
                    
                    print(f"💰 {symbol}: SELL {shares_to_sell} shares at ${price:.2f} (avg cost: ${pos['avg_price']:.2f}) - P&L: ${trade_pnl:.2f}")
                    
                    # Update position
                    pos['shares'] -= shares_to_sell
                    if pos['shares'] <= 0:
                        # Position closed
                        del positions[symbol]
                        print(f"   ✅ Position closed for {symbol}")
                    else:
                        # Partial position remains
                        pos['total_cost'] = pos['avg_price'] * pos['shares']
                        print(f"   📊 Remaining position: {pos['shares']} shares")
    
    print(f"\n📊 REALIZED P&L SUMMARY")
    print("-" * 40)
    
    total_realized_pnl = 0
    for symbol, pnl in realized_pnl.items():
        if pnl != 0:
            print(f"   {symbol}: ${pnl:.2f}")
            total_realized_pnl += pnl
    
    print(f"   Total Realized P&L: ${total_realized_pnl:.2f}")
    
    print(f"\n📈 CURRENT POSITIONS (Unrealized P&L)")
    print("-" * 40)
    
    total_unrealized_pnl = 0
    total_position_value = 0
    
    for symbol, pos in positions.items():
        current_value = pos['shares'] * pos['last_price']
        unrealized_pnl = current_value - (pos['shares'] * pos['avg_price'])
        
        print(f"   {symbol}:")
        print(f"     Shares: {pos['shares']}")
        print(f"     Avg Cost: ${pos['avg_price']:.2f}")
        print(f"     Current Price: ${pos['last_price']:.2f}")
        print(f"     Position Value: ${current_value:.2f}")
        print(f"     Unrealized P&L: ${unrealized_pnl:.2f}")
        
        total_unrealized_pnl += unrealized_pnl
        total_position_value += current_value
    
    print(f"\n💰 TOTAL PORTFOLIO SUMMARY")
    print("-" * 40)
    print(f"   Realized P&L: ${total_realized_pnl:.2f}")
    print(f"   Unrealized P&L: ${total_unrealized_pnl:.2f}")
    print(f"   Total P&L: ${total_realized_pnl + total_unrealized_pnl:.2f}")
    print(f"   Current Position Value: ${total_position_value:.2f}")
    
    # Calculate performance metrics
    if total_realized_pnl != 0 or total_unrealized_pnl != 0:
        total_pnl = total_realized_pnl + total_unrealized_pnl
        
        # Estimate initial capital (rough calculation)
        total_buy_value = sum(trade['value'] for trades in trade_history.values() 
                             for trade in trades if trade['action'] == 'BUY')
        
        if total_buy_value > 0:
            total_return_pct = (total_pnl / total_buy_value) * 100
            print(f"   Total Return: {total_return_pct:.2f}%")
    
    print(f"\n📋 DETAILED TRADE ANALYSIS BY SYMBOL")
    print("-" * 40)
    
    for symbol, trades in trade_history.items():
        buy_trades = [t for t in trades if t['action'] == 'BUY']
        sell_trades = [t for t in trades if t['action'] == 'SELL']
        
        if len(buy_trades) > 0 or len(sell_trades) > 0:
            print(f"\n   {symbol}:")
            print(f"     BUY trades: {len(buy_trades)}")
            print(f"     SELL trades: {len(sell_trades)}")
            
            if len(buy_trades) > 0:
                avg_buy_price = sum(t['price'] for t in buy_trades) / len(buy_trades)
                total_buy_value = sum(t['value'] for t in buy_trades)
                print(f"     Avg BUY price: ${avg_buy_price:.2f}")
                print(f"     Total BUY value: ${total_buy_value:.2f}")
            
            if len(sell_trades) > 0:
                avg_sell_price = sum(t['price'] for t in sell_trades) / len(sell_trades)
                total_sell_value = sum(t['value'] for t in sell_trades)
                print(f"     Avg SELL price: ${avg_sell_price:.2f}")
                print(f"     Total SELL value: ${total_sell_value:.2f}")
            
            if symbol in realized_pnl:
                print(f"     Realized P&L: ${realized_pnl[symbol]:.2f}")
            
            if symbol in positions:
                pos = positions[symbol]
                unrealized = (pos['last_price'] - pos['avg_price']) * pos['shares']
                print(f"     Unrealized P&L: ${unrealized:.2f}")
                print(f"     Current position: {pos['shares']} shares at ${pos['last_price']:.2f}")

if __name__ == "__main__":
    calculate_comprehensive_pnl() 