#!/usr/bin/env python3
"""
Test script for enhanced KPI calculations.
This script simulates the JavaScript KPI calculation logic to verify accuracy.
"""

import json
from datetime import datetime, timedelta

def calculate_enhanced_kpis(trades):
    """
    Calculate enhanced KPIs from trade data.
    This mirrors the JavaScript logic in dashboard.js
    """
    print("🔍 Testing Enhanced KPI Calculations")
    print("=" * 50)
    
    # Filter trades by action
    sell_trades = [t for t in trades if t['action'] == 'SELL']
    buy_trades = [t for t in trades if t['action'] == 'BUY']
    
    print(f"Total trades: {len(trades)}")
    print(f"BUY trades: {len(buy_trades)}")
    print(f"SELL trades: {len(sell_trades)}")
    
    # Calculate basic metrics
    winning_trades = [t for t in sell_trades if t.get('pnl', 0) > 0]
    win_rate = (len(winning_trades) / len(sell_trades) * 100) if sell_trades else 0
    
    print(f"Winning trades: {len(winning_trades)}")
    print(f"Win rate: {win_rate:.1f}%")
    
    # Calculate enhanced KPIs
    current_position_value = 0
    position_pnl = 0
    total_loss = 0
    total_profit = 0
    
    # Group trades by symbol to calculate position metrics
    positions = {}
    
    for trade in trades:
        symbol = trade['symbol']
        if symbol not in positions:
            positions[symbol] = {
                'buys': [],
                'sells': [],
                'total_shares': 0,
                'avg_buy_price': 0,
                'total_buy_value': 0,
                'total_buy_shares': 0
            }
        
        if trade['action'] == 'BUY':
            positions[symbol]['buys'].append(trade)
            positions[symbol]['total_shares'] += trade.get('shares', 0)
            positions[symbol]['total_buy_value'] += trade.get('value', 0)
            positions[symbol]['total_buy_shares'] += trade.get('shares', 0)
        elif trade['action'] == 'SELL':
            positions[symbol]['sells'].append(trade)
            positions[symbol]['total_shares'] -= trade.get('shares', 0)
    
    # Calculate position metrics for open positions
    open_positions = []
    for symbol, position in positions.items():
        if position['total_shares'] > 0:
            # Calculate average buy price for remaining shares
            position['avg_buy_price'] = position['total_buy_value'] / position['total_buy_shares']
            
            # Find the most recent price for this symbol
            symbol_trades = [t for t in trades if t['symbol'] == symbol]
            if symbol_trades:
                last_trade = symbol_trades[-1]
                current_price = last_trade.get('price', 0)
                
                current_position_value += current_price * position['total_shares']
                position_pnl += (current_price - position['avg_buy_price']) * position['total_shares']
                
                open_positions.append({
                    'symbol': symbol,
                    'shares': position['total_shares'],
                    'avg_price': position['avg_buy_price'],
                    'current_price': current_price,
                    'position_value': current_price * position['total_shares'],
                    'position_pnl': (current_price - position['avg_buy_price']) * position['total_shares']
                })
                
                print(f"📈 Open position {symbol}: {position['total_shares']} shares at avg ${position['avg_buy_price']:.2f}, current ${current_price:.2f}, P&L ${((current_price - position['avg_buy_price']) * position['total_shares']):.2f}")
    
    # Calculate total profit/loss from SELL trades (realized P&L)
    for trade in sell_trades:
        pnl = trade.get('pnl', 0)
        if pnl > 0:
            total_profit += pnl
        else:
            total_loss += abs(pnl)
    
    # Calculate summary metrics
    net_realized_pnl = total_profit - total_loss
    total_pnl = net_realized_pnl + position_pnl
    profit_factor = total_profit / total_loss if total_loss > 0 else (total_profit if total_profit > 0 else 0)
    
    print("\n📊 Enhanced KPI Results:")
    print("=" * 30)
    print(f"💰 Current Position Value: ${current_position_value:.2f}")
    print(f"📈 Position P&L: ${position_pnl:.2f}")
    print(f"📉 Total Loss: ${total_loss:.2f}")
    print(f"📊 Total Profit: ${total_profit:.2f}")
    print(f"💵 Net Realized P&L: ${net_realized_pnl:.2f}")
    print(f"📈 Total P&L (Realized + Unrealized): ${total_pnl:.2f}")
    print(f"📊 Profit Factor: {profit_factor:.2f}")
    print(f"🔢 Open Positions: {len(open_positions)}")
    
    return {
        'current_position_value': current_position_value,
        'position_pnl': position_pnl,
        'total_loss': total_loss,
        'total_profit': total_profit,
        'net_realized_pnl': net_realized_pnl,
        'total_pnl': total_pnl,
        'profit_factor': profit_factor,
        'open_positions': open_positions,
        'win_rate': win_rate
    }

