"""
Dashboard Application

Main web dashboard application using Flask for real-time trading system monitoring.
"""

import os
import sys
import json
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pathlib import Path

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
import pandas as pd
import numpy as np
import math

from ..utils.config_loader import config
from ..utils.logger import logger
from ..data_engine.data_engine import DataEngine
from ..backtesting.backtest_engine import BacktestEngine
from ..real_time_trading.trading_engine import TradingEngine
from ..portfolio_management.portfolio_manager import PortfolioManager
from .chart_generator import ChartGenerator


class DashboardApp:
    """Main dashboard application."""
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        """Initialize the dashboard application."""
        self.config = config
        self.logger = logger
        
        # Initialize components
        self.data_engine = DataEngine()
        self.trading_engine = TradingEngine()
        self.portfolio_manager = PortfolioManager()
        self.backtest_engine = BacktestEngine()
        self.chart_generator = ChartGenerator()
        
        # Flask app
        self.app = Flask(__name__, static_folder='static')
        self.app.config['SECRET_KEY'] = 'your-secret-key-here'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Dashboard state
        self.is_running = False
        self.update_thread = None
        
        # Configuration
        self.host = self.config.get('web_dashboard.host')
        self.port = self.config.get('web_dashboard.port')
        self.debug = self.config.get('web_dashboard.debug')
        self.refresh_interval = self.config.get('web_dashboard.refresh_interval', 300)
        
        # Setup routes
        self._setup_routes()
        
        self.logger.info("Dashboard application initialized")
    
    def _get_trading_system(self):
        """Lazy load the trading system to avoid circular imports."""
        if not hasattr(self, '_trading_system'):
            from ..trading_system import get_trading_system
            self._trading_system = get_trading_system()
        return self._trading_system
    
    def _setup_routes(self):
        """Setup Flask routes."""
        
        @self.app.route('/')
        def index():
            """Main dashboard page."""
            return render_template('dashboard.html')
        
        @self.app.route('/api/portfolio')
        def get_portfolio():
            """Get portfolio data."""
            try:
                # Get current prices (simulated for demo)
                current_prices = self._get_current_prices()
                portfolio_summary = self.portfolio_manager.get_portfolio_summary(current_prices)
                return jsonify(portfolio_summary)
            except Exception as e:
                self.logger.error(f"Error getting portfolio: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/performance')
        def get_performance():
            """Get performance metrics."""
            try:
                metrics = self.portfolio_manager.get_performance_metrics()
                return jsonify(metrics)
            except Exception as e:
                self.logger.error(f"Error getting performance: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/trades')
        def get_trades():
            """Get recent trades."""
            try:
                # Get trades from trading engine
                trades = self.trading_engine.broker.get_trade_history()
                return jsonify(trades)
            except Exception as e:
                self.logger.error(f"Error getting trades: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/trades/stored')
        def get_stored_trades():
            """Get trades from database with filtering."""
            try:
                from ..data_engine.data_engine import DataEngine
                data_engine = DataEngine()
                
                # Get query parameters
                ticker = request.args.get('ticker')
                strategy = request.args.get('strategy')
                start_date = request.args.get('start_date')
                end_date = request.args.get('end_date')
                status = request.args.get('status')
                limit = int(request.args.get('limit', 100))
                
                trades = data_engine.get_trades(
                    ticker=ticker,
                    strategy=strategy,
                    start_date=start_date,
                    end_date=end_date,
                    status=status,
                    limit=limit
                )
                
                return jsonify({
                    'success': True,
                    'trades': trades,
                    'count': len(trades)
                })
                
            except Exception as e:
                self.logger.error(f"Error getting stored trades: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/trades/statistics')
        def get_trade_statistics():
            """Get trade statistics."""
            try:
                from ..data_engine.data_engine import DataEngine
                data_engine = DataEngine()
                
                # Get query parameters
                ticker = request.args.get('ticker')
                strategy = request.args.get('strategy')
                start_date = request.args.get('start_date')
                end_date = request.args.get('end_date')
                
                stats = data_engine.get_trade_statistics(
                    ticker=ticker,
                    strategy=strategy,
                    start_date=start_date,
                    end_date=end_date
                )
                
                return jsonify({
                    'success': True,
                    'statistics': stats
                })
                
            except Exception as e:
                self.logger.error(f"Error getting trade statistics: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/trades/<int:trade_id>/learning', methods=['PUT'])
        def update_trade_learning(trade_id):
            """Update the 'What I Learned' field for a trade."""
            try:
                from ..data_engine.data_engine import DataEngine
                data_engine = DataEngine()
                
                data = request.get_json()
                what_learned = data.get('what_learned', '')
                
                success = data_engine.update_trade_learning(trade_id, what_learned)
                
                if success:
                    return jsonify({
                        'success': True,
                        'message': f'Updated learning for trade {trade_id}'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Trade {trade_id} not found'
                    }), 404
                    
            except Exception as e:
                self.logger.error(f"Error updating trade learning: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/chart/<symbol>')
        def get_chart_data(symbol):
            """Get chart data for a symbol."""
            try:
                period = request.args.get('period', '1y')
                interval = request.args.get('interval', '1d')
                
                data = self.data_engine.get_data(symbol, period=period, interval=interval)
                if data.empty:
                    return jsonify({'error': 'No data available'}), 404
                
                chart_data = self.chart_generator.generate_candlestick_data(data)
                return jsonify(chart_data)
            except Exception as e:
                self.logger.error(f"Error getting chart data: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/backtest', methods=['POST'])
        def run_backtest():
            """Run a backtest."""
            try:
                import numpy as np
                import math
                data = request.get_json()
                symbol = data.get('symbol', 'AAPL')
                strategy = data.get('strategy', 'MACD')
                profile = data.get('profile', 'balanced')
                start_date = data.get('start_date')
                end_date = data.get('end_date')
                custom_parameters = data.get('parameters', {})
                benchmark = data.get('benchmark', symbol)  # Use selected symbol as benchmark by default
                
                # Run backtest with strategy+profile
                results = self.backtest_engine.run_backtest(
                    symbol=symbol,
                    strategy=strategy,
                    profile=profile,
                    start_date=start_date,
                    end_date=end_date,
                    custom_parameters=custom_parameters,
                    benchmark=benchmark
                )
                
                if 'error' in results:
                    return jsonify(results), 400
                
                return jsonify(results)
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/strategies')
        def get_strategies():
            """Get available strategies."""
            try:
                strategies = self.config.get('strategies.available', [])
                if not strategies:
                    # Fallback to hardcoded strategies if config is missing
                    strategies = [
                        {
                            'name': 'MACDStrategy',
                            'description': 'Standard MACD Strategy with balanced parameters',
                            'category': 'MACD',
                            'parameters': {
                                'entry_threshold': 0.3,
                                'take_profit_pct': 5.0,
                                'stop_loss_pct': 3.0,
                                'max_hold_days': 30
                            }
                        },
                        {
                            'name': 'MACDCanonicalStrategy',
                            'description': 'Canonical MACD Strategy with traditional parameters',
                            'category': 'MACD',
                            'parameters': {
                                'entry_threshold': 0.4,
                                'take_profit_pct': 5.0,
                                'stop_loss_pct': 3.0,
                                'max_hold_days': 30
                            }
                        },
                        {
                            'name': 'MACDAggressiveStrategy',
                            'description': 'Aggressive MACD Strategy for high-frequency trading',
                            'category': 'MACD',
                            'parameters': {
                                'entry_threshold': 0.2,
                                'take_profit_pct': 3.0,
                                'stop_loss_pct': 2.0,
                                'max_hold_days': 7
                            }
                        },
                        {
                            'name': 'MACDConservativeStrategy',
                            'description': 'Conservative MACD Strategy for long-term positions',
                            'category': 'MACD',
                            'parameters': {
                                'entry_threshold': 0.6,
                                'take_profit_pct': 10.0,
                                'stop_loss_pct': 5.0,
                                'max_hold_days': 60
                            }
                        }
                    ]
                return jsonify(strategies)
            except Exception as e:
                self.logger.error(f"Error getting strategies: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/strategy/<strategy_name>/parameters')
        def get_strategy_parameters(strategy_name):
            """Get parameters for a specific strategy."""
            try:
                strategies = self.config.get('strategies.available')
                strategy_config = None
                
                for strategy in strategies:
                    if strategy.get('name') == strategy_name:
                        strategy_config = strategy
                        break
                
                if not strategy_config:
                    return jsonify({'error': f'Strategy {strategy_name} not found'}), 404
                
                # Extract parameters from strategy config
                parameters = {
                    'name': strategy_config.get('name'),
                    'description': strategy_config.get('description'),
                    'entry_conditions': strategy_config.get('entry_conditions', {}),
                    'exit_conditions': strategy_config.get('exit_conditions', {}),
                    'position_sizing': strategy_config.get('position_sizing', {})
                }
                
                return jsonify(parameters)
            except Exception as e:
                self.logger.error(f"Error getting strategy parameters: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/symbols')
        def get_symbols():
            """Get available symbols."""
            try:
                symbols = self.config.get('dashboard.default_tickers')
                return jsonify(symbols)
            except Exception as e:
                self.logger.error(f"Error getting symbols: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/symbols/search')
        def search_symbols():
            """Search for available symbols"""
            try:
                # Common stock symbols for demonstration
                symbols = [
                    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 
                    'SPY', 'QQQ', 'IWM', 'VTI', 'VOO', 'VEA', 'VWO', 'GLD', 'SLV',
                    'JPM', 'JNJ', 'PG', 'UNH', 'HD', 'MA', 'V', 'PYPL', 'ADBE', 'CRM',
                    'NKE', 'DIS', 'WMT', 'COST', 'TMO', 'ABBV', 'PFE', 'MRK', 'LLY'
                ]
                
                query = request.args.get('q', '').upper()
                if query:
                    symbols = [s for s in symbols if query in s]
                
                return jsonify({
                    'success': True,
                    'symbols': symbols[:10]  # Limit to 10 results
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/trading/start', methods=['POST'])
        def start_trading():
            """Start real-time trading."""
            try:
                if not self.trading_engine.is_running:
                    # Start trading in background
                    threading.Thread(target=self._start_trading_session).start()
                    return jsonify({'status': 'started'})
                else:
                    return jsonify({'status': 'already_running'})
            except Exception as e:
                self.logger.error(f"Error starting trading: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/trading/stop', methods=['POST'])
        def stop_trading():
            """Stop real-time trading."""
            try:
                self.trading_engine.stop_trading()
                return jsonify({'status': 'stopped'})
            except Exception as e:
                self.logger.error(f"Error stopping trading: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/trading/status')
        def get_trading_status():
            """Get trading status."""
            try:
                status = {
                    'is_running': self.trading_engine.is_running,
                    'market_open': self.trading_engine.is_market_open(),
                    'daily_trades': self.trading_engine.daily_trade_count
                }
                return jsonify(status)
            except Exception as e:
                self.logger.error(f"Error getting trading status: {e}")
                return jsonify({'error': str(e)}), 500
        
        # Automation API routes
        @self.app.route('/api/automation/status')
        def get_automation_status():
            """Get automation status."""
            try:
                from ..real_time_trading.automation_scheduler import AutomationScheduler
                from ..real_time_trading.automation_engine import TradingMode
                
                # Get scheduler status
                scheduler = AutomationScheduler(self.config, TradingMode.PAPER_TRADING)
                status = scheduler.get_status()
                
                # Add market hours information
                try:
                    import pytz
                    et_tz = pytz.timezone('America/New_York')
                    now_et = datetime.now(et_tz)
                    
                    # Check if market is open
                    is_market_open = (
                        now_et.weekday() < 5 and  # Monday-Friday
                        (now_et.hour > 9 or (now_et.hour == 9 and now_et.minute >= 30)) and  # After 9:30 AM
                        now_et.hour < 16  # Before 4:00 PM
                    )
                    
                    status['market_status'] = {
                        'is_open': is_market_open,
                        'current_time_et': now_et.strftime('%Y-%m-%d %H:%M:%S ET'),
                        'market_hours': '9:30 AM - 4:00 PM ET',
                        'next_open': 'Monday 9:30 AM ET' if now_et.weekday() >= 5 else 'Tomorrow 9:30 AM ET' if now_et.hour >= 16 else 'Today 9:30 AM ET'
                    }
                    
                except ImportError:
                    status['market_status'] = {
                        'is_open': 'Unknown',
                        'current_time_et': 'Unknown',
                        'market_hours': '9:30 AM - 4:00 PM ET',
                        'next_open': 'Unknown'
                    }
                
                return jsonify(status)
            except Exception as e:
                self.logger.error(f"Error getting automation status: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/automation/start', methods=['POST'])
        def start_automation():
            """Start automation."""
            try:
                from ..real_time_trading.automation_engine import AutomationEngine
                automation_engine = AutomationEngine(self.config)
                
                data = request.get_json() or {}
                mode = data.get('mode', 'paper_trading')
                
                success = automation_engine.start_automation(mode)
                
                if success:
                    return jsonify({
                        'success': True,
                        'message': f'Automation started in {mode} mode'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Failed to start automation'
                    }), 500
                    
            except Exception as e:
                self.logger.error(f"Error starting automation: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/automation/stop', methods=['POST'])
        def stop_automation():
            """Stop automation."""
            try:
                from ..real_time_trading.automation_engine import AutomationEngine
                automation_engine = AutomationEngine(self.config)
                
                success = automation_engine.stop_automation()
                
                if success:
                    return jsonify({
                        'success': True,
                        'message': 'Automation stopped'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Failed to stop automation'
                    }), 500
                    
            except Exception as e:
                self.logger.error(f"Error stopping automation: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/automation/cycle', methods=['POST'])
        def run_automation_cycle():
            """Run a single automation cycle."""
            try:
                from ..real_time_trading.automation_engine import AutomationEngine
                automation_engine = AutomationEngine(self.config)
                
                result = automation_engine.run_cycle()
                
                return jsonify({
                    'success': True,
                    'result': result
                })
                    
            except Exception as e:
                self.logger.error(f"Error running automation cycle: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/automation/positions')
        def get_automation_positions():
            """Get automation positions."""
            try:
                from ..real_time_trading.position_manager import PositionManager
                position_manager = PositionManager()
                
                positions = position_manager.get_all_positions()
                return jsonify(positions)
                    
            except Exception as e:
                self.logger.error(f"Error getting automation positions: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/automation/performance')
        def get_automation_performance():
            """Get automation performance metrics."""
            try:
                from ..real_time_trading.automation_engine import AutomationEngine
                automation_engine = AutomationEngine(self.config)
                
                performance = automation_engine.get_performance_metrics()
                return jsonify(performance)
                    
            except Exception as e:
                self.logger.error(f"Error getting automation performance: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/automation/config', methods=['GET', 'PUT'])
        def automation_config():
            """Get or update automation configuration."""
            try:
                from ..real_time_trading.automation_engine import AutomationEngine
                automation_engine = AutomationEngine(self.config)
                
                if request.method == 'GET':
                    config = automation_engine.get_config()
                    return jsonify(config)
                else:
                    data = request.get_json()
                    success = automation_engine.update_config(data)
                    
                    if success:
                        return jsonify({
                            'success': True,
                            'message': 'Configuration updated'
                        })
                    else:
                        return jsonify({
                            'success': False,
                            'error': 'Failed to update configuration'
                        }), 500
                        
            except Exception as e:
                self.logger.error(f"Error with automation config: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/automation/historical-backtest', methods=['POST'])
        def run_historical_backtest():
            """Run historical backtest with automation strategies using centralized trading system."""
            try:
                import numpy as np
                import math
                data = request.get_json()
                start_date = data.get('start_date')
                end_date = data.get('end_date')
                period = data.get('period')  # 1m, 6m, 1y, 2y, 3y, 5y
                benchmark = data.get('benchmark', 'SPY')
                strategy = data.get('strategy', 'MACD')
                profile = data.get('profile', 'balanced')
                
                # Calculate date range based on period only if start_date and end_date are not provided
                if not start_date or not end_date:
                    if period:
                        end_dt = datetime.now()
                        if period == '1m':
                            start_dt = end_dt - timedelta(days=30)
                        elif period == '6m':
                            start_dt = end_dt - timedelta(days=180)
                        elif period == '1y':
                            start_dt = end_dt - timedelta(days=365)
                        elif period == '2y':
                            start_dt = end_dt - timedelta(days=730)
                        elif period == '3y':
                            start_dt = end_dt - timedelta(days=1095)
                        elif period == '5y':
                            start_dt = end_dt - timedelta(days=1825)
                        else:
                            return jsonify({'error': 'Invalid period'}), 400
                        
                        start_date = start_dt.strftime('%Y-%m-%d')
                        end_date = end_dt.strftime('%Y-%m-%d')
                    else:
                        return jsonify({'error': 'Start date and end date are required'}), 400
                
                if not start_date or not end_date:
                    return jsonify({'error': 'Start date and end date are required'}), 400
                
                # Run historical backtest using the new unified system
                results = self.backtest_engine.run_historical_backtest(
                    strategy=strategy,
                    profile=profile,
                    start_date=start_date,
                    end_date=end_date,
                    benchmark=benchmark
                )
                
                if 'error' in results:
                    return jsonify(results), 400
                
                return jsonify(results)
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/automation/historical-backtest/periods', methods=['GET'])
        def get_historical_periods():
            """Get available historical backtest periods."""
            periods = [
                {'value': '1m', 'label': '1 Month'},
                {'value': '6m', 'label': '6 Months'},
                {'value': '1y', 'label': '1 Year'},
                {'value': '2y', 'label': '2 Years'},
                {'value': '3y', 'label': '3 Years'},
                {'value': '5y', 'label': '5 Years'}
            ]
            return jsonify(periods)
        
        @self.app.route('/api/automation/historical-backtest/benchmarks', methods=['GET'])
        def get_benchmarks():
            """Get available benchmark symbols."""
            benchmarks = [
                {'value': 'SPY', 'label': 'S&P 500 (SPY)'},
                {'value': 'QQQ', 'label': 'NASDAQ 100 (QQQ)'},
                {'value': 'IWM', 'label': 'Russell 2000 (IWM)'},
                {'value': 'DIA', 'label': 'Dow Jones (DIA)'},
                {'value': 'VTI', 'label': 'Total Stock Market (VTI)'}
            ]
            return jsonify(benchmarks)
        
        @self.app.route('/api/market-indexes')
        def get_market_indexes():
            """Get current market indexes data."""
            try:
                import random
                import time
                
                # Simulate market indexes data (in real implementation, this would fetch from a data provider)
                indexes = {
                    'SPY': {
                        'symbol': 'SPY',
                        'name': 'S&P 500 ETF',
                        'price': 520.45 + random.uniform(-2, 2),
                        'change': random.uniform(-1.5, 1.5),
                        'change_pct': random.uniform(-0.3, 0.3),
                        'volume': '2.1B',
                        'last_updated': time.time()
                    },
                    'QQQ': {
                        'symbol': 'QQQ',
                        'name': 'NASDAQ-100 ETF',
                        'price': 445.67 + random.uniform(-3, 3),
                        'change': random.uniform(-2, 2),
                        'change_pct': random.uniform(-0.4, 0.4),
                        'volume': '1.8B',
                        'last_updated': time.time()
                    },
                    'DIA': {
                        'symbol': 'DIA',
                        'name': 'Dow Jones ETF',
                        'price': 385.23 + random.uniform(-1.5, 1.5),
                        'change': random.uniform(-1, 1),
                        'change_pct': random.uniform(-0.25, 0.25),
                        'volume': '950M',
                        'last_updated': time.time()
                    },
                    'VIX': {
                        'symbol': 'VIX',
                        'name': 'Volatility Index',
                        'price': 12.34 + random.uniform(-0.5, 0.5),
                        'change': random.uniform(-0.3, 0.3),
                        'change_pct': random.uniform(-2, 2),
                        'volume': '45M',
                        'last_updated': time.time()
                    }
                }
                
                return jsonify(indexes)
            except Exception as e:
                self.logger.error(f"Error getting market indexes: {e}")
                return jsonify({'error': str(e)}), 500
    
    def _get_current_prices(self) -> Dict[str, float]:
        """Get current prices for portfolio symbols."""
        # This would typically fetch real-time prices
        # For demo purposes, we'll simulate prices
        symbols = list(self.portfolio_manager.portfolio.keys())
        prices = {}
        
        for symbol in symbols:
            try:
                data = self.data_engine.get_data(symbol, period='1d', interval='1m')
                if not data.empty:
                    prices[symbol] = data['Close'].iloc[-1]
                else:
                    prices[symbol] = 100.0  # Default price
            except Exception as e:
                self.logger.warning(f"Error getting price for {symbol}: {e}")
                prices[symbol] = 100.0
        
        return prices
    
    def _start_trading_session(self):
        """Start trading session in background."""
        try:
            # Get default symbols and strategies
            symbols = self.config.get('dashboard.default_tickers')
            
            # For demo, we'll use a simple strategy for all symbols
            from ..strategies.macd_strategy import MACDStrategy
            strategies = {symbol: MACDStrategy() for symbol in symbols}
            
            # Start trading session
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                self.trading_engine.run_trading_session(strategies, symbols)
            )
            
        except Exception as e:
            self.logger.error(f"Error in trading session: {e}")
    
    def _update_dashboard_data(self):
        """Update dashboard data periodically."""
        while self.is_running:
            try:
                # Get current portfolio data
                current_prices = self._get_current_prices()
                portfolio_data = self.portfolio_manager.get_portfolio_summary(current_prices)
                
                # Emit to connected clients
                self.socketio.emit('portfolio_update', portfolio_data)
                
                # Get trading status
                trading_status = {
                    'is_running': self.trading_engine.is_running,
                    'market_open': self.trading_engine.is_market_open(),
                    'daily_trades': self.trading_engine.daily_trade_count
                }
                self.socketio.emit('trading_status_update', trading_status)
                
                time.sleep(self.refresh_interval)
                
            except Exception as e:
                self.logger.error(f"Error updating dashboard data: {e}")
                time.sleep(60)  # Wait before retrying
    
    def start(self):
        """Start the dashboard application."""
        self.is_running = True
        
        # Start data update thread
        self.update_thread = threading.Thread(target=self._update_dashboard_data)
        self.update_thread.daemon = True
        self.update_thread.start()
        
        self.logger.info(f"Starting dashboard on {self.host}:{self.port}")
        
        # Start Flask app
        self.socketio.run(
            self.app,
            host=self.host,
            port=self.port,
            debug=self.debug
        )
    
    def stop(self):
        """Stop the dashboard application."""
        self.is_running = False
        self.trading_engine.stop_trading()
        
        if self.update_thread:
            self.update_thread.join(timeout=5)
        
        self.logger.info("Dashboard stopped")
    
    def get_app(self):
        """Get the Flask app instance."""
        return self.app 

if __name__ == "__main__":
    app = DashboardApp()
    app.start() 