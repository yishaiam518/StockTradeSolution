# AI-Driven Stock Trading System - Phase 2

## Overview

Phase 2 extends the modular stock trading system with advanced AI-driven features including real-time trading, machine learning price prediction, portfolio management, and web-based monitoring.

## 🚀 New Features in Phase 2

### 1. Real-Time Trading Engine
- **Paper Trading Simulation**: Risk-free trading environment
- **Market Hours Detection**: Automatic market open/close detection
- **Order Management**: Comprehensive order lifecycle tracking
- **Position Management**: Real-time P&L calculation
- **Risk Controls**: Daily trade limits and position sizing

### 2. Machine Learning Price Prediction
- **Multiple Algorithms**: LSTM, GRU, and Transformer models
- **Automatic Training**: Configurable retraining schedules
- **Confidence Scoring**: Uncertainty quantification for predictions
- **Feature Engineering**: Advanced technical indicator integration
- **Model Persistence**: Save/load trained models

### 3. Portfolio Management
- **Dynamic Rebalancing**: Automatic portfolio rebalancing
- **Sector Diversification**: Industry-based allocation limits
- **Performance Tracking**: Comprehensive metrics and analytics
- **Risk Optimization**: Advanced portfolio optimization algorithms
- **Data Export/Import**: Portfolio persistence and backup

### 4. Web Dashboard
- **Real-Time Monitoring**: Live portfolio and trading status
- **Interactive Charts**: Candlestick charts with indicators
- **Performance Analytics**: Visual performance metrics
- **Strategy Management**: Web-based strategy configuration
- **API Endpoints**: RESTful API for external integrations

### 5. Advanced Risk Management
- **Position Sizing**: Kelly Criterion and volatility-based sizing
- **Correlation Analysis**: Portfolio correlation monitoring
- **Drawdown Protection**: Circuit breakers and stop-losses
- **Stress Testing**: Monte Carlo simulation capabilities
- **VaR Calculation**: Value at Risk modeling

## 📁 Project Structure

```
StockTradeSolution/
├── config/
│   └── settings.yaml          # Phase 2 configuration
├── src/
│   ├── real_time_trading/     # Real-time trading engine
│   │   ├── trading_engine.py
│   │   ├── paper_trading.py
│   │   ├── order_manager.py
│   │   └── position_manager.py
│   ├── machine_learning/      # ML price prediction
│   │   ├── price_prediction.py
│   │   ├── sentiment_analysis.py
│   │   ├── pattern_recognition.py
│   │   └── risk_model.py
│   ├── portfolio_management/  # Portfolio management
│   │   ├── portfolio_manager.py
│   │   ├── allocation_engine.py
│   │   ├── rebalancing_engine.py
│   │   └── risk_optimizer.py
│   ├── web_dashboard/        # Web interface
│   │   ├── dashboard_app.py
│   │   ├── chart_generator.py
│   │   └── api_routes.py
│   └── [existing modules]    # Phase 1 components
├── models/                   # Trained ML models
├── data/                     # Market data cache
├── logs/                     # System logs
├── example_phase2_usage.py   # Phase 2 examples
└── requirements.txt          # Updated dependencies
```

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- Virtual environment recommended

### Setup
```bash
# Clone the repository
git clone <repository-url>
cd StockTradeSolution

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install optional ML dependencies
pip install tensorflow torch transformers
```

## 🚀 Quick Start

### 1. Basic Phase 2 Demo
```bash
python example_phase2_usage.py
```

### 2. Start Web Dashboard
```bash
python -m src.web_dashboard.dashboard_app
```
Then visit `http://localhost:8080`

### 3. Real-Time Trading
```python
from src.real_time_trading.trading_engine import TradingEngine

# Initialize trading engine
trading_engine = TradingEngine()

# Start trading session
await trading_engine.run_trading_session(strategies, symbols)
```

### 4. ML Price Prediction
```python
from src.machine_learning.price_prediction import PricePredictionModel

# Initialize ML model
model = PricePredictionModel()

# Train model
model.train("AAPL", period="2y")

# Make predictions
predictions = model.predict("AAPL", days_ahead=5)
```