def create_sample_trades():
    """
    Create sample trade data for testing
    """
    base_date = datetime(2024, 1, 1)
    
    trades = [
        # AAPL trades - some buys and sells
        {
            'date': (base_date + timedelta(days=1)).strftime('%Y-%m-%d'),
            'symbol': 'AAPL',
            'action': 'BUY',
            'shares': 10,
            'price': 150.00,
            'value': 1500.00,
            'pnl': 0.0
        },
        {
            'date': (base_date + timedelta(days=5)).strftime('%Y-%m-%d'),
            'symbol': 'AAPL',
            'action': 'BUY',
            'shares': 5,
            'price': 155.00,
            'value': 775.00,
            'pnl': 0.0
        },
        {
            'date': (base_date + timedelta(days=10)).strftime('%Y-%m-%d'),
            'symbol': 'AAPL',
            'action': 'SELL',
            'shares': 15,  # Sell all remaining shares (10 + 5)
            'price': 160.00,
            'value': 2400.00,
            'pnl': 125.00  # Profit (15 * 160) - (10*150 + 5*155) = 2400 - 2275 = 125
        },
        # MSFT trades - profitable
        {
            'date': (base_date + timedelta(days=2)).strftime('%Y-%m-%d'),
            'symbol': 'MSFT',
            'action': 'BUY',
            'shares': 8,
            'price': 300.00,
            'value': 2400.00,
            'pnl': 0.0
        },
        {
            'date': (base_date + timedelta(days=8)).strftime('%Y-%m-%d'),
            'symbol': 'MSFT',
            'action': 'SELL',
            'shares': 8,
            'price': 320.00,
            'value': 2560.00,
            'pnl': 160.00  # Profit
        },
        # TSLA trades - loss
        {
            'date': (base_date + timedelta(days=3)).strftime('%Y-%m-%d'),
            'symbol': 'TSLA',
            'action': 'BUY',
            'shares': 5,
            'price': 200.00,
            'value': 1000.00,
            'pnl': 0.0
        },
        {
            'date': (base_date + timedelta(days=7)).strftime('%Y-%m-%d'),
            'symbol': 'TSLA',
            'action': 'SELL',
            'shares': 5,
            'price': 180.00,
            'value': 900.00,
            'pnl': -100.00  # Loss
        },
        # GOOGL - open position
        {
            'date': (base_date + timedelta(days=4)).strftime('%Y-%m-%d'),
            'symbol': 'GOOGL',
            'action': 'BUY',
            'shares': 3,
            'price': 140.00,
            'value': 420.00,
            'pnl': 0.0
        },
        {
            'date': (base_date + timedelta(days=6)).strftime('%Y-%m-%d'),
            'symbol': 'GOOGL',
            'action': 'BUY',
            'shares': 2,
            'price': 145.00,
            'value': 290.00,
            'pnl': 0.0
        }
    ]
    
    return trades

if __name__ == "__main__":
    # Create sample trade data
    sample_trades = create_sample_trades()
    
    # Calculate enhanced KPIs
    results = calculate_enhanced_kpis(sample_trades)
    
    print("\n✅ Enhanced KPI calculation test completed!")
    print("Expected results:")
    print("- Current Position Value: Should show value of GOOGL position (5 shares * last price)")
    print("- Position P&L: Should show unrealized P&L on GOOGL position")
    print("- Total Loss: Should show $100 (TSLA loss)")
    print("- Total Profit: Should show $285 (AAPL + MSFT profits)")
    print("- Net Realized P&L: Should show $185 (285 - 100)")
    print("- Profit Factor: Should show 2.85 (285/100)") 