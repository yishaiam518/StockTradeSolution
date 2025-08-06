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

from flask import Flask, render_template, jsonify, request, redirect
from flask_socketio import SocketIO
import pandas as pd
import numpy as np
import math
import io
import logging

from ..utils.config_loader import config
from ..utils.logger import logger
from ..utils.timezone_utils import (
    make_timezone_naive, normalize_dataframe_dates, 
    normalize_index_dates, safe_date_comparison,
    safe_date_range_filter, parse_date_string
)
from ..data_engine.data_engine import DataEngine
from ..backtesting.backtest_engine import BacktestEngine
from ..real_time_trading.trading_engine import TradingEngine
from ..portfolio_management.portfolio_manager import PortfolioManager
from .chart_generator import ChartGenerator


class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle numpy types."""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


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
        
        # Initialize data collection manager
        from ..data_collection.data_manager import DataCollectionManager, DataCollectionConfig, Exchange
        self.data_collection_manager = DataCollectionManager()
        
        # Flask app
        self.app = Flask(__name__, static_folder='static')
        self.app.config['SECRET_KEY'] = 'your-secret-key-here'
        self.app.json_encoder = NumpyEncoder
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Configure proper MIME types for static files
        self.app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
        
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
        
                # Configure Flask to serve static files with correct MIME types
        self.app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

        # Add route to serve JavaScript files with correct MIME type
        @self.app.route('/static/js/<path:filename>')
        def serve_js(filename):
            """Serve JavaScript files with correct MIME type."""
            import os
            from flask import send_file
            static_dir = os.path.join(os.getcwd(), 'static')
            file_path = os.path.join(static_dir, 'js', filename)
            if os.path.exists(file_path):
                return send_file(file_path, mimetype='application/javascript')
            else:
                return "File not found", 404
        
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
            """Main dashboard page - redirect to data collection"""
            return redirect('/data-collection')
        
        @self.app.route('/data-collection')
        def data_collection():
            """Data Collection page"""
            return render_template('data_collection_clean.html')
        
        @self.app.route('/performance-analytics')
        def performance_analytics():
            """Performance Analytics page"""
            return render_template('performance_analytics.html')
        
        @self.app.route('/stock-viewer')
        def stock_viewer():
            """Render the full-screen stock viewer page."""
            return render_template('stock_viewer.html')
        
        @self.app.route('/test-stock-viewer')
        def test_stock_viewer():
            """Test page for stock viewer JavaScript."""
            return render_template('test_stock_viewer.html')
        
        @self.app.route('/debug_stock_viewer.js')
        def debug_stock_viewer_js():
            """Serve the debug script for stock viewer."""
            return send_file('debug_stock_viewer.js', mimetype='application/javascript')
        
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
                # Check if we have current backtest results
                if hasattr(self, 'current_historical_trades_data') and self.current_historical_trades_data:
                    print(f"🔍 DEBUG: Returning {len(self.current_historical_trades_data)} trades from current backtest results")
                    return jsonify({
                        'success': True,
                        'trades': self.current_historical_trades_data,
                        'count': len(self.current_historical_trades_data),
                        'source': 'backtest_results'
                    })
                
                # Fallback to database trades
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
                
                print(f"🔍 DEBUG: Returning {len(trades)} trades from database")
                return jsonify({
                    'success': True,
                    'trades': trades,
                    'count': len(trades),
                    'source': 'database'
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
                
                # Convert any remaining numpy types to Python native types
                def convert_numpy_types(obj):
                    if isinstance(obj, dict):
                        return {key: convert_numpy_types(value) for key, value in obj.items()}
                    elif isinstance(obj, list):
                        return [convert_numpy_types(item) for item in obj]
                    elif isinstance(obj, np.integer):
                        return int(obj)
                    elif isinstance(obj, np.floating):
                        return float(obj)
                    elif isinstance(obj, np.ndarray):
                        return obj.tolist()
                    elif isinstance(obj, pd.Timestamp):
                        return obj.isoformat()
                    elif isinstance(obj, datetime):
                        return obj.isoformat()
                    else:
                        return obj
                
                # Convert results to ensure JSON serialization
                serializable_results = convert_numpy_types(results)
                
                return jsonify(serializable_results)
                
            except Exception as e:
                self.logger.error(f"Error in backtest API: {str(e)}")
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
            """Run historical backtest with simplified implementation matching test script."""
            try:
                import io
                import sys
                from contextlib import redirect_stdout, redirect_stderr
                
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No JSON data provided'}), 400
                
                start_date = data.get('start_date')
                end_date = data.get('end_date')
                period = data.get('period', '1y')  # Default to 1y if not provided
                benchmark = data.get('benchmark', 'SPY')
                strategy = data.get('strategy', 'MACD')
                profile = data.get('profile', 'balanced')
                
                # Map frontend strategy names to backend strategy names
                strategy_mapping = {
                    'macd_enhanced': 'MACD_ENHANCED',
                    'MACD_ENHANCED': 'MACD_ENHANCED',
                    'macd': 'MACD',
                    'MACD': 'MACD'
                }
                strategy = strategy_mapping.get(strategy, strategy)
                
                # Calculate date range based on period
                # Use a realistic end date (today's date) instead of datetime.now()
                end_dt = datetime.now()
                
                # For testing, use a fixed end date to ensure we have historical data
                # Use 2024-12-31 as end date to ensure we have full historical data
                end_dt = datetime(2024, 12, 31)
                
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
                    return jsonify({'error': f'Invalid period: {period}'}), 400
                
                # Use calculated dates if not provided
                if not start_date:
                    start_date = start_dt.strftime('%Y-%m-%d')
                if not end_date:
                    end_date = end_dt.strftime('%Y-%m-%d')
                
                # Debug: Print the actual date range being used
                print(f"🔍 DEBUG: Using date range: {start_date} to {end_date}")
                print(f"🔍 DEBUG: Period requested: {period}")
                print(f"🔍 DEBUG: Strategy: {strategy}, Profile: {profile}, Benchmark: {benchmark}")
                
                # Create a custom string buffer to capture all output
                output_buffer = io.StringIO()
                
                # Create a custom print function that writes to our buffer
                def custom_print(*args, **kwargs):
                    print(*args, **kwargs, file=output_buffer)
                
                # Create a custom logger handler that captures ALL output
                class CustomHandler(logging.Handler):
                    def emit(self, record):
                        try:
                            msg = self.format(record)
                            output_buffer.write(msg + '\n')
                            # Also print to console for debugging
                            print(f"[CAPTURED] {msg}")
                        except Exception:
                            pass
                
                # Set up custom logging with more comprehensive capture
                custom_handler = CustomHandler()
                custom_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
                
                # Add custom handler to ALL relevant loggers
                key_loggers = [
                    'src.backtesting.backtest_engine', 
                    'TradingSystem', 
                    'src.data_engine.data_cache',
                    'src.data_engine.data_engine',
                    'src.strategies.macd_strategy',
                    'src.strategies.macd_enhanced_strategy',
                    'src.portfolio_management.portfolio_manager'
                ]
                original_handlers = {}
                
                for logger_name in key_loggers:
                    logger_obj = logging.getLogger(logger_name)
                    original_handlers[logger_name] = logger_obj.handlers.copy()
                    logger_obj.addHandler(custom_handler)
                    # Set level to capture all messages
                    logger_obj.setLevel(logging.DEBUG)
                
                # Run simplified historical backtest using direct implementation
                with redirect_stdout(output_buffer), redirect_stderr(output_buffer):
                    results = self._run_simplified_historical_backtest(
                        strategy=strategy,
                        profile=profile,
                        start_date=start_date,
                        end_date=end_date,
                        benchmark=benchmark
                    )
                
                # Restore original handlers
                for logger_name, handlers in original_handlers.items():
                    logger_obj = logging.getLogger(logger_name)
                    # Remove our custom handler
                    for handler in logger_obj.handlers[:]:
                        if isinstance(handler, CustomHandler):
                            logger_obj.removeHandler(handler)
                    # Restore original handlers
                    for handler in handlers:
                        logger_obj.addHandler(handler)
                
                # Get captured output
                terminal_output = output_buffer.getvalue()
                
                # Check if backtest failed
                if 'error' in results:
                    return jsonify({
                        'error': results['error'],
                        'terminal_output': terminal_output
                    }), 400
                
                # Store the results for the frontend
                self.current_historical_trades_data = results.get('trades', [])
                
                # Add terminal output to results
                results['terminal_output'] = terminal_output
                
                # Debug: Print what we're storing
                print(f"💾 Storing {len(self.current_historical_trades_data)} trades in current_historical_trades_data")
                if self.current_historical_trades_data:
                    print(f"🔍 First trade: {self.current_historical_trades_data[0]}")
                    print(f"🔍 Last trade: {self.current_historical_trades_data[-1]}")
                
                return jsonify(results)
                
            except Exception as e:
                import traceback
                error_msg = f"Error running historical backtest: {str(e)}"
                print(f"❌ {error_msg}")
                print(f"🔍 Traceback: {traceback.format_exc()}")
                return jsonify({'error': error_msg}), 500
        
        @self.app.route('/api/trades/clear', methods=['POST'])
        def clear_trade_history():
            """Clear the trade history."""
            try:
                # Only clear if explicitly requested with force=true
                data = request.get_json() or {}
                force_clear = data.get('force', False)
                
                if force_clear:
                    # Clear the stored trade data
                    if hasattr(self, 'current_historical_trades_data'):
                        old_count = len(self.current_historical_trades_data) if self.current_historical_trades_data else 0
                        delattr(self, 'current_historical_trades_data')
                        print(f"🗑️ Cleared backtest results (forced) - removed {old_count} trades")
                    return jsonify({'success': True, 'message': 'Trade history cleared'})
                else:
                    # Don't clear automatically - keep the data
                    current_count = len(self.current_historical_trades_data) if hasattr(self, 'current_historical_trades_data') and self.current_historical_trades_data else 0
                    print(f"🛡️ Trade history clear blocked - preserving {current_count} trades")
                    return jsonify({'success': True, 'message': 'Trade history preserved'})
                    
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
        
        @self.app.route('/api/pnl/comprehensive')
        def get_comprehensive_pnl():
            """Get comprehensive P&L analysis including realized and unrealized gains."""
            try:
                from ..data_engine.data_cache import DataCache
                import pandas as pd
                
                cache = DataCache()
                all_transactions = cache.get_transaction_history()
                
                if all_transactions.empty:
                    return jsonify({
                        'success': False,
                        'error': 'No transactions found'
                    }), 404
                
                # Convert date column to datetime
                all_transactions['date'] = pd.to_datetime(all_transactions['date'])
                all_transactions = all_transactions.sort_values('date')
                
                # Initialize tracking
                positions = {}  # Current open positions
                realized_pnl = {}  # Realized P&L per symbol
                trade_history = {}  # All trades per symbol
                
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
                        'date': str(date),
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
                                'last_date': str(date)
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
                            pos['last_date'] = str(date)
                            
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
                                
                                # Update position
                                pos['shares'] -= shares_to_sell
                                if pos['shares'] <= 0:
                                    # Position closed
                                    del positions[symbol]
                                else:
                                    # Partial position remains
                                    pos['total_cost'] = pos['avg_price'] * pos['shares']
                
                # Calculate unrealized P&L
                unrealized_pnl = {}
                total_unrealized_pnl = 0
                total_position_value = 0
                
                for symbol, pos in positions.items():
                    current_value = pos['shares'] * pos['last_price']
                    unrealized_pnl[symbol] = current_value - (pos['shares'] * pos['avg_price'])
                    total_unrealized_pnl += unrealized_pnl[symbol]
                    total_position_value += current_value
                
                # Calculate totals
                total_realized_pnl = sum(realized_pnl.values())
                total_pnl = total_realized_pnl + total_unrealized_pnl
                
                # Calculate performance metrics
                total_buy_value = sum(trade['value'] for trades in trade_history.values() 
                                     for trade in trades if trade['action'] == 'BUY')
                total_return_pct = (total_pnl / total_buy_value) * 100 if total_buy_value > 0 else 0
                
                # Prepare response
                response = {
                    'success': True,
                    'summary': {
                        'total_realized_pnl': total_realized_pnl,
                        'total_unrealized_pnl': total_unrealized_pnl,
                        'total_pnl': total_pnl,
                        'current_position_value': total_position_value,
                        'total_return_pct': total_return_pct,
                        'total_transactions': len(all_transactions),
                        'unique_symbols': len(set(all_transactions['symbol']))
                    },
                    'realized_pnl': realized_pnl,
                    'unrealized_pnl': unrealized_pnl,
                    'positions': positions,
                    'trade_history': trade_history
                }
                
                return jsonify(response)
                
            except Exception as e:
                self.logger.error(f"Error calculating comprehensive P&L: {e}")
                return jsonify({'error': str(e)}), 500
        
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
        
        @self.app.route('/api/trades/backtest-results')
        def get_backtest_results():
            """Get current backtest results."""
            try:
                if hasattr(self, 'current_historical_trades_data') and self.current_historical_trades_data:
                    return jsonify({
                        'success': True,
                        'trades': self.current_historical_trades_data,
                        'count': len(self.current_historical_trades_data),
                        'source': 'backtest_results'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'No backtest results available'
                    }), 404
                    
            except Exception as e:
                self.logger.error(f"Error getting backtest results: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/trades/backtest-status')
        def get_backtest_status():
            """Check if backtest results are available."""
            try:
                has_results = hasattr(self, 'current_historical_trades_data') and self.current_historical_trades_data
                return jsonify({
                    'success': True,
                    'has_results': has_results,
                    'trade_count': len(self.current_historical_trades_data) if has_results else 0
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/data-collection/start', methods=['POST'])
        def start_data_collection():
            """Start a data collection job."""
            try:
                from ..data_collection.data_manager import DataCollectionManager, DataCollectionConfig, Exchange
                
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No JSON data provided'}), 400
                
                # Extract parameters
                exchange_name = data.get('exchange', 'NASDAQ')
                start_date = data.get('start_date')
                end_date = data.get('end_date')
                symbols = data.get('symbols')
                sectors = data.get('sectors')
                market_cap_min = data.get('market_cap_min')
                market_cap_max = data.get('market_cap_max')
                include_etfs = data.get('include_etfs', True)
                include_penny_stocks = data.get('include_penny_stocks', False)
                
                # Validate exchange
                try:
                    exchange = Exchange[exchange_name]
                except KeyError:
                    return jsonify({'error': f'Invalid exchange: {exchange_name}'}), 400
                
                # Create config
                config = DataCollectionConfig(
                    exchange=exchange,
                    start_date=start_date,
                    end_date=end_date,
                    symbols=symbols,
                    sectors=sectors,
                    market_cap_min=market_cap_min,
                    market_cap_max=market_cap_max,
                    include_etfs=include_etfs,
                    include_penny_stocks=include_penny_stocks
                )
                
                # Initialize data manager
                data_manager = DataCollectionManager()
                
                # Start collection
                result = data_manager.collect_data(config)
                
                if result['status'] == 'success':
                    return jsonify({
                        'success': True,
                        'collection_id': result['collection_id'],
                        'message': f"Data collection completed. Collected {result['successful_symbols']} symbols.",
                        'total_symbols': result['total_symbols'],
                        'successful_symbols': result['successful_symbols'],
                        'failed_symbols': result['failed_symbols']
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': result.get('error', 'Unknown error')
                    }), 500
                    
            except Exception as e:
                self.logger.error(f"Error starting data collection: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/data-collection/collections', methods=['GET'])
        def list_data_collections():
            """List all data collections"""
            try:
                collections = self.data_collection_manager.list_collections()
                
                # Add auto_update and update_interval fields to each collection
                for collection in collections:
                    collection['auto_update'] = collection.get('auto_update', False)
                    collection['update_interval'] = collection.get('update_interval', '24h')
                    collection['last_run'] = collection.get('last_run', None)
                    collection['next_run'] = collection.get('next_run', None)
                    collection['successful_symbols'] = collection.get('successful_symbols', 0)
                    collection['failed_count'] = collection.get('failed_count', 0)
                
                return jsonify({
                    'success': True,
                    'collections': collections
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Error listing collections: {str(e)}'
                }), 500
        
        @self.app.route('/api/data-collection/collections/<collection_id>', methods=['GET'])
        def get_data_collection(collection_id):
            """Get details of a specific data collection."""
            try:
                from ..data_collection.data_manager import DataCollectionManager
                
                data_manager = DataCollectionManager()
                collection_data = data_manager.get_collected_data(collection_id)
                collection_details = data_manager.get_collection_details(collection_id)
                
                if collection_data and collection_details:
                    return jsonify({
                        'success': True,
                        'collection': {
                            'collection_id': collection_id,
                            'exchange': collection_data['config']['exchange'],
                            'start_date': collection_data['config']['start_date'],
                            'end_date': collection_data['config']['end_date'],
                            'total_symbols': collection_data['total_symbols'],
                            'successful_symbols': collection_data['successful_symbols'],
                            'failed_count': collection_data['failed_count'],
                            'collection_date': collection_data['collection_date'],
                            'symbols_count': len(collection_data['data']),
                            'auto_update': collection_details.get('auto_update', False),
                            'last_updated': collection_details.get('last_updated', collection_data['collection_date'])
                        }
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Collection not found'
                    }), 404
                    
            except Exception as e:
                self.logger.error(f"Error getting data collection: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/data-collection/collections/<collection_id>', methods=['DELETE'])
        def delete_data_collection(collection_id):
            """Delete a data collection."""
            try:
                from ..data_collection.data_manager import DataCollectionManager
                
                data_manager = DataCollectionManager()
                success = data_manager.delete_collection(collection_id)
                
                if success:
                    return jsonify({
                        'success': True,
                        'message': f'Collection {collection_id} deleted successfully'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Collection not found'
                    }), 404
                    
            except Exception as e:
                self.logger.error(f"Error deleting data collection: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/data-collection/exchanges', methods=['GET'])
        def get_available_exchanges():
            """Get list of available exchanges."""
            try:
                from ..data_collection.data_manager import Exchange
                
                exchanges = [exchange.value for exchange in Exchange]
                
                return jsonify({
                    'success': True,
                    'exchanges': exchanges
                })
                
            except Exception as e:
                self.logger.error(f"Error getting exchanges: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/data-collection/collections/<collection_id>/symbols', methods=['GET'])
        def get_collection_symbols(collection_id):
            """Get list of symbols in a collection."""
            try:
                collection_data = self.data_collection_manager.get_collected_data(collection_id)
                
                if collection_data and collection_data['data']:
                    symbols = list(collection_data['data'].keys())
                    return jsonify({
                        'success': True,
                        'symbols': symbols
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'No symbols found in collection'
                    }), 404
                    
            except Exception as e:
                self.logger.error(f"Error getting collection symbols: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/data-collection/collections/<collection_id>/symbols/<symbol>', methods=['GET'])
        def get_symbol_data(collection_id, symbol):
            """Get data for a specific symbol in a collection."""
            try:
                collection_data = self.data_collection_manager.get_collected_data(collection_id)
                
                if collection_data and collection_data['data'] and symbol in collection_data['data']:
                    stock_data = collection_data['data'][symbol]
                    
                    # Convert DataFrame to JSON format
                    stock_data_json = stock_data.to_dict('records')
                    
                    return jsonify({
                        'success': True,
                        'stock_data': stock_data_json
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Symbol {symbol} not found in collection'
                    }), 404
                    
            except Exception as e:
                self.logger.error(f"Error getting symbol data: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/data-collection/collections/<collection_id>/update', methods=['POST'])
        def update_data_collection(collection_id):
            """Update a data collection to include data up to today."""
            try:
                result = self.data_collection_manager.update_collection(collection_id)
                
                if result['success']:
                    return jsonify({
                        'success': True,
                        'message': f'Collection updated successfully',
                        'updated_symbols': result['updated_symbols'],
                        'failed_symbols': result['failed_symbols'],
                        'new_end_date': result['new_end_date']
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': result.get('error', 'Unknown error')
                    }), 400
                    
            except Exception as e:
                self.logger.error(f"Error updating collection {collection_id}: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/data-collection/collections/<collection_id>/auto-update', methods=['POST'])
        def toggle_auto_update(collection_id):
            """Toggle auto-update for a specific collection."""
            try:
                data = request.get_json()
                enable = data.get('enable', True)
                interval = data.get('interval', '24h')
                
                # Initialize scheduler if not already done
                if not hasattr(self, 'data_scheduler'):
                    from ..data_collection.scheduler import DataCollectionScheduler
                    self.data_scheduler = DataCollectionScheduler(self.data_collection_manager)
                
                # Enable/disable auto-update in database
                success = self.data_collection_manager.enable_auto_update(collection_id, enable, interval)
                
                if success:
                    if enable:
                        # Set the interval for the scheduler
                        self.data_scheduler.set_collection_interval(collection_id, interval)
                        
                        # Start the scheduler for this collection
                        scheduler_started = self.data_scheduler.start_collection_scheduler(collection_id)
                        if scheduler_started:
                            return jsonify({
                                'success': True,
                                'message': f'Auto-update enabled for collection {collection_id} with {interval} interval',
                                'scheduler_started': True,
                                'interval': interval
                            })
                        else:
                            return jsonify({
                                'success': True,
                                'message': f'Auto-update enabled for collection {collection_id} with {interval} interval',
                                'scheduler_started': False,
                                'warning': 'Scheduler already running',
                                'interval': interval
                            })
                    else:
                        # Stop the scheduler for this collection
                        self.data_scheduler.stop_collection_scheduler(collection_id)
                        return jsonify({
                            'success': True,
                            'message': f'Auto-update disabled for collection {collection_id}',
                            'scheduler_stopped': True
                        })
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Failed to update auto-update setting for {collection_id}'
                    }), 400
                    
            except Exception as e:
                self.logger.error(f"Error toggling auto-update for {collection_id}: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/data-collection/collections/<collection_id>/scheduler/start', methods=['POST'])
        def start_collection_scheduler(collection_id):
            """Start the scheduler for a specific collection"""
            try:
                # Initialize scheduler if not already done
                if not hasattr(self, 'data_scheduler'):
                    from ..data_collection.scheduler import DataCollectionScheduler
                    self.data_scheduler = DataCollectionScheduler(self.data_collection_manager)
                
                # Get collection details to determine the interval
                collection_details = self.data_collection_manager.get_collection_details(collection_id)
                if not collection_details:
                    return jsonify({
                        'success': False,
                        'message': f'Collection {collection_id} not found'
                    }), 404
                
                # Get current time for last_run
                from datetime import datetime, timedelta
                now = datetime.now()
                
                # Calculate next run time based on interval
                interval = collection_details.get('update_interval', '24h')
                if interval == '1min':
                    next_run = now + timedelta(minutes=1)
                elif interval == '5min':
                    next_run = now + timedelta(minutes=5)
                elif interval == '10min':
                    next_run = now + timedelta(minutes=10)
                elif interval == '30min':
                    next_run = now + timedelta(minutes=30)
                elif interval == '1h':
                    next_run = now + timedelta(hours=1)
                else:  # 24h default
                    next_run = now + timedelta(hours=24)
                
                # Update the collection's auto_update status in the database with run times
                self.logger.info(f"Starting scheduler for {collection_id} with interval {interval}")
                self.logger.info(f"last_run: {now.isoformat()}, next_run: {next_run.isoformat()}")
                success = self.data_collection_manager.enable_auto_update(
                    collection_id, 
                    True, 
                    interval, 
                    now.isoformat(), 
                    next_run.isoformat()
                )
                
                if success:
                    # Actually start the background scheduler thread
                    self.logger.info(f"Attempting to start background scheduler for collection {collection_id}")
                    scheduler_started = self.data_scheduler.start_collection_scheduler(collection_id)
                    if scheduler_started:
                        self.logger.info(f"Background scheduler thread started for collection {collection_id}")
                    else:
                        self.logger.warning(f"Failed to start background scheduler thread for collection {collection_id}")
                    
                    return jsonify({
                        'success': True,
                        'message': f'Scheduler started for collection {collection_id}',
                        'collection_id': collection_id,
                        'last_run': now.isoformat(),
                        'next_run': next_run.isoformat(),
                        'interval': interval
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': f'Failed to start scheduler for collection {collection_id}'
                    }), 500
                    
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Error starting scheduler: {str(e)}'
                }), 500

        @self.app.route('/api/data-collection/collections/<collection_id>/scheduler/stop', methods=['POST'])
        def stop_collection_scheduler(collection_id):
            """Stop the scheduler for a specific collection"""
            try:
                # Initialize scheduler if not already done
                if not hasattr(self, 'data_scheduler'):
                    from ..data_collection.scheduler import DataCollectionScheduler
                    self.data_scheduler = DataCollectionScheduler(self.data_collection_manager)
                
                # Stop the background scheduler thread first
                scheduler_stopped = self.data_scheduler.stop_collection_scheduler(collection_id)
                if scheduler_stopped:
                    self.logger.info(f"Background scheduler thread stopped for collection {collection_id}")
                else:
                    self.logger.warning(f"Failed to stop background scheduler thread for collection {collection_id}")
                
                # Update the collection's auto_update status in the database
                success = self.data_collection_manager.enable_auto_update(collection_id, False, None, None, None)
                
                if success:
                    return jsonify({
                        'success': True,
                        'message': f'Scheduler stopped for collection {collection_id}',
                        'collection_id': collection_id,
                        'last_run': None,
                        'next_run': None
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': f'Failed to stop scheduler for collection {collection_id}'
                    }), 400
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Error stopping scheduler: {str(e)}'
                }), 500

        @self.app.route('/api/data-collection/collections/<collection_id>/scheduler/status', methods=['GET'])
        def get_collection_scheduler_status(collection_id):
            """Get the scheduler status for a specific collection"""
            try:
                # Initialize scheduler if not already done
                if not hasattr(self, 'data_scheduler'):
                    from ..data_collection.scheduler import DataCollectionScheduler
                    self.data_scheduler = DataCollectionScheduler(self.data_collection_manager)
                
                # Get real-time status from the scheduler
                scheduler_status = self.data_scheduler.get_collection_status(collection_id)
                self.logger.info(f"Scheduler status for {collection_id}: {scheduler_status}")
                self.logger.info(f"Scheduler status keys: {list(scheduler_status.keys()) if scheduler_status else 'None'}")
                self.logger.info(f"AI ranking last update: {scheduler_status.get('ai_ranking_last_update', 'Never') if scheduler_status else 'None'}")
                
                if scheduler_status:
                    # Check if AI ranking has been triggered, if not trigger it
                    if not scheduler_status.get('ai_ranking_last_update'):
                        self.logger.info(f"AI ranking not triggered yet for {collection_id}, triggering now...")
                        collection_scheduler = self.data_scheduler.get_or_create_scheduler(collection_id)
                        collection_scheduler._trigger_ai_ranking_recalculation()
                        # Get updated status
                        scheduler_status = self.data_scheduler.get_collection_status(collection_id)
                        self.logger.info(f"Updated scheduler status after AI ranking trigger: {scheduler_status}")
                    
                    # Return real-time scheduler status with AI ranking information
                    return jsonify({
                        'success': True,
                        'collection_id': collection_id,
                        'auto_update': scheduler_status.get('is_running', False),
                        'update_interval': scheduler_status.get('interval', '24h'),
                        'last_run': scheduler_status.get('last_run'),
                        'next_run': scheduler_status.get('next_run'),
                        'ai_ranking_last_update': scheduler_status.get('ai_ranking_last_update'),
                        'ai_ranking_last_update_formatted': scheduler_status.get('ai_ranking_last_update_formatted'),
                        'ai_ranking_metadata': scheduler_status.get('ai_ranking_metadata'),
                        'ai_ranking_integrated': scheduler_status.get('ai_ranking_integrated', True)
                    })
                else:
                    # Fallback to database status if scheduler not found
                    self.logger.info(f"No scheduler status found for {collection_id}, using database fallback")
                    collection_details = self.data_collection_manager.get_collection_details(collection_id)
                    self.logger.info(f"Database collection details for {collection_id}: {collection_details}")
                    
                    if collection_details:
                        return jsonify({
                            'success': True,
                            'collection_id': collection_id,
                            'auto_update': collection_details.get('auto_update', False),
                            'update_interval': collection_details.get('update_interval', '24h'),
                            'last_run': collection_details.get('last_run'),
                            'next_run': collection_details.get('next_run'),
                            'ai_ranking_last_update': collection_details.get('ai_ranking_last_update'),
                            'ai_ranking_last_update_formatted': collection_details.get('ai_ranking_last_update_formatted'),
                            'ai_ranking_metadata': collection_details.get('ai_ranking_metadata'),
                            'ai_ranking_integrated': collection_details.get('ai_ranking_integrated', True)
                        })
                    else:
                        return jsonify({
                            'success': False,
                            'message': f'Collection {collection_id} not found'
                        }), 404
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Error getting scheduler status: {str(e)}'
                }), 500
        
        @self.app.route('/api/data-collection/scheduler/status', methods=['GET'])
        def get_all_scheduler_status():
            """Get status of all collection schedulers."""
            try:
                # Initialize scheduler if not already done
                if not hasattr(self, 'data_scheduler'):
                    from ..data_collection.scheduler import DataCollectionScheduler
                    self.data_scheduler = DataCollectionScheduler(self.data_collection_manager)
                
                status_list = self.data_scheduler.get_all_scheduler_status()
                
                return jsonify({
                    'success': True,
                    'schedulers': status_list,
                    'total_schedulers': len(status_list)
                })
                    
            except Exception as e:
                self.logger.error(f"Error getting all scheduler status: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/data-collection/scheduler/intervals', methods=['GET'])
        def get_scheduler_intervals():
            """Get available scheduler intervals."""
            try:
                # Initialize scheduler if not already done
                if not hasattr(self, 'data_scheduler'):
                    from ..data_collection.scheduler import DataCollectionScheduler
                    self.data_scheduler = DataCollectionScheduler(self.data_collection_manager)
                
                intervals = self.data_scheduler.get_available_intervals()
                return jsonify({
                    'success': True,
                    'intervals': intervals
                })
            except Exception as e:
                self.logger.error(f"Error getting scheduler intervals: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        # Technical Indicators API Endpoints
        @self.app.route('/api/data-collection/collections/<collection_id>/indicators/calculate', methods=['POST'])
        def calculate_collection_indicators(collection_id):
            """Manually trigger technical indicator calculation for a collection."""
            try:
                result = self.data_collection_manager.calculate_collection_indicators(collection_id)
                return jsonify(result)
            except Exception as e:
                self.logger.error(f"Error calculating indicators for collection {collection_id}: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/data-collection/collections/<collection_id>/indicators/status', methods=['GET'])
        def get_collection_indicators_status(collection_id):
            """Get the status of technical indicators for a collection."""
            try:
                status = self.data_collection_manager.get_collection_indicators_status(collection_id)
                return jsonify({
                    'success': True,
                    'collection_id': collection_id,
                    'status': status
                })
            except Exception as e:
                self.logger.error(f"Error getting indicators status for collection {collection_id}: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/data-collection/collections/<collection_id>/symbols/<symbol>/indicators', methods=['GET'])
        def get_symbol_indicators(collection_id, symbol):
            """Get technical indicators data for a specific symbol."""
            try:
                indicators_data = self.data_collection_manager.get_symbol_indicators(collection_id, symbol)
                
                if indicators_data is None:
                    return jsonify({
                        'success': False,
                        'error': f'No indicators found for symbol {symbol} in collection {collection_id}'
                    }), 404
                
                # Convert DataFrame to JSON for API response
                indicators_json = indicators_data.to_json(orient='records', date_format='iso')
                
                return jsonify({
                    'success': True,
                    'collection_id': collection_id,
                    'symbol': symbol,
                    'indicators_data': json.loads(indicators_json),
                    'columns': indicators_data.columns.tolist(),
                    'shape': indicators_data.shape
                })
                
            except Exception as e:
                self.logger.error(f"Error getting indicators for symbol {symbol} in collection {collection_id}: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/data-collection/collections/<collection_id>/symbols/<symbol>/data-with-indicators', methods=['GET'])
        def get_symbol_data_with_indicators(collection_id, symbol):
            """Get both original data and technical indicators for a symbol."""
            try:
                # Get original data
                original_data = self.data_collection_manager.get_symbol_data(collection_id, symbol)
                if original_data is None:
                    return jsonify({
                        'success': False,
                        'error': f'No data found for symbol {symbol} in collection {collection_id}'
                    }), 404
                
                # Get indicators data
                indicators_data = self.data_collection_manager.get_symbol_indicators(collection_id, symbol)
                
                # Combine data if indicators exist
                if indicators_data is not None:
                    # Start with the indicators data (which contains both original and indicators)
                    combined_data = indicators_data.copy()
                    
                    # Ensure we have the original column names for compatibility
                    column_mapping = {
                        'open': 'Open',
                        'high': 'High', 
                        'low': 'Low',
                        'close': 'Close',
                        'volume': 'Volume'
                    }
                    
                    # Rename columns if needed
                    for old_col, new_col in column_mapping.items():
                        if old_col in combined_data.columns and new_col not in combined_data.columns:
                            combined_data[new_col] = combined_data[old_col]
                    
                    # Ensure Date column is present
                    if 'Date' not in combined_data.columns and 'date' in combined_data.columns:
                        combined_data['Date'] = combined_data['date']
                    
                else:
                    combined_data = original_data
                
                # Convert to JSON for API response
                data_json = combined_data.to_json(orient='records', date_format='iso')
                
                return jsonify({
                    'success': True,
                    'collection_id': collection_id,
                    'symbol': symbol,
                    'data': json.loads(data_json),
                    'columns': combined_data.columns.tolist(),
                    'shape': combined_data.shape,
                    'indicators_available': indicators_data is not None
                })
                
            except Exception as e:
                self.logger.error(f"Error getting data with indicators for symbol {symbol} in collection {collection_id}: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        # Performance Analytics API Endpoints
        @self.app.route('/api/performance/collection/<collection_id>/metrics', methods=['GET'])
        def get_collection_performance_metrics(collection_id):
            """Get performance metrics for a specific collection."""
            try:
                # Get collection details
                collection = self.data_collection_manager.get_collection_details(collection_id)
                if not collection:
                    return jsonify({
                        'success': False,
                        'message': f'Collection {collection_id} not found'
                    }), 404

                # Calculate performance metrics
                metrics = self._calculate_collection_metrics(collection_id)
                
                return jsonify({
                    'success': True,
                    'metrics': metrics
                })
                    
            except Exception as e:
                self.logger.error(f"Error getting collection performance metrics: {e}")
                return jsonify({
                    'success': False,
                    'message': str(e)
                }), 500

        @self.app.route('/api/performance/collection/<collection_id>/risk', methods=['GET'])
        def get_collection_risk_data(collection_id):
            """Get risk management data for a specific collection."""
            try:
                # Get risk management data
                risk_data = self._calculate_collection_risk_data(collection_id)
                
                return jsonify({
                    'success': True,
                    'risk': risk_data
                })
                    
            except Exception as e:
                self.logger.error(f"Error getting collection risk data: {e}")
                return jsonify({
                    'success': False,
                    'message': str(e)
                }), 500

        @self.app.route('/api/performance/collection/<collection_id>/positions', methods=['GET'])
        def get_collection_positions(collection_id):
            """Get active positions for a specific collection."""
            try:
                # Get active positions
                positions = self._get_collection_positions(collection_id)
                
                return jsonify({
                    'success': True,
                    'positions': positions
                })
                    
            except Exception as e:
                self.logger.error(f"Error getting collection positions: {e}")
                return jsonify({
                    'success': False,
                    'message': str(e)
                }), 500

        @self.app.route('/api/performance/collection/<collection_id>/charts', methods=['GET'])
        def get_collection_charts(collection_id):
            """Get performance charts for a specific collection."""
            try:
                # Get performance charts data
                charts_data = self._get_collection_charts_data(collection_id)
                
                return jsonify({
                    'success': True,
                    'charts': charts_data
                })
                    
            except Exception as e:
                self.logger.error(f"Error getting collection charts: {e}")
                return jsonify({
                    'success': False,
                    'message': str(e)
                }), 500

        # AI Ranking API Endpoints
        @self.app.route('/api/ai-ranking/collection/<collection_id>/rank', methods=['GET'])
        def get_collection_ranking(collection_id):
            """Get AI-powered ranking for a specific collection."""
            try:
                # Initialize AI integration if not already done
                if not hasattr(self, '_ai_integration'):
                    from ..data_collection.integration import DataCollectionAIIntegration
                    self._ai_integration = DataCollectionAIIntegration(self.data_collection_manager)
                
                max_stocks = request.args.get('max_stocks', 1000, type=int)  # Default to high number to get all stocks
                ranking_data = self._ai_integration.get_collection_ranking(collection_id, max_stocks)
                
                if ranking_data['success']:
                    return jsonify(ranking_data)
                else:
                    return jsonify(ranking_data), 500
                    
            except Exception as e:
                self.logger.error(f"Error getting collection ranking: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/ai-ranking/collection/<collection_id>/stock/<symbol>', methods=['GET'])
        def get_stock_analysis(collection_id, symbol):
            """Get detailed AI analysis for a specific stock."""
            try:
                # Initialize AI integration if not already done
                if not hasattr(self, '_ai_integration'):
                    from ..data_collection.integration import DataCollectionAIIntegration
                    self._ai_integration = DataCollectionAIIntegration(self.data_collection_manager)
                
                analysis_data = self._ai_integration.get_stock_analysis(collection_id, symbol)
                
                if analysis_data['success']:
                    return jsonify(analysis_data)
                else:
                    return jsonify(analysis_data), 500
                    
            except Exception as e:
                self.logger.error(f"Error getting stock analysis: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/ai-ranking/collection/<collection_id>/performance', methods=['GET'])
        def get_ranking_performance(collection_id):
            """Get ranking performance metrics and insights."""
            try:
                # Initialize AI integration if not already done
                if not hasattr(self, '_ai_integration'):
                    from ..data_collection.integration import DataCollectionAIIntegration
                    self._ai_integration = DataCollectionAIIntegration(self.data_collection_manager)
                
                performance_data = self._ai_integration.get_ranking_performance(collection_id)
                
                if performance_data['success']:
                    return jsonify(performance_data)
                else:
                    return jsonify(performance_data), 500
                    
            except Exception as e:
                self.logger.error(f"Error getting ranking performance: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/ai-ranking/collection/<collection_id>/export', methods=['GET'])
        def export_ranking_report(collection_id):
            """Export ranking report in specified format."""
            try:
                # Initialize AI integration if not already done
                if not hasattr(self, '_ai_integration'):
                    from ..data_collection.integration import DataCollectionAIIntegration
                    self._ai_integration = DataCollectionAIIntegration(self.data_collection_manager)
                
                format_type = request.args.get('format', 'json')
                if format_type not in ['json', 'csv']:
                    return jsonify({'success': False, 'error': 'Invalid format. Use "json" or "csv"'}), 400
                
                export_data = self._ai_integration.export_ranking_report(collection_id, format_type)
                
                if export_data['success']:
                    return jsonify(export_data)
                else:
                    return jsonify(export_data), 500
                    
            except Exception as e:
                self.logger.error(f"Error exporting ranking report: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

    def _calculate_collection_metrics(self, collection_id):
        """Calculate performance metrics for a collection."""
        try:
            # Get collection symbols
            symbols = self.data_collection_manager.get_collection_symbols(collection_id)
            if not symbols:
                return {
                    'sharpe_ratio': 0.0,
                    'sortino_ratio': 0.0,
                    'calmar_ratio': 0.0,
                    'max_drawdown': 0.0,
                    'volatility': 0.0,
                    'beta': 0.0
                }

            # Calculate metrics for each symbol and aggregate
            total_sharpe = 0.0
            total_sortino = 0.0
            total_calmar = 0.0
            total_max_drawdown = 0.0
            total_volatility = 0.0
            total_beta = 0.0
            valid_symbols = 0

            for symbol in symbols[:10]:  # Limit to first 10 symbols for performance
                try:
                    # Get symbol data
                    data = self.data_collection_manager.get_symbol_data(collection_id, symbol)
                    if data is None or data.empty:
                        continue

                    # Calculate returns
                    if 'Close' in data.columns:
                        returns = data['Close'].pct_change().dropna()
                    elif 'close' in data.columns:
                        returns = data['close'].pct_change().dropna()
                    else:
                        continue

                    if len(returns) < 30:  # Need at least 30 days of data
                        continue

                    # Calculate metrics
                    mean_return = returns.mean()
                    std_return = returns.std()
                    
                    # Sharpe Ratio (assuming risk-free rate of 0.02)
                    sharpe_ratio = (mean_return - 0.02/252) / std_return if std_return > 0 else 0
                    
                    # Sortino Ratio (using downside deviation)
                    downside_returns = returns[returns < 0]
                    downside_deviation = downside_returns.std() if len(downside_returns) > 0 else 0
                    sortino_ratio = (mean_return - 0.02/252) / downside_deviation if downside_deviation > 0 else 0
                    
                    # Max Drawdown
                    cumulative_returns = (1 + returns).cumprod()
                    running_max = cumulative_returns.expanding().max()
                    drawdown = (cumulative_returns - running_max) / running_max
                    max_drawdown = drawdown.min()
                    
                    # Calmar Ratio
                    calmar_ratio = mean_return / abs(max_drawdown) if max_drawdown != 0 else 0
                    
                    # Volatility (annualized)
                    volatility = std_return * (252 ** 0.5)
                    
                    # Beta (simplified - using market correlation)
                    beta = 1.0  # Simplified for now

                    # Aggregate
                    total_sharpe += sharpe_ratio
                    total_sortino += sortino_ratio
                    total_calmar += calmar_ratio
                    total_max_drawdown += max_drawdown
                    total_volatility += volatility
                    total_beta += beta
                    valid_symbols += 1

                except Exception as e:
                    self.logger.warning(f"Error calculating metrics for {symbol}: {e}")
                    continue

            # Return averages
            if valid_symbols > 0:
                return {
                    'sharpe_ratio': total_sharpe / valid_symbols,
                    'sortino_ratio': total_sortino / valid_symbols,
                    'calmar_ratio': total_calmar / valid_symbols,
                    'max_drawdown': total_max_drawdown / valid_symbols,
                    'volatility': total_volatility / valid_symbols,
                    'beta': total_beta / valid_symbols
                }
            else:
                return {
                    'sharpe_ratio': 0.0,
                    'sortino_ratio': 0.0,
                    'calmar_ratio': 0.0,
                    'max_drawdown': 0.0,
                    'volatility': 0.0,
                    'beta': 0.0
                }

        except Exception as e:
            self.logger.error(f"Error calculating collection metrics: {e}")
            return {
                'sharpe_ratio': 0.0,
                'sortino_ratio': 0.0,
                'calmar_ratio': 0.0,
                'max_drawdown': 0.0,
                'volatility': 0.0,
                'beta': 0.0
            }

    def _calculate_collection_risk_data(self, collection_id):
        """Calculate risk management data for a collection."""
        try:
            # Get collection details
            collection = self.data_collection_manager.get_collection_details(collection_id)
            if not collection:
                return {
                    'position_size': 'N/A',
                    'stop_loss': 'N/A',
                    'portfolio_limits': 'N/A',
                    'sector_exposure': 'N/A'
                }

            # Calculate risk metrics
            symbols = self.data_collection_manager.get_collection_symbols(collection_id)
            
            # Position Size (based on collection size)
            position_size = f"{len(symbols)} symbols" if symbols else "0 symbols"
            
            # Stop Loss (example: 2% per position)
            stop_loss = "2.0% per position"
            
            # Portfolio Limits (example: 5% max per position)
            portfolio_limits = "5.0% max per position"
            
            # Sector Exposure (simplified)
            sector_exposure = "Diversified across sectors"

            return {
                'position_size': position_size,
                'stop_loss': stop_loss,
                'portfolio_limits': portfolio_limits,
                'sector_exposure': sector_exposure
            }

        except Exception as e:
            self.logger.error(f"Error calculating collection risk data: {e}")
            return {
                'position_size': 'N/A',
                'stop_loss': 'N/A',
                'portfolio_limits': 'N/A',
                'sector_exposure': 'N/A'
            }

    def _get_collection_positions(self, collection_id):
        """Get active positions for a collection."""
        try:
            # Get collection symbols
            symbols = self.data_collection_manager.get_collection_symbols(collection_id)
            if not symbols:
                return []

            # Simulate active positions for demonstration
            positions = []
            for i, symbol in enumerate(symbols[:5]):  # Show first 5 symbols
                try:
                    # Get current price
                    data = self.data_collection_manager.get_symbol_data(collection_id, symbol)
                    if data is None or data.empty:
                        continue

                    # Get latest price
                    if 'Close' in data.columns:
                        current_price = data['Close'].iloc[-1]
                    elif 'close' in data.columns:
                        current_price = data['close'].iloc[-1]
                    else:
                        continue

                    # Simulate position data
                    entry_price = current_price * (0.95 + 0.1 * (i % 3))  # Vary entry prices
                    quantity = 100 + (i * 50)  # Vary quantities
                    pnl = (current_price - entry_price) * quantity

                    positions.append({
                        'symbol': symbol,
                        'quantity': quantity,
                        'entry_price': round(entry_price, 2),
                        'current_price': round(current_price, 2),
                        'pnl': round(pnl, 2)
                    })

                except Exception as e:
                    self.logger.warning(f"Error getting position for {symbol}: {e}")
                    continue

            return positions

        except Exception as e:
            self.logger.error(f"Error getting collection positions: {e}")
            return []

    def _get_collection_charts_data(self, collection_id):
        """Get performance charts data for a collection."""
        try:
            # Get collection symbols
            symbols = self.data_collection_manager.get_collection_symbols(collection_id)
            if not symbols:
                return {
                    'price_chart': [],
                    'volume_chart': [],
                    'performance_chart': []
                }

            # Get data for first symbol as example
            symbol = symbols[0]
            data = self.data_collection_manager.get_symbol_data(collection_id, symbol)
            
            if data is None or data.empty:
                return {
                    'price_chart': [],
                    'volume_chart': [],
                    'performance_chart': []
                }

            # Prepare chart data
            dates = data.index.tolist() if hasattr(data.index, 'tolist') else list(range(len(data)))
            
            if 'Close' in data.columns:
                prices = data['Close'].tolist()
                volumes = data['Volume'].tolist() if 'Volume' in data.columns else [0] * len(prices)
            elif 'close' in data.columns:
                prices = data['close'].tolist()
                volumes = data['volume'].tolist() if 'volume' in data.columns else [0] * len(prices)
            else:
                return {
                    'price_chart': [],
                    'volume_chart': [],
                    'performance_chart': []
                }

            # Calculate performance (cumulative returns)
            performance = []
            if len(prices) > 1:
                base_price = prices[0]
                for price in prices:
                    performance.append(((price - base_price) / base_price) * 100)

            return {
                'price_chart': {
                    'dates': dates,
                    'prices': prices,
                    'symbol': symbol
                },
                'volume_chart': {
                    'dates': dates,
                    'volumes': volumes,
                    'symbol': symbol
                },
                'performance_chart': {
                    'dates': dates,
                    'performance': performance,
                    'symbol': symbol
                }
            }

        except Exception as e:
            self.logger.error(f"Error getting collection charts data: {e}")
            return {
                'price_chart': [],
                'volume_chart': [],
                'performance_chart': []
            }
    
    def _run_simplified_historical_backtest(self, strategy, profile, start_date, end_date, benchmark):
        """Run a simplified historical backtest using the same logic as the test script."""
        try:
            # Initialize backtest engine (same as test script)
            from ..backtesting.backtest_engine import BacktestEngine
            from ..data_engine.data_cache import DataCache
            
            print(f"🧹 Clearing all cached data to ensure fresh backtest...")
            
            # Clear all caches first
            try:
                data_cache = DataCache()
                data_cache.clear_all_cache()
                print(f"✅ Cleared data cache")
            except Exception as e:
                print(f"⚠️  Could not clear data cache: {e}")
            
            # Initialize backtest engine
            backtest_engine = BacktestEngine()
            
            # Clear backtest engine caches
            if hasattr(backtest_engine, 'data_engine'):
                try:
                    backtest_engine.data_engine.clear_cache()
                    print(f"✅ Cleared backtest engine data cache")
                except Exception as e:
                    print(f"⚠️  Could not clear backtest engine cache: {e}")
            
            if hasattr(backtest_engine, 'data_cache'):
                try:
                    backtest_engine.data_cache.clear_all_cache()
                    print(f"✅ Cleared backtest engine data cache")
                except Exception as e:
                    print(f"⚠️  Could not clear backtest engine data cache: {e}")
            
            # Run backtest (same as test script)
            print(f"🚀 Starting Historical Backtest")
            print(f"📊 Period: 1y")
            print(f"🎯 Strategy: {strategy} ({profile})")
            print(f"📈 Benchmark: {benchmark}")
            print(f"⏳ Calculating date range...")
            print(f"📅 Date Range: {start_date} to {end_date}")
            print(f"🔄 Making API call...")
            
            # Force fresh data collection
            print(f"📡 Forcing fresh data collection...")
            
            results = backtest_engine.run_historical_backtest(
                strategy=strategy,
                profile=profile,
                start_date=start_date,
                end_date=end_date,
                benchmark=benchmark
            )
            
            # Check if backtest was successful
            if not results or 'error' in results:
                error_msg = results.get('error', 'Unknown error in backtest') if results else 'No results returned from backtest'
                print(f"❌ Backtest failed: {error_msg}")
                return {'error': error_msg}
            
            # Get trades from the backtest results
            trades = results.get('trades', [])
            
            print(f"📊 Backtest completed with {len(trades)} trades")
            
            if not trades:
                print(f"⚠️  No trades found in backtest results")
                return {'error': 'No trades found in backtest results'}
            
            # Debug: Print first few trades
            print(f"🔍 First 3 trades:")
            for i, trade in enumerate(trades[:3]):
                print(f"  {i+1}. {trade.get('symbol', 'N/A')} - {trade.get('action', 'N/A')} - {trade.get('date', 'N/A')}")
            
            # Convert to the format expected by the frontend
            processed_trades = []
            for trade in trades:
                # Ensure we have all required fields
                processed_trade = {
                    'date': str(trade.get('date', '')),
                    'symbol': trade.get('symbol', ''),
                    'action': trade.get('action', ''),
                    'shares': float(trade.get('shares', 0)),
                    'price': float(trade.get('price', 0)),
                    'value': float(trade.get('value', 0)),
                    'pnl': float(trade.get('pnl', 0)),
                    'pnl_pct': float(trade.get('pnl_pct', 0)),
                    'strategy': trade.get('strategy', strategy),
                    'entry_reason': trade.get('entry_reason', 'Strategy Entry'),
                    'exit_reason': trade.get('exit_reason', 'N/A')
                }
                processed_trades.append(processed_trade)
            
            # Calculate summary from actual trade data
            sell_trades = [t for t in processed_trades if t['action'] == 'SELL']
            total_pnl = sum(t['pnl'] for t in sell_trades)
            win_rate = 0
            if sell_trades:
                winning_trades = len([t for t in sell_trades if t['pnl'] > 0])
                win_rate = (winning_trades / len(sell_trades)) * 100
            
            print(f"✅ Backtest completed successfully!")
            print(f"📊 Total trades: {len(processed_trades)}")
            print(f"💰 Final portfolio value: ${results.get('final_portfolio_value', 0):,.3f}")
            print(f"📈 Total return: {results.get('total_return', 0):.2f}%")
            print(f"🎯 Win rate: {win_rate:.1f}%")
            print(f"💵 Total P&L: ${total_pnl:,.2f}")
            
            return {
                'success': True,
                'trades': processed_trades,
                'summary': {
                    'total_trades': len(processed_trades),
                    'unique_symbols': len(set(trade['symbol'] for trade in processed_trades)),
                    'final_portfolio_value': results.get('final_portfolio_value', 0),
                    'total_return': results.get('total_return', 0),
                    'total_pnl': total_pnl,
                    'win_rate': win_rate,
                    'sell_trades': len(sell_trades),
                    'buy_trades': len([t for t in processed_trades if t['action'] == 'BUY'])
                }
            }
            
        except Exception as e:
            import traceback
            error_msg = f"Error in _run_simplified_historical_backtest: {str(e)}"
            print(f"❌ {error_msg}")
            print(f"🔍 Traceback: {traceback.format_exc()}")
            return {'error': error_msg}
    
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
                    prices[symbol] = data['close'].iloc[-1]
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