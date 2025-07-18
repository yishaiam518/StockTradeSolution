#!/usr/bin/env python3
"""
Enhanced Trade Report Generator for StockTradeSolution
Generates comprehensive reports with multiple trades and their values
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def generate_sample_trades():
    """Generate sample trade data for demonstration"""
    trades = []
    
    # Generate 25 sample trades with more realistic data
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMD', 'INTC', 'SPY', 'QQQ']
    strategies = ['MACDCanonical', 'MACDAggressive', 'MACDConservative']
    profiles = ['conservative', 'moderate', 'aggressive']
    
    for i in range(25):
        symbol = np.random.choice(symbols)
        strategy = np.random.choice(strategies)
        profile = np.random.choice(profiles)
        
        # Generate realistic trade data
        entry_price = np.random.uniform(50, 800)
        exit_price = entry_price * np.random.uniform(0.80, 1.30)  # -20% to +30%
        quantity = np.random.randint(10, 200)
        
        # Calculate P&L
        pnl = (exit_price - entry_price) * quantity
        pnl_pct = ((exit_price - entry_price) / entry_price) * 100
        
        # Generate realistic dates
        entry_date = datetime.now() - timedelta(days=np.random.randint(1, 365))
        exit_date = entry_date + timedelta(days=np.random.randint(1, 45))
        
        # Determine trade direction and action
        if entry_price < exit_price:
            action = "BUY"
            trade_type = "LONG"
        else:
            action = "SELL"
            trade_type = "SHORT"
        
        trade = {
            'trade_id': f"T{i+1:03d}",
            'symbol': symbol,
            'strategy': strategy,
            'profile': profile,
            'action': action,
            'trade_type': trade_type,
            'entry_date': entry_date,
            'exit_date': exit_date,
            'entry_price': round(entry_price, 2),
            'exit_price': round(exit_price, 2),
            'quantity': quantity,
            'total_entry': round(entry_price * quantity, 2),
            'total_exit': round(exit_price * quantity, 2),
            'pnl': round(pnl, 2),
            'pnl_pct': round(pnl_pct, 2),
            'hold_days': (exit_date - entry_date).days,
            'status': 'closed',
            'exit_reason': np.random.choice(['take_profit', 'stop_loss', 'signal', 'timeout', 'trailing_stop'])
        }
        
        trades.append(trade)
    
    return pd.DataFrame(trades)

def generate_detailed_report():
    """Generate a comprehensive trade report"""
    print("📊 Generating Enhanced Trade Report...")
    print("=" * 80)
    
    # Generate sample trades
    trades_df = generate_sample_trades()
    
    # Calculate summary statistics
    total_trades = len(trades_df)
    winning_trades = len(trades_df[trades_df['pnl'] > 0])
    losing_trades = len(trades_df[trades_df['pnl'] < 0])
    win_rate = (winning_trades / total_trades) * 100
    
    total_pnl = trades_df['pnl'].sum()
    avg_pnl = trades_df['pnl'].mean()
    max_profit = trades_df['pnl'].max()
    max_loss = trades_df['pnl'].min()
    
    # Strategy performance
    strategy_performance = trades_df.groupby('strategy').agg({
        'pnl': ['sum', 'mean', 'count'],
        'pnl_pct': 'mean'
    }).round(2)
    
    # Profile performance
    profile_performance = trades_df.groupby('profile').agg({
        'pnl': ['sum', 'mean', 'count'],
        'pnl_pct': 'mean'
    }).round(2)
    
    # Symbol performance
    symbol_performance = trades_df.groupby('symbol').agg({
        'pnl': ['sum', 'mean', 'count'],
        'pnl_pct': 'mean'
    }).round(2)
    
    # Print comprehensive report
    print("🎯 ENHANCED TRADE REPORT SUMMARY")
    print("=" * 80)
    print(f"📅 Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Total Trades: {total_trades}")
    print(f"✅ Winning Trades: {winning_trades}")
    print(f"❌ Losing Trades: {losing_trades}")
    print(f"📈 Win Rate: {win_rate:.1f}%")
    print(f"💰 Total P&L: ${total_pnl:,.2f}")
    print(f"📊 Average P&L: ${avg_pnl:.2f}")
    print(f"🚀 Max Profit: ${max_profit:.2f}")
    print(f"📉 Max Loss: ${max_loss:.2f}")
    
    print("\n📋 DETAILED TRADE LIST WITH FULL DATES")
    print("=" * 80)
    print(f"{'ID':<6} {'Symbol':<6} {'Action':<4} {'Strategy':<15} {'Profile':<12} {'Entry Date':<19} {'Exit Date':<19} {'Entry':<8} {'Exit':<8} {'Qty':<4} {'Total Entry':<12} {'Total Exit':<12} {'P&L':<8} {'P&L%':<6} {'Days':<5}")
    print("-" * 140)
    
    for _, trade in trades_df.iterrows():
        entry_date_str = trade['entry_date'].strftime('%Y-%m-%d %H:%M')
        exit_date_str = trade['exit_date'].strftime('%Y-%m-%d %H:%M')
        
        print(f"{trade['trade_id']:<6} {trade['symbol']:<6} {trade['action']:<4} {trade['strategy']:<15} {trade['profile']:<12} "
              f"{entry_date_str:<19} {exit_date_str:<19} ${trade['entry_price']:<7.2f} ${trade['exit_price']:<7.2f} "
              f"{trade['quantity']:<4} ${trade['total_entry']:<11.2f} ${trade['total_exit']:<11.2f} "
              f"${trade['pnl']:<7.2f} {trade['pnl_pct']:<5.1f}% {trade['hold_days']:<5}")
    
    print("\n📊 STRATEGY PERFORMANCE ANALYSIS")
    print("=" * 80)
    for strategy in strategy_performance.index:
        stats = strategy_performance.loc[strategy]
        print(f"📈 {strategy}:")
        print(f"   Total P&L: ${stats[('pnl', 'sum')]:,.2f}")
        print(f"   Average P&L: ${stats[('pnl', 'mean')]:.2f}")
        print(f"   Trade Count: {stats[('pnl', 'count')]}")
        print(f"   Average Return: {stats[('pnl_pct', 'mean')]:.1f}%")
        print()
    
    print("🎛️  PROFILE PERFORMANCE ANALYSIS")
    print("=" * 80)
    for profile in profile_performance.index:
        stats = profile_performance.loc[profile]
        print(f"⚙️  {profile.title()}:")
        print(f"   Total P&L: ${stats[('pnl', 'sum')]:,.2f}")
        print(f"   Average P&L: ${stats[('pnl', 'mean')]:.2f}")
        print(f"   Trade Count: {stats[('pnl', 'count')]}")
        print(f"   Average Return: {stats[('pnl_pct', 'mean')]:.1f}%")
        print()
    
    print("📈 SYMBOL PERFORMANCE ANALYSIS")
    print("=" * 80)
    for symbol in symbol_performance.index:
        stats = symbol_performance.loc[symbol]
        print(f"💹 {symbol}:")
        print(f"   Total P&L: ${stats[('pnl', 'sum')]:,.2f}")
        print(f"   Average P&L: ${stats[('pnl', 'mean')]:.2f}")
        print(f"   Trade Count: {stats[('pnl', 'count')]}")
        print(f"   Average Return: {stats[('pnl_pct', 'mean')]:.1f}%")
        print()
    
    # Risk analysis
    print("⚠️  RISK ANALYSIS")
    print("=" * 80)
    
    # Calculate drawdown
    cumulative_pnl = trades_df['pnl'].cumsum()
    running_max = cumulative_pnl.expanding().max()
    drawdown = (cumulative_pnl - running_max) / running_max * 100
    
    max_drawdown = drawdown.min()
    volatility = trades_df['pnl_pct'].std()
    
    print(f"📉 Maximum Drawdown: {max_drawdown:.1f}%")
    print(f"📊 Volatility: {volatility:.1f}%")
    print(f"📈 Sharpe Ratio: {(avg_pnl / volatility) if volatility > 0 else 0:.2f}")
    
    # Exit reason analysis
    print("\n🚪 EXIT REASON ANALYSIS")
    print("=" * 80)
    exit_reasons = trades_df['exit_reason'].value_counts()
    for reason, count in exit_reasons.items():
        pnl_for_reason = trades_df[trades_df['exit_reason'] == reason]['pnl'].sum()
        print(f"🔚 {reason.replace('_', ' ').title()}: {count} trades, P&L: ${pnl_for_reason:.2f}")
    
    # Time analysis
    print("\n⏰ TIME ANALYSIS")
    print("=" * 80)
    avg_hold_days = trades_df['hold_days'].mean()
    print(f"📅 Average Hold Time: {avg_hold_days:.1f} days")
    
    # Monthly performance
    trades_df['month'] = trades_df['entry_date'].dt.to_period('M')
    monthly_performance = trades_df.groupby('month')['pnl'].sum()
    
    print(f"📅 Monthly Performance:")
    for month, pnl in monthly_performance.items():
        print(f"   {month}: ${pnl:.2f}")
    
    # Trade type analysis
    print("\n📊 TRADE TYPE ANALYSIS")
    print("=" * 80)
    trade_types = trades_df['trade_type'].value_counts()
    for trade_type, count in trade_types.items():
        pnl_for_type = trades_df[trades_df['trade_type'] == trade_type]['pnl'].sum()
        print(f"📈 {trade_type}: {count} trades, P&L: ${pnl_for_type:.2f}")
    
    return trades_df

def save_report_to_file(trades_df, filename="enhanced_trade_report.txt"):
    """Save the enhanced report to a file"""
    with open(filename, 'w') as f:
        f.write("STOCKTRADESOLUTION - ENHANCED TRADE REPORT\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Save detailed trade list
        f.write("DETAILED TRADE LIST\n")
        f.write("=" * 80 + "\n")
        f.write(f"{'ID':<6} {'Symbol':<6} {'Action':<4} {'Strategy':<15} {'Profile':<12} {'Entry Date':<19} {'Exit Date':<19} {'Entry':<8} {'Exit':<8} {'Qty':<4} {'Total Entry':<12} {'Total Exit':<12} {'P&L':<8} {'P&L%':<6} {'Days':<5}\n")
        f.write("-" * 140 + "\n")
        
        for _, trade in trades_df.iterrows():
            entry_date_str = trade['entry_date'].strftime('%Y-%m-%d %H:%M')
            exit_date_str = trade['exit_date'].strftime('%Y-%m-%d %H:%M')
            
            f.write(f"{trade['trade_id']:<6} {trade['symbol']:<6} {trade['action']:<4} {trade['strategy']:<15} {trade['profile']:<12} "
                   f"{entry_date_str:<19} {exit_date_str:<19} ${trade['entry_price']:<7.2f} ${trade['exit_price']:<7.2f} "
                   f"{trade['quantity']:<4} ${trade['total_entry']:<11.2f} ${trade['total_exit']:<11.2f} "
                   f"${trade['pnl']:<7.2f} {trade['pnl_pct']:<5.1f}% {trade['hold_days']:<5}\n")
        
        # Save summary statistics
        f.write("\n\nSUMMARY STATISTICS\n")
        f.write("=" * 80 + "\n")
        f.write(f"Total Trades: {len(trades_df)}\n")
        f.write(f"Total P&L: ${trades_df['pnl'].sum():,.2f}\n")
        f.write(f"Win Rate: {(len(trades_df[trades_df['pnl'] > 0]) / len(trades_df) * 100):.1f}%\n")
        f.write(f"Average P&L: ${trades_df['pnl'].mean():.2f}\n")
        f.write(f"Max Profit: ${trades_df['pnl'].max():.2f}\n")
        f.write(f"Max Loss: ${trades_df['pnl'].min():.2f}\n")
    
    print(f"\n💾 Enhanced report saved to: {filename}")

def main():
    """Main function"""
    print("🚀 StockTradeSolution - Enhanced Trade Report Generator")
    print("=" * 80)
    
    try:
        # Generate detailed report
        trades_df = generate_detailed_report()
        
        # Save to file
        save_report_to_file(trades_df)
        
        print("\n🎉 Enhanced trade report generated successfully!")
        print("📁 Check the generated files for detailed analysis")
        print("📊 Report includes:")
        print("   ✅ Full buy/sell dates and times")
        print("   ✅ Entry and exit prices")
        print("   ✅ Total entry and exit values")
        print("   ✅ P&L calculations")
        print("   ✅ Strategy and profile analysis")
        print("   ✅ Risk metrics")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 