## 📊 Configuration

### Real-Time Trading
```yaml
real_time_trading:
  enabled: true
  broker: "paper_trading"
  paper_trading:
    initial_balance: 100000.0
    commission: 0.005
    slippage: 0.001
  execution_settings:
    max_daily_trades: 50
    trading_hours:
      start: "09:30"
      end: "16:00"
      timezone: "America/New_York"
```

### Machine Learning
```yaml
machine_learning:
  enabled: true
  models:
    price_prediction:
      enabled: true
      algorithm: "lstm"
      lookback_period: 60
      prediction_horizon: 5
      retrain_frequency: 7
```

### Portfolio Management
```yaml
portfolio_management:
  enabled: true
  rebalancing:
    frequency: "monthly"
    method: "equal_weight"
    threshold: 5.0
  allocation:
    max_single_position: 10.0
    sector_limits:
      technology: 30.0
      healthcare: 20.0
      financial: 20.0
```

## 🔧 API Endpoints

### Portfolio Management
- `GET /api/portfolio` - Get portfolio summary
- `GET /api/performance` - Get performance metrics
- `POST /api/backtest` - Run backtest
- `GET /api/trades` - Get trade history

### Trading Control
- `POST /api/trading/start` - Start trading session
- `POST /api/trading/stop` - Stop trading session
- `GET /api/trading/status` - Get trading status

### Data & Charts
- `GET /api/chart/<symbol>` - Get chart data
- `GET /api/strategies` - Get available strategies
- `GET /api/symbols` - Get available symbols

## 📈 Features in Detail

### Real-Time Trading Engine

The real-time trading engine provides:
- **Paper Trading**: Simulate trades without real money
- **Market Hours**: Automatic detection of market open/close
- **Order Types**: Market, limit, stop, and stop-limit orders
- **Position Tracking**: Real-time P&L and position management
- **Risk Controls**: Daily limits and position sizing

```python
# Example: Real-time trading session
trading_engine = TradingEngine()
strategies = {'AAPL': MACDStrategy(), 'MSFT': MACDStrategy()}
symbols = ['AAPL', 'MSFT']

await trading_engine.run_trading_session(strategies, symbols)
```

### Machine Learning Price Prediction

Advanced ML models for price prediction:
- **LSTM Networks**: Long Short-Term Memory for time series
- **GRU Networks**: Gated Recurrent Units for efficiency
- **Transformer Models**: Attention-based architectures
- **Automatic Training**: Scheduled model retraining
- **Confidence Scoring**: Uncertainty quantification

```python
# Example: ML price prediction
model = PricePredictionModel()
model.train("AAPL", period="2y")
predictions = model.predict("AAPL", days_ahead=5)
confidence = model.get_prediction_confidence("AAPL")
```

### Portfolio Management

Comprehensive portfolio management:
- **Dynamic Rebalancing**: Automatic portfolio rebalancing
- **Sector Diversification**: Industry-based allocation
- **Performance Analytics**: Comprehensive metrics
- **Risk Optimization**: Advanced optimization algorithms
- **Data Persistence**: Export/import functionality

```python
# Example: Portfolio management
portfolio_manager = PortfolioManager()
portfolio_manager.add_position("AAPL", 100, 150.0, "technology")
portfolio_manager.set_target_allocation({'AAPL': 25.0, 'MSFT': 25.0})
rebalancing_needed = portfolio_manager.check_rebalancing_needed(current_prices)
```

### Web Dashboard

Interactive web interface:
- **Real-Time Updates**: Live portfolio and trading data
- **Interactive Charts**: Candlestick charts with indicators
- **Performance Metrics**: Visual analytics and reports
- **Strategy Management**: Web-based configuration
- **API Integration**: RESTful API endpoints

## 🔒 Security & Risk Management

### Risk Controls
- **Position Limits**: Maximum position sizes
- **Daily Trade Limits**: Prevent overtrading
- **Drawdown Protection**: Circuit breakers
- **Correlation Monitoring**: Portfolio diversification
- **VaR Calculation**: Value at Risk modeling

