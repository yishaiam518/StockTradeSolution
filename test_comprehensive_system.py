#!/usr/bin/env python3
"""
Comprehensive Test Suite for StockTradeSolution
Tests all latest modifications including:
- Unified Architecture
- Strategy + Profile Selection
- Unified Scoring System
- Trading System Integration
- Backtesting Engine
- GUI Components
"""

import sys
import os
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.trading_system import TradingSystem
from src.machine_learning.stock_scorer import UnifiedStockScorer
from src.backtesting.backtest_engine import BacktestEngine
from src.strategies.macd_canonical_strategy import MACDCanonicalStrategy
from src.strategies.macd_aggressive_strategy import MACDAggressiveStrategy
from src.strategies.macd_conservative_strategy import MACDConservativeStrategy
from src.utils.config_loader import ConfigLoader
from src.utils.logger import setup_logger

class ComprehensiveSystemTest(unittest.TestCase):
    """Comprehensive test suite for the entire trading system"""
    
    def setUp(self):
        """Set up test environment"""
        self.logger = setup_logger('test_comprehensive_system')
        self.config = ConfigLoader().config
        
        # Create sample data
        self.sample_data = self._create_sample_data()
        
        # Initialize components
        self.scorer = UnifiedStockScorer()
        self.trading_system = TradingSystem()
        
    def _create_sample_data(self):
        """Create sample stock data for testing"""
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
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
    
    def test_01_unified_scoring_system(self):
        """Test unified scoring system with different modes"""
        self.logger.info("Testing unified scoring system...")
        
        # Test different modes
        modes = ['backtesting', 'historic', 'automation']
        
        for mode in modes:
            # Test scoring list creation
            scoring_list = self.scorer.create_scoring_list(mode)
            self.assertIsInstance(scoring_list, list)
            self.assertGreater(len(scoring_list), 0)
            
            # Test scoring with strategy and profile
            strategy = MACDCanonicalStrategy()
            profile = 'conservative'
            
            scores = self.scorer.score_stocks(
                self.sample_data, 
                strategy=strategy, 
                profile=profile, 
                mode=mode
            )
            
            self.assertIsInstance(scores, dict)
            self.assertGreater(len(scores), 0)
            
            # Verify scores are reasonable
            for stock, score in scores.items():
                self.assertIsInstance(score, (int, float))
                self.assertGreaterEqual(score, 0)
                self.assertLessEqual(score, 100)
        
        self.logger.info("✅ Unified scoring system test passed")
    
    def test_02_strategy_profile_selection(self):
        """Test strategy and profile selection functionality"""
        self.logger.info("Testing strategy and profile selection...")
        
        # Test all strategies
        strategies = [
            MACDCanonicalStrategy(),
            MACDAggressiveStrategy(),
            MACDConservativeStrategy()
        ]
        
        profiles = ['conservative', 'moderate', 'aggressive']
        
        for strategy in strategies:
            for profile in profiles:
                # Test strategy configuration
                strategy.configure_profile(profile)
                
                # Test signal generation
                signals = strategy.generate_signals(self.sample_data['AAPL'])
                
                self.assertIsInstance(signals, pd.DataFrame)
                self.assertGreater(len(signals), 0)
                
                # Verify signal columns exist
                expected_columns = ['signal', 'strength', 'confidence']
                for col in expected_columns:
                    if col in signals.columns:
                        self.assertIsInstance(signals[col].iloc[0], (int, float, str))
        
        self.logger.info("✅ Strategy and profile selection test passed")
    
    def test_03_trading_system_integration(self):
        """Test trading system integration with unified components"""
        self.logger.info("Testing trading system integration...")
        
        # Test trading system initialization
        self.assertIsNotNone(self.trading_system)
        
        # Test profile management
        profiles = self.trading_system.get_available_profiles()
        self.assertIsInstance(profiles, list)
        self.assertGreater(len(profiles), 0)
        
        # Test strategy management
        strategies = self.trading_system.get_available_strategies()
        self.assertIsInstance(strategies, list)
        self.assertGreater(len(strategies), 0)
        
        # Test scoring integration
        scoring_list = self.trading_system.create_scoring_list('backtesting')
        self.assertIsInstance(scoring_list, list)
        
        # Test signal generation
        signals = self.trading_system.generate_signals(
            self.sample_data['AAPL'],
            strategy_name='MACDCanonical',
            profile_name='conservative'
        )
        
        self.assertIsInstance(signals, pd.DataFrame)
        self.assertGreater(len(signals), 0)
        
        self.logger.info("✅ Trading system integration test passed")
    
    def test_04_backtesting_engine(self):
        """Test backtesting engine with new architecture"""
        self.logger.info("Testing backtesting engine...")
        
        engine = BacktestEngine()
        
        # Test single stock backtesting
        results = engine.run_single_stock_backtest(
            self.sample_data['AAPL'],
            strategy_name='MACDCanonical',
            profile_name='conservative',
            initial_capital=10000
        )
        
        self.assertIsInstance(results, dict)
        self.assertIn('total_return', results)
        self.assertIn('sharpe_ratio', results)
        self.assertIn('max_drawdown', results)
        self.assertIn('trades', results)
        
        # Test multi-stock backtesting
        results = engine.run_multi_stock_backtest(
            self.sample_data,
            strategy_name='MACDCanonical',
            profile_name='conservative',
            initial_capital=10000
        )
        
        self.assertIsInstance(results, dict)
        self.assertIn('portfolio_return', results)
        self.assertIn('individual_returns', results)
        
        self.logger.info("✅ Backtesting engine test passed")
    
    def test_05_gui_components(self):
        """Test GUI components and API routes"""
        self.logger.info("Testing GUI components...")
        
        # Test strategy descriptions
        from src.web_dashboard.dashboard_app import app
        
        with app.test_client() as client:
            # Test strategy endpoint
            response = client.get('/api/strategies')
            self.assertEqual(response.status_code, 200)
            
            # Test profile endpoint
            response = client.get('/api/profiles')
            self.assertEqual(response.status_code, 200)
            
            # Test backtesting endpoint
            response = client.post('/api/backtest', json={
                'symbol': 'AAPL',
                'strategy': 'MACDCanonical',
                'profile': 'conservative',
                'start_date': '2023-01-01',
                'end_date': '2023-12-31',
                'initial_capital': 10000
            })
            self.assertEqual(response.status_code, 200)
        
        self.logger.info("✅ GUI components test passed")
    
    def test_06_data_pipeline(self):
        """Test data pipeline and processing"""
        self.logger.info("Testing data pipeline...")
        
        # Test data validation
        for symbol, data in self.sample_data.items():
            # Check required columns
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in required_columns:
                self.assertIn(col, data.columns)
            
            # Check data types
            self.assertIsInstance(data.index, pd.DatetimeIndex)
            
            # Check for missing values
            self.assertEqual(data.isnull().sum().sum(), 0)
        
        self.logger.info("✅ Data pipeline test passed")
    
    def test_07_risk_management(self):
        """Test risk management features"""
        self.logger.info("Testing risk management...")
        
        # Test position sizing
        capital = 10000
        risk_per_trade = 0.02  # 2% risk per trade
        
        position_size = self.trading_system.calculate_position_size(
            capital, risk_per_trade, 150.0, 145.0
        )
        
        self.assertIsInstance(position_size, (int, float))
        self.assertGreater(position_size, 0)
        
        # Test stop loss calculation
        stop_loss = self.trading_system.calculate_stop_loss(
            150.0, 0.05  # 5% stop loss
        )
        
        self.assertIsInstance(stop_loss, (int, float))
        self.assertLess(stop_loss, 150.0)
        
        self.logger.info("✅ Risk management test passed")
    
    def test_08_performance_metrics(self):
        """Test performance metrics calculation"""
        self.logger.info("Testing performance metrics...")
        
        # Create sample trade data
        trades = pd.DataFrame({
            'entry_date': pd.date_range('2023-01-01', periods=10),
            'exit_date': pd.date_range('2023-01-02', periods=10),
            'entry_price': [100, 105, 110, 95, 120, 115, 125, 130, 135, 140],
            'exit_price': [105, 110, 115, 100, 125, 120, 130, 135, 140, 145],
            'quantity': [100, 100, 100, 100, 100, 100, 100, 100, 100, 100],
            'side': ['buy', 'buy', 'buy', 'buy', 'buy', 'buy', 'buy', 'buy', 'buy', 'buy']
        })
        
        # Calculate metrics
        metrics = self.trading_system.calculate_performance_metrics(trades)
        
        self.assertIsInstance(metrics, dict)
        self.assertIn('total_return', metrics)
        self.assertIn('win_rate', metrics)
        self.assertIn('profit_factor', metrics)
        self.assertIn('max_drawdown', metrics)
        
        self.logger.info("✅ Performance metrics test passed")
    
    def test_09_configuration_management(self):
        """Test configuration management"""
        self.logger.info("Testing configuration management...")
        
        # Test config loading
        self.assertIsNotNone(self.config)
        self.assertIsInstance(self.config, dict)
        
        # Test strategy configurations
        strategy_configs = self.config.get('strategies', {})
        self.assertIsInstance(strategy_configs, dict)
        
        # Test profile configurations
        profile_configs = self.config.get('profiles', {})
        self.assertIsInstance(profile_configs, dict)
        
        self.logger.info("✅ Configuration management test passed")
    
    def test_10_error_handling(self):
        """Test error handling and edge cases"""
        self.logger.info("Testing error handling...")
        
        # Test with empty data
        empty_data = pd.DataFrame()
        
        with self.assertRaises(Exception):
            self.scorer.score_stocks(empty_data)
        
        # Test with invalid strategy
        with self.assertRaises(Exception):
            self.trading_system.generate_signals(
                self.sample_data['AAPL'],
                strategy_name='InvalidStrategy',
                profile_name='conservative'
            )
        
        # Test with invalid profile
        with self.assertRaises(Exception):
            self.trading_system.generate_signals(
                self.sample_data['AAPL'],
                strategy_name='MACDCanonical',
                profile_name='invalid_profile'
            )
        
        self.logger.info("✅ Error handling test passed")

def run_comprehensive_tests():
    """Run all comprehensive tests"""
    print("🧪 Starting Comprehensive System Tests...")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(ComprehensiveSystemTest)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("=" * 60)
    print(f"📊 Test Results:")
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    print(f"   Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback}")
    
    if result.errors:
        print("\n❌ Errors:")
        for test, traceback in result.errors:
            print(f"   - {test}: {traceback}")
    
    if not result.failures and not result.errors:
        print("\n🎉 All tests passed! System is working correctly.")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1) 