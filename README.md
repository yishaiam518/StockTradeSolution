# 🚀 StockTradeSolution

**Advanced Stock Trading System with Unified Architecture, Comprehensive Testing Framework, and Enhanced Dashboard Features**

## 📊 Overview

StockTradeSolution is a sophisticated trading system that combines multiple strategies, risk management, and real-time automation. The system features a unified architecture where backtesting, historic backtesting, and automation use the same building blocks.

## 🎯 Key Features

### 🔧 **Unified Architecture**
- **Strategy + Profile Selection**: Choose from multiple MACD strategies with different risk profiles
- **Unified Stock Scoring**: Separate scoring lists for backtesting, historic, and automation modes
- **Modular Design**: Clean separation of concerns with reusable components

### 📈 **Trading Strategies**
- **MACD Canonical**: Pure MACD crossover strategy
- **MACD Aggressive**: Higher risk, higher potential returns
- **MACD Conservative**: Lower risk, steady returns
- **Profile Management**: Conservative, Moderate, Aggressive risk profiles

### 🧪 **Comprehensive Testing Framework**
- **Multiple Test Scripts**: Unit tests, integration tests, performance benchmarks
- **Automated Testing**: Run all tests with a single command
- **Mock Data Generation**: Realistic testing scenarios
- **Performance Benchmarking**: Memory and execution time analysis

### 📊 **Enhanced Reporting**
- **Detailed Trade Reports**: Full buy/sell dates, prices, P&L analysis
- **Strategy Performance**: Individual strategy and profile analysis
- **Risk Metrics**: Drawdown, volatility, Sharpe ratio calculations
- **Symbol Analysis**: Performance breakdown by stock symbol

### 🖥️ **Interactive Dashboard**
- **Web-based GUI**: Modern, responsive interface
- **Real-time Updates**: Live performance metrics
- **Strategy Selection**: Dynamic strategy and profile configuration
- **Trade History**: Comprehensive trade tracking

## 🏗️ Architecture

```
StockTradeSolution/
├── src/
│   ├── backtesting/          # Backtesting engine
│   ├── data_collection/      # Data collection and scheduling
│   ├── data_engine/          # Data processing and storage
│   ├── indicators/           # Technical indicators
│   ├── machine_learning/     # ML models and scoring
│   ├── portfolio_management/ # Portfolio optimization
│   ├── real_time_trading/    # Live trading automation
│   ├── risk_management/      # Risk controls
│   ├── strategies/           # Trading strategies
│   ├── utils/               # Utilities and configuration
│   └── web_dashboard/       # Web interface
├── tests/                   # Test suite
├── config/                  # Configuration files
├── data/                    # Data storage
├── logs/                    # System logs
└── models/                  # Trained models
```

## 🚀 Quick Start

### 1. **Installation**
```bash
# Clone the repository
git clone https://github.com/yishaiam518/StockTradeSolution.git
cd StockTradeSolution

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. **Run Tests**
```bash
# Run all tests
python run_all_tests.py

# Run specific test
python test_simple_verification.py
```

### 3. **Generate Trade Report**
```bash
python generate_trade_report.py
```

### 4. **Start Dashboard**
```bash
python simple_dashboard.py
# Access at: http://localhost:8080
```

## 📊 Performance Highlights

### Recent Trade Report Summary (25 trades):
- **76% Win Rate** (19 winning, 6 losing trades)
- **$119,616.78 Total P&L**
- **$4,784.67 Average P&L per trade**
- **$22,369.06 Max Profit** vs **-$3,400.79 Max Loss**

### Strategy Performance:
- **MACDCanonical**: $47,028.72 (23.2% avg return)
- **MACDAggressive**: $30,981.85 (12.2% avg return)
- **MACDConservative**: $41,606.21 (7.4% avg return)

### Profile Performance:
- **Moderate**: $64,887.76 (21.9% avg return)
- **Conservative**: $28,846.55 (5.7% avg return)
- **Aggressive**: $25,882.47 (7.8% avg return)

## 🧪 Testing Framework

### Test Scripts:
- `test_simple_verification.py`: Basic functionality tests
- `test_comprehensive_system.py`: Full system integration tests
- `test_performance_benchmark.py`: Performance analysis
- `run_all_tests.py`: Master test runner

### Test Coverage:
- ✅ Configuration loading
- ✅ Data pipeline functionality
- ✅ Strategy implementations
- ✅ Technical indicators
- ✅ Risk management
- ✅ Portfolio management
- ✅ Utility functions

## 📈 Dashboard Features

### Interactive Elements:
- **Strategy Selection**: Choose from MACD variants
- **Profile Configuration**: Risk profile management
- **Backtesting**: Run simulations with custom parameters
- **Performance Metrics**: Real-time performance tracking
- **Trade History**: Detailed trade analysis

### API Endpoints:
- `/api/strategies`: Available strategies
- `/api/profiles`: Risk profiles
- `/api/backtest`: Run backtests
- `/api/trades`: Trade history
- `/api/performance`: Performance metrics

## 🔧 Configuration

### Main Configuration (`config/settings.yaml`):
```yaml
trading:
  default_strategy: MACDCanonical
  default_profile: moderate
  risk_management:
    max_position_size: 0.1
    stop_loss: 0.05
    take_profit: 0.15

data:
  sources:
    - yahoo_finance
    - alpha_vantage
  update_frequency: 1h

backtesting:
  start_date: 2023-01-01
  end_date: 2023-12-31
  initial_capital: 100000
```

## 📋 File Structure

### Core Files:
- `simple_dashboard.py`: Main dashboard application
- `generate_trade_report.py`: Enhanced trade reporting
- `run_all_tests.py`: Test orchestration
- `src/trading_system.py`: Main trading system
- `src/strategies/base_strategy.py`: Strategy framework

### Documentation:
- `TESTING_GUIDE.md`: Testing framework documentation
- `UNIFIED_ARCHITECTURE.md`: Architecture overview
- `ARCHITECTURE_IMPROVEMENTS.md`: Improvement roadmap

## 🚧 Current Status

### ✅ **Completed Features:**
- Unified architecture with strategy + profile selection
- Comprehensive testing framework
- Enhanced trade reporting with detailed P&L analysis
- Interactive web dashboard
- Risk management and portfolio optimization
- Real-time trading automation framework

### 🔄 **In Progress:**
- GUI improvements and additional features
- Enhanced data collection and processing
- Advanced machine learning models
- Real-time market data integration

### 📋 **Planned Features:**
- Advanced charting and visualization
- Multi-asset portfolio management
- Social trading features
- Mobile application
- API for external integrations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For questions, issues, or contributions, please:
- Open an issue on GitHub
- Check the documentation in the `/docs` folder
- Review the testing guide for troubleshooting

---

**🎯 Built with ❤️ for advanced algorithmic trading** 