### Data Security
- **Encrypted Storage**: Secure data persistence
- **API Authentication**: JWT-based authentication
- **Rate Limiting**: API request throttling
- **Audit Logging**: Comprehensive activity logs

## 📊 Performance Metrics

### Trading Performance
- **Total Return**: Overall portfolio performance
- **Sharpe Ratio**: Risk-adjusted returns
- **Maximum Drawdown**: Worst peak-to-trough decline
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Ratio of gross profit to gross loss

### Portfolio Analytics
- **Sector Allocation**: Industry diversification
- **Correlation Matrix**: Position correlations
- **Volatility Analysis**: Risk measurement
- **Rebalancing Frequency**: Portfolio maintenance
- **Transaction Costs**: Impact of fees and slippage

## 🚀 Advanced Features

### Machine Learning Integration
- **Ensemble Methods**: Multiple model predictions
- **Feature Selection**: Automatic feature engineering
- **Hyperparameter Tuning**: Automated optimization
- **Model Validation**: Cross-validation and testing
- **Prediction Intervals**: Confidence bounds

### Portfolio Optimization
- **Mean-Variance Optimization**: Modern Portfolio Theory
- **Risk Parity**: Equal risk contribution
- **Black-Litterman**: Bayesian portfolio optimization
- **Monte Carlo Simulation**: Stress testing
- **Scenario Analysis**: What-if analysis

### Real-Time Analytics
- **Stream Processing**: Real-time data analysis
- **Alert System**: Custom trading alerts
- **Performance Monitoring**: Live metrics
- **Risk Dashboard**: Real-time risk metrics
- **Compliance Reporting**: Regulatory reporting

## 🔧 Development

### Adding New Strategies
```python
from src.strategies.base_strategy import BaseStrategy

class MyStrategy(BaseStrategy):
    def generate_signals(self, data):
        # Implement your strategy logic
        return {'action': 'BUY', 'confidence': 0.8}
```

### Adding New ML Models
```python
from src.machine_learning.price_prediction import PricePredictionModel

class CustomModel(PricePredictionModel):
    def build_model(self, input_shape):
        # Implement your custom model
        return model
```

### Adding New Indicators
```python
from src.indicators.indicators import TechnicalIndicators

class CustomIndicator(TechnicalIndicators):
    def calculate(self, data):
        # Implement your indicator
        return indicator_values
```

## 📝 Testing

### Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test
pytest tests/test_real_time_trading.py
```

### Test Coverage
- Unit tests for all components
- Integration tests for workflows
- Performance benchmarks
- ML model validation
- Risk management tests

## 📚 Documentation

### API Documentation
- RESTful API endpoints
- WebSocket events
- Data schemas
- Authentication methods

### User Guides
- Getting started guide
- Strategy development
- ML model training
- Dashboard usage
- Risk management

### Developer Guides
- Architecture overview
- Component development
- Testing guidelines
- Deployment guide

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create feature branch
3. Implement changes
4. Add tests
5. Submit pull request

### Code Standards
- Follow PEP 8 style guide
- Add type hints
- Write comprehensive tests
- Update documentation
- Maintain backward compatibility

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### Getting Help
- Check the documentation
- Review example scripts
- Search existing issues
- Create new issue with details

### Community
- GitHub Discussions
- Stack Overflow tags
- Discord community
- Email support

## 🎯 Roadmap

### Phase 3 (Future)
- **Advanced ML**: Deep reinforcement learning
- **Multi-Asset**: Options, futures, crypto
- **Cloud Deployment**: AWS/Azure integration
- **Mobile App**: iOS/Android applications
- **Social Trading**: Copy trading features

### Phase 4 (Future)
- **AI Agents**: Autonomous trading agents
- **Quantum Computing**: Quantum algorithms
- **Blockchain**: DeFi integration
- **Global Markets**: International exchanges
- **Regulatory Compliance**: Advanced compliance

---

**Note**: This is a sophisticated trading system. Always test thoroughly in paper trading mode before using real money. Past performance does not guarantee future results. 