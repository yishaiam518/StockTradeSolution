#!/usr/bin/env python3
"""
Simple Dashboard for StockTradeSolution
A simplified version that avoids circular imports
"""

import sys
import os
import webbrowser
import time
from threading import Timer
from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

app = Flask(__name__)

def generate_sample_data():
    """Generate sample trading data"""
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    
    # Generate sample stock data
    data = {
        'AAPL': pd.DataFrame({
            'Open': np.random.uniform(150, 200, len(dates)),
            'High': np.random.uniform(160, 210, len(dates)),
            'Low': np.random.uniform(140, 190, len(dates)),
            'Close': np.random.uniform(150, 200, len(dates)),
            'Volume': np.random.randint(1000000, 5000000, len(dates))
        }, index=dates),
        'MSFT': pd.DataFrame({
            'Open': np.random.uniform(250, 350, len(dates)),
            'High': np.random.uniform(260, 360, len(dates)),
            'Low': np.random.uniform(240, 340, len(dates)),
            'Close': np.random.uniform(250, 350, len(dates)),
            'Volume': np.random.randint(2000000, 6000000, len(dates))
        }, index=dates)
    }
    
    return data

def generate_sample_trades():
    """Generate sample trade data"""
    trades = []
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    strategies = ['MACDCanonical', 'MACDAggressive', 'MACDConservative']
    profiles = ['conservative', 'moderate', 'aggressive']
    
    for i in range(10):
        symbol = np.random.choice(symbols)
        strategy = np.random.choice(strategies)
        profile = np.random.choice(profiles)
        
        entry_price = np.random.uniform(50, 500)
        exit_price = entry_price * np.random.uniform(0.85, 1.25)
        quantity = np.random.randint(10, 100)
        
        pnl = (exit_price - entry_price) * quantity
        pnl_pct = ((exit_price - entry_price) / entry_price) * 100
        
        entry_date = datetime.now() - timedelta(days=np.random.randint(1, 365))
        exit_date = entry_date + timedelta(days=np.random.randint(1, 30))
        
        trade = {
            'id': f"T{i+1:03d}",
            'symbol': symbol,
            'strategy': strategy,
            'profile': profile,
            'entry_date': entry_date.strftime('%Y-%m-%d'),
            'exit_date': exit_date.strftime('%Y-%m-%d'),
            'entry_price': round(entry_price, 2),
            'exit_price': round(exit_price, 2),
            'quantity': quantity,
            'pnl': round(pnl, 2),
            'pnl_pct': round(pnl_pct, 2),
            'status': 'closed'
        }
        
        trades.append(trade)
    
    return trades

