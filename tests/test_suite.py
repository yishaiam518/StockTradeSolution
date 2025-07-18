"""
Main test suite for the SMART STOCK TRADING SYSTEM.
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.data_engine import DataEngine
from src.indicators import TechnicalIndicators
from src.strategies import MACDStrategy
from src.backtesting import BacktestEngine
from src.utils.config_loader import config
from src.utils.logger import logger


class TestSMARTTradingSystem(unittest.TestCase):
    """Test suite for the SMART Trading System."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.data_engine = DataEngine()
        self.indicators = TechnicalIndicators()
        self.strategy = MACDStrategy()
        self.backtest_engine = BacktestEngine()
        
        # Test parameters
        self.test_ticker = "AAPL"
        self.start_date = "2023-01-01"
        self.end_date = "2023-12-31"
    
    def test_01_config_loading(self):
        """Test configuration loading."""
        logger.info("Testing configuration loading...")
        
        # Test that config loads without errors
        self.assertIsNotNone(config.config)
        
        # Test specific config sections
        data_config = config.get_data_engine_config()
        self.assertIsInstance(data_config, dict)
        
        indicators_config = config.get_indicators_config()
        self.assertIsInstance(indicators_config, dict)
        
        strategies_config = config.get_strategies_config()
        self.assertIsInstance(strategies_config, dict)
        
        logger.info("✓ Configuration loading test passed")
    
    def test_02_data_engine(self):
        """Test data engine functionality."""
        logger.info("Testing data engine...")
        
        # Test data fetching
        data = self.data_engine.fetch_data(self.test_ticker, self.start_date, self.end_date)
        
        # Basic validation
        self.assertIsInstance(data, pd.DataFrame)
        self.assertGreater(len(data), 0)
        
        # Check required columns
        required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            self.assertIn(col, data.columns)
        
        # Test data validation
        is_valid = self.data_engine.validate_data(data)
        self.assertTrue(is_valid)
        
        # Test data info
        info = self.data_engine.get_data_info(self.test_ticker)
        self.assertIsInstance(info, dict)
        
        logger.info("✓ Data engine test passed")
    
    def test_03_indicators(self):
        """Test technical indicators calculation."""
        logger.info("Testing technical indicators...")
        
        # Get test data
        data = self.data_engine.fetch_data(self.test_ticker, self.start_date, self.end_date)
        self.assertGreater(len(data), 0)
        
        # Calculate indicators
        data_with_indicators = self.indicators.calculate_all_indicators(data)
        
        # Check that indicators were added
        indicator_columns = [
            'macd_line', 'macd_signal', 'macd_histogram',
            'rsi', 'ema_short', 'ema_long',
            'bb_upper', 'bb_middle', 'bb_lower',
            'volume_ma'
        ]
        
        for col in indicator_columns:
            self.assertIn(col, data_with_indicators.columns)
        
        # Test indicator validation
        is_valid = self.indicators.validate_indicators(data_with_indicators)
        self.assertTrue(is_valid)
        
        # Test signal generation
        signals = self.indicators.get_indicator_signals(data_with_indicators)
        self.assertIsInstance(signals, dict)
        
        logger.info("✓ Technical indicators test passed")
    
    def test_04_strategy(self):
        """Test MACD strategy functionality."""
        logger.info("Testing MACD strategy...")
        
        # Test strategy initialization
        self.assertEqual(self.strategy.name, "MACDStrategy")
        
        # Test strategy parameters
        params = self.strategy.get_strategy_parameters()
        self.assertIsInstance(params, dict)
        self.assertIn('rsi_range', params)
        self.assertIn('take_profit_pct', params)
        self.assertIn('stop_loss_pct', params)
        
        # Test position sizing
        position_size = self.strategy.calculate_position_size(10000, 150.0)
        self.assertGreater(position_size, 0)
        
        # Test strategy description
        description = self.strategy.get_strategy_description()
        self.assertIsInstance(description, str)
        self.assertGreater(len(description), 0)
        
        logger.info("✓ MACD strategy test passed")
    
    def test_05_backtest_engine(self):
        """Test backtesting engine functionality."""
        logger.info("Testing backtesting engine...")
        
        # Test backtest initialization
        self.assertIsNotNone(self.backtest_engine.initial_capital)
        self.assertGreater(self.backtest_engine.initial_capital, 0)
        
        # Test data preparation
        data = self.backtest_engine._prepare_data(self.test_ticker, self.start_date, self.end_date)
        self.assertIsInstance(data, pd.DataFrame)
        self.assertGreater(len(data), 0)
        
        # Test strategy validation
        is_valid = self.strategy.validate_data_requirements(data)
        self.assertTrue(is_valid)
        
        logger.info("✓ Backtesting engine test passed")
    
    def test_06_full_backtest(self):
        """Test complete backtest execution."""
        logger.info("Testing full backtest execution...")
        
        # Run a complete backtest
        results = self.backtest_engine.run_backtest(
            self.strategy, 
            self.test_ticker, 
            self.start_date, 
            self.end_date,
            initial_capital=10000
        )
        
        # Validate results structure
        required_keys = [
            'ticker', 'strategy_name', 'start_date', 'end_date',
            'initial_capital', 'final_capital', 'total_return_pct',
            'trade_log', 'equity_curve', 'performance_metrics'
        ]
        
        for key in required_keys:
            self.assertIn(key, results)
        
        # Validate data types
        self.assertIsInstance(results['ticker'], str)
        self.assertIsInstance(results['strategy_name'], str)
        self.assertIsInstance(results['initial_capital'], (int, float))
        self.assertIsInstance(results['final_capital'], (int, float))
        self.assertIsInstance(results['total_return_pct'], (int, float))
        self.assertIsInstance(results['trade_log'], list)
        self.assertIsInstance(results['equity_curve'], list)
        self.assertIsInstance(results['performance_metrics'], dict)
        
        # Validate performance metrics
        metrics = results['performance_metrics']
        if metrics:  # Only if we have metrics
            self.assertIn('total_return', metrics)
            self.assertIn('sharpe_ratio', metrics)
            self.assertIn('max_drawdown', metrics)
            self.assertIn('total_trades', metrics)
            self.assertIn('win_rate', metrics)
        
        logger.info("✓ Full backtest test passed")
    
    def test_07_strategy_performance(self):
        """Test strategy performance calculation."""
        logger.info("Testing strategy performance calculation...")
        
        # Reset strategy
        self.strategy.reset()
        
        # Get initial performance
        initial_performance = self.strategy.get_performance_summary()
        self.assertIsInstance(initial_performance, dict)
        self.assertEqual(initial_performance['total_trades'], 0)
        
        # Simulate some trades
        test_trades = [
            {'type': 'BUY', 'price': 100, 'date': '2023-01-01', 'shares': 10, 'value': 1000, 'reason': {'summary': 'Test'}, 'strategy': 'MACDStrategy'},
            {'type': 'SELL', 'price': 110, 'date': '2023-01-15', 'shares': 10, 'value': 1100, 'reason': {'summary': 'Test'}, 'strategy': 'MACDStrategy',
             'entry_price': 100, 'entry_date': '2023-01-01', 'pnl_pct': 10.0, 'pnl_dollars': 100, 'holding_days': 14}
        ]
        
        self.strategy.trades = test_trades
        
        # Get performance after trades
        performance = self.strategy.get_performance_summary()
        self.assertEqual(performance['total_trades'], 1)
        self.assertEqual(performance['winning_trades'], 1)
        self.assertEqual(performance['win_rate'], 100.0)
        self.assertEqual(performance['total_return'], 10.0)
        
        logger.info("✓ Strategy performance test passed")
    
    def test_08_error_handling(self):
        """Test error handling in various components."""
        logger.info("Testing error handling...")
        
        # Test invalid ticker
        invalid_data = self.data_engine.fetch_data("INVALID_TICKER", self.start_date, self.end_date)
        self.assertTrue(invalid_data.empty)
        
        # Test invalid date range
        invalid_data = self.data_engine.fetch_data(self.test_ticker, "2023-13-01", "2023-13-31")
        self.assertTrue(invalid_data.empty)
        
        # Test empty data validation
        empty_df = pd.DataFrame()
        is_valid = self.data_engine.validate_data(empty_df)
        self.assertFalse(is_valid)
        
        logger.info("✓ Error handling test passed")
    
    def test_09_configuration_validation(self):
        """Test configuration validation."""
        logger.info("Testing configuration validation...")
        
        # Test that all required config sections exist
        required_sections = [
            'data_engine', 'indicators', 'strategies', 
            'backtesting', 'risk_management', 'dashboard'
        ]
        
        for section in required_sections:
            section_config = config.get(section)
            self.assertIsNotNone(section_config)
            self.assertIsInstance(section_config, dict)
        
        logger.info("✓ Configuration validation test passed")
    
    def test_10_logging(self):
        """Test logging functionality."""
        logger.info("Testing logging functionality...")
        
        # Test various log levels
        logger.info("Test info message")
        logger.warning("Test warning message")
        logger.error("Test error message")
        logger.debug("Test debug message")
        
        # Test trade logging
        test_trade = {
            'ticker': 'AAPL',
            'entry_price': 100.0,
            'exit_price': 110.0,
            'pnl_pct': 10.0
        }
        logger.log_trade(test_trade)
        
        # Test strategy performance logging
        test_metrics = {
            'total_return': 15.5,
            'sharpe_ratio': 1.2,
            'max_drawdown': 5.0
        }
        logger.log_strategy_performance("TestStrategy", test_metrics)
        
        logger.info("✓ Logging test passed")


def run_test_suite():
    """Run the complete test suite."""
    logger.info("Starting SMART Trading System test suite...")
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSMARTTradingSystem)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Log results
    if result.wasSuccessful():
        logger.info("✓ All tests passed!")
        return True
    else:
        logger.error(f"✗ {len(result.failures)} failures, {len(result.errors)} errors")
        return False


if __name__ == "__main__":
    success = run_test_suite()
    sys.exit(0 if success else 1) 