# SMART STOCK TRADING SYSTEM

An AI-driven, modular stock trading system with comprehensive backtesting, strategy optimization, and educational insights.

## 🚀 Features

### Phase 1 - Core Features ✅
- **Data Engine**: Historical and real-time stock data via yfinance
- **Technical Indicators**: MACD, RSI, EMA, Bollinger Bands, Volume MA
- **Strategy Engine**: Rule-based entry/exit conditions with scoring system
- **Backtesting Engine**: Trade simulation with performance metrics
- **Capital Projection**: Growth simulation with monthly targets

### Phase 2 - Advanced Features 🔄
- **Dashboard UI**: Interactive Streamlit dashboard
- **Trade Analysis**: Detailed trade logic and performance analysis
- **Dry Run Mode**: Real-time simulation without execution
- **Risk Management**: Stop-loss, drawdown protection, circuit breakers
- **Performance Benchmarking**: Sharpe ratio, Sortino ratio, max drawdown

### Phase 3 - Scalability 🔄
- **Strategy Diversification**: Multiple strategies and sectors
- **Account Scaling**: Dynamic position sizing
- **Trade Journal**: SQLite persistence with learning notes
- **Deployment**: Git versioning and Docker support

### Phase 4 - AI Integration 🔄
- **LLM-Powered Analysis**: GPT-based trade feedback and improvements

## 📁 Project Structure

```
StockTradeSolution/
├── src/
│   ├── data_engine/          # Data fetching and storage
│   ├── indicators/           # Technical indicators
│   ├── strategies/           # Trading strategies
│   ├── backtesting/          # Backtesting engine
│   ├── risk_management/      # Risk controls
│   ├── dashboard/            # Streamlit UI
│   └── utils/               # Shared utilities
├── tests/                   # Test suite
├── config/                  # Configuration files
├── data/                    # Data storage
├── logs/                    # System logs
└── docs/                    # Documentation
```

## 🛠️ Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd StockTradeSolution
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run tests:
```bash
pytest tests/
```

4. Start the dashboard:
```bash
streamlit run src/dashboard/main.py
```

## 🧪 Testing

The system includes comprehensive testing:
- Unit tests for each module
- Integration tests for data flow
- Performance benchmarks
- Strategy validation tests

Run the full test suite:
```bash
python tests/test_suite.py
```

## 📊 Usage

### Basic Backtesting
```python
from src.data_engine import DataEngine
from src.strategies import MACDStrategy
from src.backtesting import BacktestEngine

# Initialize components
data_engine = DataEngine()
strategy = MACDStrategy()
backtest = BacktestEngine()

# Run backtest
results = backtest.run(strategy, "AAPL", "2023-01-01", "2023-12-31")
```

### Dashboard Access
Launch the interactive dashboard to visualize:
- Trade logs and performance
- Capital growth projections
- Strategy comparisons
- Risk metrics

## 🔧 Configuration

Edit `config/settings.yaml` to customize:
- Default strategies
- Risk parameters
- Data sources
- Dashboard settings

## 📈 Performance Metrics

The system tracks:
- Total Return
- Sharpe Ratio
- Maximum Drawdown
- Win Rate
- Average Trade Duration
- Risk-Adjusted Returns

## 🤝 Contributing

1. Follow the modular development structure
2. Write tests for new features
3. Use black for code formatting
4. Update documentation

## 📝 License

MIT License - see LICENSE file for details

## 🚨 Disclaimer

This system is for educational and research purposes. Past performance does not guarantee future results. Always conduct thorough testing before live trading. 