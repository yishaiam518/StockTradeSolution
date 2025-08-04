#!/usr/bin/env python3
"""
Trade Report Generator with P&L Analysis

Generates a comprehensive report showing all trades with their P&L calculations.
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.backtesting.backtest_engine import BacktestEngine
from src.utils.logger import get_logger

def generate_trade_report_with_pnl():
    """Generate a comprehensive trade report with P&L analysis."""
    
    logger = get_logger(__name__)
    logger.info("Generating comprehensive trade report with P&L analysis...")
    
    # Run a historical backtest to get trade data
    backtest_engine = BacktestEngine()
    
    # Run the backtest
    results = backtest_engine.run_historical_backtest(
        strategy="MACD",
        profile="balanced",
        start_date="2023-01-01",
        end_date="2023-12-31",
        benchmark="SPY"
    )
    
    if not results or 'trades' not in results:
        logger.error("No trade data available for report generation")
        return
    
    trades = results['trades']
    logger.info(f"Processing {len(trades)} trades for P&L analysis...")
    
    # Create detailed trade analysis
    trade_analysis = []
    running_pnl = 0.0
    total_buy_value = 0.0
    total_sell_value = 0.0
    
    # Group trades by symbol to calculate P&L
    symbol_positions = {}
    
    for i, trade in enumerate(trades):
        symbol = trade['symbol']
        action = trade['action']
        shares = trade['shares']
        price = trade['price']
        value = trade['value']
        date = trade['date']
        
        # Initialize symbol tracking if not exists
        if symbol not in symbol_positions:
            symbol_positions[symbol] = {
                'total_shares': 0.0,
                'total_cost': 0.0,
                'avg_price': 0.0,
                'pnl': 0.0,
                'trades': []
            }
        
        position = symbol_positions[symbol]
        
        if action == 'BUY':
            # Update position
            old_shares = position['total_shares']
            old_cost = position['total_cost']
            
            position['total_shares'] += shares
            position['total_cost'] += value
            position['avg_price'] = position['total_cost'] / position['total_shares']
            
            total_buy_value += value
            
            # Calculate running P&L (no P&L on buy, just track position)
            trade_pnl = 0.0
            running_pnl += trade_pnl
            
            trade_analysis.append({
                'trade_id': i + 1,
                'date': date,
                'symbol': symbol,
                'action': action,
                'shares': shares,
                'price': price,
                'value': value,
                'running_pnl': running_pnl,
                'trade_pnl': trade_pnl,
                'position_shares': position['total_shares'],
                'position_avg_price': position['avg_price'],
                'position_value': position['total_cost']
            })
            
        elif action == 'SELL':
            # Calculate P&L for this sell
            if position['total_shares'] > 0:
                # Calculate realized P&L
                realized_pnl = (price - position['avg_price']) * shares
                trade_pnl = realized_pnl
                running_pnl += trade_pnl
                
                # Update position
                position['total_shares'] -= shares
                position['total_cost'] -= (position['avg_price'] * shares)
                
                if position['total_shares'] > 0:
                    position['avg_price'] = position['total_cost'] / position['total_shares']
                else:
                    position['avg_price'] = 0.0
                
                total_sell_value += value
                
                trade_analysis.append({
                    'trade_id': i + 1,
                    'date': date,
                    'symbol': symbol,
                    'action': action,
                    'shares': shares,
                    'price': price,
                    'value': value,
                    'running_pnl': running_pnl,
                    'trade_pnl': trade_pnl,
                    'realized_pnl': realized_pnl,
                    'position_shares': position['total_shares'],
                    'position_avg_price': position['avg_price'],
                    'position_value': position['total_cost']
                })
    
    # Create summary statistics
    summary_stats = {
        'total_trades': len(trades),
        'buy_trades': len([t for t in trades if t['action'] == 'BUY']),
        'sell_trades': len([t for t in trades if t['action'] == 'SELL']),
        'total_buy_value': total_buy_value,
        'total_sell_value': total_sell_value,
        'final_pnl': running_pnl,
        'pnl_percentage': (running_pnl / total_buy_value * 100) if total_buy_value > 0 else 0,
        'unique_symbols': len(symbol_positions),
        'final_portfolio_value': results.get('final_portfolio_value', 0)
    }
    
    # Generate the report
    report = generate_report_text(trade_analysis, summary_stats, symbol_positions)
    
    # Save report to file
    with open('comprehensive_trade_report.txt', 'w') as f:
        f.write(report)
    
    logger.info("Comprehensive trade report generated: comprehensive_trade_report.txt")
    return report

def generate_report_text(trade_analysis, summary_stats, symbol_positions):
    """Generate formatted report text."""
    
    report = []
    report.append("=" * 80)
    report.append("COMPREHENSIVE TRADE REPORT WITH P&L ANALYSIS")
    report.append("=" * 80)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # Summary Statistics
    report.append("📊 SUMMARY STATISTICS")
    report.append("-" * 40)
    report.append(f"Total Trades: {summary_stats['total_trades']}")
    report.append(f"Buy Trades: {summary_stats['buy_trades']}")
    report.append(f"Sell Trades: {summary_stats['sell_trades']}")
    report.append(f"Total Buy Value: ${summary_stats['total_buy_value']:,.2f}")
    report.append(f"Total Sell Value: ${summary_stats['total_sell_value']:,.2f}")
    report.append(f"Final P&L: ${summary_stats['final_pnl']:,.2f}")
    report.append(f"P&L Percentage: {summary_stats['pnl_percentage']:.2f}%")
    report.append(f"Unique Symbols Traded: {summary_stats['unique_symbols']}")
    report.append(f"Final Portfolio Value: ${summary_stats['final_portfolio_value']:,.2f}")
    report.append("")
    
    # Symbol-wise P&L Summary
    report.append("📈 SYMBOL-WISE P&L SUMMARY")
    report.append("-" * 40)
    
    symbol_pnl_summary = []
    for symbol, position in symbol_positions.items():
        if position['total_shares'] == 0:  # Closed positions only
            symbol_pnl_summary.append({
                'symbol': symbol,
                'total_pnl': position['pnl'],
                'trades_count': len(position['trades'])
            })
    
    # Sort by P&L
    symbol_pnl_summary.sort(key=lambda x: x['total_pnl'], reverse=True)
    
    for item in symbol_pnl_summary:
        report.append(f"{item['symbol']}: ${item['total_pnl']:,.2f} ({item['trades_count']} trades)")
    
    report.append("")
    
    # Detailed Trade Log (first 50 trades)
    report.append("📋 DETAILED TRADE LOG (First 50 Trades)")
    report.append("-" * 40)
    report.append(f"{'ID':<4} {'Date':<12} {'Symbol':<6} {'Action':<4} {'Shares':<8} {'Price':<8} {'Value':<10} {'P&L':<10} {'Running P&L':<12}")
    report.append("-" * 80)
    
    for trade in trade_analysis[:50]:
        pnl_str = f"${trade['trade_pnl']:,.2f}" if trade['trade_pnl'] != 0 else "N/A"
        running_pnl_str = f"${trade['running_pnl']:,.2f}"
        
        report.append(
            f"{trade['trade_id']:<4} {trade['date']:<12} {trade['symbol']:<6} "
            f"{trade['action']:<4} {trade['shares']:<8.2f} ${trade['price']:<7.2f} "
            f"${trade['value']:<9.2f} {pnl_str:<10} {running_pnl_str:<12}"
        )
    
    if len(trade_analysis) > 50:
        report.append(f"... and {len(trade_analysis) - 50} more trades")
    
    report.append("")
    
    # P&L Analysis
    report.append("💰 P&L ANALYSIS")
    report.append("-" * 40)
    
    # Calculate P&L metrics
    profitable_trades = [t for t in trade_analysis if t.get('trade_pnl', 0) > 0]
    losing_trades = [t for t in trade_analysis if t.get('trade_pnl', 0) < 0]
    
    report.append(f"Profitable Trades: {len(profitable_trades)}")
    report.append(f"Losing Trades: {len(losing_trades)}")
    report.append(f"Win Rate: {len(profitable_trades) / len(trade_analysis) * 100:.1f}%")
    
    if profitable_trades:
        avg_profit = sum(t['trade_pnl'] for t in profitable_trades) / len(profitable_trades)
        report.append(f"Average Profit per Trade: ${avg_profit:,.2f}")
    
    if losing_trades:
        avg_loss = sum(t['trade_pnl'] for t in losing_trades) / len(losing_trades)
        report.append(f"Average Loss per Trade: ${avg_loss:,.2f}")
    
    report.append("")
    report.append("=" * 80)
    report.append("END OF REPORT")
    report.append("=" * 80)
    
    return "\n".join(report)

if __name__ == "__main__":
    report = generate_trade_report_with_pnl()
    print(report) 