@app.route('/')
def dashboard():
    """Main dashboard page"""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StockTradeSolution Dashboard</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }
        .card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        select, input {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin-right: 10px;
        }
        button:hover {
            opacity: 0.9;
        }
        .results {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-top: 15px;
        }
        .metric {
            display: inline-block;
            margin: 10px;
            padding: 10px;
            background: white;
            border-radius: 5px;
            min-width: 120px;
            text-align: center;
        }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
        }
        .metric-label {
            font-size: 12px;
            color: #666;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        th, td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f8f9fa;
            font-weight: bold;
        }
        .positive { color: #28a745; }
        .negative { color: #dc3545; }
        .loading {
            text-align: center;
            padding: 20px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 StockTradeSolution Dashboard</h1>
            <p>Advanced Trading System with Strategy + Profile Selection</p>
        </div>

        <div class="grid">
            <!-- Backtesting Section -->
            <div class="card">
                <h2>📊 Backtesting</h2>
                <div class="form-group">
                    <label for="strategy">Strategy:</label>
                    <select id="strategy">
                        <option value="MACDCanonical">MACD Canonical</option>
                        <option value="MACDAggressive">MACD Aggressive</option>
                        <option value="MACDConservative">MACD Conservative</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="profile">Profile:</label>
                    <select id="profile">
                        <option value="conservative">Conservative</option>
                        <option value="moderate">Moderate</option>
                        <option value="aggressive">Aggressive</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="symbol">Symbol:</label>
                    <input type="text" id="symbol" value="AAPL" placeholder="Enter stock symbol">
                </div>
                <button onclick="runBacktest()">Run Backtest</button>
                <div id="backtest-results" class="results" style="display: none;">
                    <h3>Backtest Results</h3>
                    <div id="backtest-metrics"></div>
                </div>
            </div>

            <!-- Performance Metrics -->
            <div class="card">
                <h2>📈 Performance Metrics</h2>
                <div id="performance-metrics">
                    <div class="loading">Loading performance data...</div>
                </div>
            </div>
        </div>

        <!-- Trade History -->
        <div class="card">
            <h2>📋 Trade History</h2>
            <div id="trades-table">
                <div class="loading">Loading trade history...</div>
            </div>
        </div>
    </div>

    <script>
        // Load initial data
        document.addEventListener('DOMContentLoaded', function() {
            loadPerformanceMetrics();
            loadTradeHistory();
        });

        function runBacktest() {
            const strategy = document.getElementById('strategy').value;
            const profile = document.getElementById('profile').value;
            const symbol = document.getElementById('symbol').value;

            // Show loading
            document.getElementById('backtest-results').style.display = 'block';
            document.getElementById('backtest-metrics').innerHTML = '<div class="loading">Running backtest...</div>';

            // Simulate API call
            fetch('/api/backtest', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    strategy: strategy,
                    profile: profile,
                    symbol: symbol
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    displayBacktestResults(data.results);
                } else {
                    document.getElementById('backtest-metrics').innerHTML = '<div class="negative">Error: ' + data.error + '</div>';
                }
            })
            .catch(error => {
                document.getElementById('backtest-metrics').innerHTML = '<div class="negative">Error: ' + error.message + '</div>';
            });
        }

        function displayBacktestResults(results) {
            const metricsDiv = document.getElementById('backtest-metrics');
            metricsDiv.innerHTML = `
                <div class="metric">
                    <div class="metric-value ${results.total_return >= 0 ? 'positive' : 'negative'}">${results.total_return}%</div>
                    <div class="metric-label">Total Return</div>
                </div>
                <div class="metric">
                    <div class="metric-value">${results.sharpe_ratio}</div>
                    <div class="metric-label">Sharpe Ratio</div>
                </div>
                <div class="metric">
                    <div class="metric-value negative">${results.max_drawdown}%</div>
                    <div class="metric-label">Max Drawdown</div>
                </div>
                <div class="metric">
                    <div class="metric-value">${results.win_rate}%</div>
                    <div class="metric-label">Win Rate</div>
                </div>
                <div class="metric">
                    <div class="metric-value">${results.total_trades}</div>
                    <div class="metric-label">Total Trades</div>
                </div>
                <div style="margin-top: 15px;">
                    <strong>Strategy:</strong> ${results.strategy}<br>
                    <strong>Profile:</strong> ${results.profile}<br>
                    <strong>Symbol:</strong> ${results.symbol}
                </div>
            `;
        }

        function loadPerformanceMetrics() {
            fetch('/api/performance')
            .then(response => response.json())
            .then(data => {
                document.getElementById('performance-metrics').innerHTML = `
                    <div class="metric">
                        <div class="metric-value ${data.total_pnl >= 0 ? 'positive' : 'negative'}">$${data.total_pnl.toLocaleString()}</div>
                        <div class="metric-label">Total P&L</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">${data.win_rate}%</div>
                        <div class="metric-label">Win Rate</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">${data.total_trades}</div>
                        <div class="metric-label">Total Trades</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value ${data.avg_trade_pnl >= 0 ? 'positive' : 'negative'}">$${data.avg_trade_pnl}</div>
                        <div class="metric-label">Avg Trade P&L</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value positive">$${data.max_profit}</div>
                        <div class="metric-label">Max Profit</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value negative">$${data.max_loss}</div>
                        <div class="metric-label">Max Loss</div>
                    </div>
                `;
            })
            .catch(error => {
                document.getElementById('performance-metrics').innerHTML = '<div class="negative">Error loading performance data</div>';
            });
        }

        function loadTradeHistory() {
            fetch('/api/trades')
            .then(response => response.json())
            .then(trades => {
                let tableHTML = `
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Symbol</th>
                                <th>Strategy</th>
                                <th>Profile</th>
                                <th>Entry Date</th>
                                <th>Exit Date</th>
                                <th>Entry Price</th>
                                <th>Exit Price</th>
                                <th>Quantity</th>
                                <th>P&L</th>
                                <th>P&L%</th>
                            </tr>
                        </thead>
                        <tbody>
                `;

                trades.forEach(trade => {
                    const pnlClass = trade.pnl >= 0 ? 'positive' : 'negative';
                    tableHTML += `
                        <tr>
                            <td>${trade.id}</td>
                            <td>${trade.symbol}</td>
                            <td>${trade.strategy}</td>
                            <td>${trade.profile}</td>
                            <td>${trade.entry_date}</td>
                            <td>${trade.exit_date}</td>
                            <td>$${trade.entry_price}</td>
                            <td>$${trade.exit_price}</td>
                            <td>${trade.quantity}</td>
                            <td class="${pnlClass}">$${trade.pnl}</td>
                            <td class="${pnlClass}">${trade.pnl_pct}%</td>
                        </tr>
                    `;
                });

                tableHTML += '</tbody></table>';
                document.getElementById('trades-table').innerHTML = tableHTML;
            })
            .catch(error => {
                document.getElementById('trades-table').innerHTML = '<div class="negative">Error loading trade history</div>';
            });
        }
    </script>
</body>
</html>
    """
    return html_content

@app.route('/api/strategies')
def get_strategies():
    """Get available strategies"""
    strategies = [
        {'name': 'MACDCanonical', 'description': 'Pure MACD crossover strategy'},
        {'name': 'MACDAggressive', 'description': 'Aggressive MACD with higher risk'},
        {'name': 'MACDConservative', 'description': 'Conservative MACD with lower risk'}
    ]
    return jsonify(strategies)

@app.route('/api/profiles')
def get_profiles():
    """Get available profiles"""
    profiles = [
        {'name': 'conservative', 'description': 'Low risk, low return'},
        {'name': 'moderate', 'description': 'Balanced risk and return'},
        {'name': 'aggressive', 'description': 'High risk, high return'}
    ]
    return jsonify(profiles)

@app.route('/api/backtest', methods=['POST'])
def run_backtest():
    """Run backtest simulation"""
    try:
        data = request.get_json()
        strategy = data.get('strategy', 'MACDCanonical')
        profile = data.get('profile', 'moderate')
        symbol = data.get('symbol', 'AAPL')
        
        # Generate sample results
        results = {
            'total_return': round(np.random.uniform(-20, 50), 2),
            'sharpe_ratio': round(np.random.uniform(0.5, 2.5), 2),
            'max_drawdown': round(np.random.uniform(-30, -5), 2),
            'win_rate': round(np.random.uniform(40, 80), 1),
            'total_trades': np.random.randint(10, 50),
            'strategy': strategy,
            'profile': profile,
            'symbol': symbol
        }
        
        return jsonify({'success': True, 'results': results})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/trades')
def get_trades():
    """Get sample trades"""
    trades = generate_sample_trades()
    return jsonify(trades)

@app.route('/api/performance')
def get_performance():
    """Get performance metrics"""
    performance = {
        'total_pnl': round(np.random.uniform(-5000, 15000), 2),
        'win_rate': round(np.random.uniform(50, 80), 1),
        'total_trades': np.random.randint(20, 100),
        'avg_trade_pnl': round(np.random.uniform(-200, 500), 2),
        'max_profit': round(np.random.uniform(1000, 5000), 2),
        'max_loss': round(np.random.uniform(-3000, -500), 2)
    }
    return jsonify(performance)

def open_browser():
    """Open the dashboard in the browser"""
    webbrowser.open('http://localhost:8080')

def main():
    """Start the simple dashboard"""
    print("🚀 Starting Simple StockTradeSolution Dashboard...")
    print("=" * 50)
    print("📊 Dashboard Features:")
    print("   - Strategy + Profile Selection")
    print("   - Backtesting Simulation")
    print("   - Trade History")
    print("   - Performance Metrics")
    print("=" * 50)
    
    # Open browser after 2 seconds
    Timer(2.0, open_browser).start()
    
    print("🌐 Opening dashboard in browser...")
    print("🔗 URL: http://localhost:8080")
    print("⏹️  Press Ctrl+C to stop the dashboard")
    print("=" * 50)
    
    # Start the Flask app on port 8080
    app.run(host='0.0.0.0', port=8080, debug=True)

if __name__ == "__main__":
    main() 