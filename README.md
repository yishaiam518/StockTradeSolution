# StockTradeSolution 🚀

A comprehensive algorithmic trading system with web-based dashboard, real-time data collection, and advanced backtesting capabilities.

## 🌟 Features

### 📊 **Trading Dashboard**
- **Strategy Selection**: Multiple MACD-based strategies (Conservative, Moderate, Aggressive, Enhanced)
- **Real-time Backtesting**: Historical data analysis with custom date ranges
- **Performance Analytics**: KPI tracking and trade history visualization
- **Portfolio Management**: Real-time position tracking and P&L calculations

### 📈 **Data Collection Module**
- **Multi-Exchange Support**: NASDAQ, NYSE, AMEX data collection
- **Flexible Time Periods**: Custom date ranges and predefined periods
- **Persistent Storage**: SQLite database for data collections
- **Stock Viewer**: Full-screen interactive charts with Syncfusion integration

### 🔧 **Advanced Features**
- **Caching System**: Optimized data retrieval and storage
- **Technical Indicators**: MACD, RSI, EMA, Volume analysis
- **Risk Management**: Position sizing and stop-loss mechanisms
- **Real-time Updates**: WebSocket integration for live data

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- pip
- Git

### Setup
```bash
# Clone the repository
git clone https://github.com/yishaiam518/StockTradeSolution.git
cd StockTradeSolution

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the dashboard
python start_dashboard.py
```

## 🚀 Quick Start

1. **Start the Dashboard**:
   ```bash
   python start_dashboard.py
   ```

2. **Access the Web Interface**:
   - Open browser to `http://localhost:8080`
   - Navigate to "Data Collection" tab
   - Select exchange and time period
   - Start data collection

3. **Run Backtests**:
   - Go to "Historical Backtesting" tab
   - Select strategy and time period
   - View results and trade history

## 📁 Project Structure

```
StockTradeSolution/
├── src/
│   ├── backtesting/          # Backtesting engine
│   ├── data_collection/      # Data collection module
│   ├── data_engine/          # Data processing and caching
│   ├── indicators/           # Technical indicators
│   ├── machine_learning/     # ML models and analysis
│   ├── portfolio_management/ # Portfolio tracking
│   ├── real_time_trading/    # Live trading components
│   ├── strategies/           # Trading strategies
│   ├── utils/               # Utility functions
│   └── web_dashboard/       # Web interface
├── config/                  # Configuration files
├── data/                    # Data storage
├── logs/                    # Application logs
├── tests/                   # Test files
└── requirements.txt         # Python dependencies
```

## 🎯 Key Components

### **Trading Strategies**
- **MACD Conservative**: Low-risk, steady returns
- **MACD Moderate**: Balanced risk/reward
- **MACD Aggressive**: High-risk, high-reward
- **MACD Enhanced**: Advanced with additional filters

### **Data Collection**
- **Multi-Exchange**: NASDAQ, NYSE, AMEX support
- **Historical Data**: Up to 5 years of data
- **Real-time Updates**: Live market data integration
- **Persistent Storage**: SQLite database

### **Web Dashboard**
- **Interactive Charts**: Syncfusion-powered visualizations
- **Real-time Updates**: Live data streaming
- **Performance Metrics**: Comprehensive KPI tracking
- **User-friendly Interface**: Modern, responsive design

## 🔧 Configuration

### Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration Files
- `config/settings.yaml`: Main configuration
- `requirements.txt`: Python dependencies

## 📊 Usage Examples

### Data Collection
```python
# Collect NASDAQ data for 1 year
# Navigate to Data Collection tab
# Select: Exchange = NASDAQ, Period = 1 Year
# Click "Start Collection"
```

### Backtesting
```python
# Run historical backtest
# Navigate to Historical Backtesting tab
# Select: Strategy = MACD Enhanced, Period = 1 Year
# Click "Run Backtest"
# View results in Trade History
```

### Stock Viewer
```python
# View individual stock data
# From Data Collection, click "View" on any collection
# Select stock from dropdown
# View interactive charts and technical indicators
```

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/

# Run specific test
python test_comprehensive_backtest.py
```

## 📈 Performance

- **Data Collection**: 1000+ stocks per minute
- **Backtesting**: Real-time strategy evaluation
- **Web Interface**: Responsive, modern UI
- **Caching**: Optimized data retrieval

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: Create an issue on GitHub
- **Documentation**: Check the code comments and docstrings
- **Community**: Join our discussions

## 🔮 Roadmap

- [ ] Real-time trading integration
- [ ] Additional technical indicators
- [ ] Machine learning model integration
- [ ] Mobile app development
- [ ] API documentation
- [ ] Docker containerization

## 📞 Contact

- **GitHub**: [yishaiam518](https://github.com/yishaiam518)
- **Project**: [StockTradeSolution](https://github.com/yishaiam518/StockTradeSolution)

---

**Made with ❤️ for algorithmic trading enthusiasts** 