# Automation Framework Documentation

## Overview

The Automation Framework is a comprehensive system for automated stock trading that supports multiple trading modes, intelligent stock selection, advanced signal generation, and risk management. It provides both backtesting capabilities and live trading automation.

## Architecture

### Core Components

1. **Automation Engine** (`src/real_time_trading/automation_engine.py`)
   - Main orchestrator for automated trading
   - Handles stock analysis, signal generation, and trade execution
   - Supports multiple trading modes

2. **Position Manager** (`src/real_time_trading/position_manager.py`)
   - Tracks and manages trading positions
   - Calculates P&L and portfolio metrics
   - Enforces position limits and risk management

3. **Automation Scheduler** (`src/real_time_trading/automation_scheduler.py`)
   - Runs automated cycles at specified intervals
   - Manages market hours and scheduling
   - Tracks performance metrics

4. **Paper Trading Broker** (`src/real_time_trading/paper_trading.py`)
   - Simulates real trading without actual money
   - Provides realistic trading environment
   - Tracks account balance and positions

## Trading Modes

### 1. Paper Trading Mode
- **Purpose**: Safe testing and learning environment
- **Features**: 
  - Simulates real trading with virtual money
  - No risk of losing actual capital
  - Perfect for strategy validation
- **Use Case**: Testing new strategies, learning the system

### 2. Semi-Automatic Mode
- **Purpose**: Human oversight with automation assistance
- **Features**:
  - Generates trade signals automatically
  - Requires manual approval before execution
  - Provides detailed analysis and reasoning
- **Use Case**: Conservative trading with human oversight

### 3. Full Automatic Mode
- **Purpose**: Complete automation with risk management
- **Features**:
  - Fully automated trading based on signals
  - Built-in risk management and position sizing
  - Continuous monitoring and adjustment
- **Use Case**: Hands-off trading for experienced users

### 4. Manual Mode
- **Purpose**: Manual trading with automation assistance
- **Features**:
  - Provides analysis and signals for manual review
  - No automatic execution
  - Full control over trade decisions
- **Use Case**: Manual trading with automated analysis

## Configuration

### Automation Settings

```yaml
automation:
  mode: "paper_trading"  # paper_trading, semi_auto, full_auto, manual
  watchlist:
    - "AAPL"
    - "MSFT"
    - "GOOGL"
    - "AMZN"
    - "TSLA"
    - "NVDA"
    - "META"
    - "NFLX"
    - "SPY"
    - "QQQ"
  
  # Risk Management
  max_positions: 5
  position_size: 20  # Percentage of portfolio
  stop_loss: 5       # Percentage
  take_profit: 15    # Percentage
  risk_level: "medium"  # low, medium, high
  
  # Scheduling
  cycle_interval: 300  # Seconds between cycles
  market_hours_only: true
  
  # Paper Trading Settings
  paper_trading:
    initial_cash: 100000
    commission: 0.00
    slippage: 0.00
```

## Features

### 1. Intelligent Stock Selection
- **Multi-Strategy Analysis**: Analyzes stocks using multiple strategies (MACD, RSI, etc.)
- **Confidence Scoring**: Each signal includes a confidence score (0-100%)
- **Risk Assessment**: Evaluates volatility, trend, and support/resistance levels
- **Watchlist Management**: Easy addition/removal of stocks to monitor

### 2. Advanced Signal Generation
- **Multi-Strategy Signals**: Combines signals from multiple strategies
- **Confidence-Based Filtering**: Only executes high-confidence signals
- **Risk-Adjusted Position Sizing**: Position size based on confidence and risk
- **Market Condition Analysis**: Considers overall market conditions

### 3. Risk Management
- **Position Limits**: Maximum number of concurrent positions
- **Stop Loss**: Automatic position closure on losses
- **Take Profit**: Automatic profit taking at specified levels
- **Portfolio Diversification**: Limits exposure per position
- **Drawdown Protection**: Prevents excessive losses

### 4. Performance Tracking
- **Real-time Metrics**: Live P&L, win rate, Sharpe ratio
- **Cycle Analysis**: Detailed analysis of each automation cycle
- **Historical Performance**: Tracks performance over time
- **Risk Metrics**: Maximum drawdown, volatility analysis

## Dashboard Integration

### Automation Tab Features

1. **Status Overview**
   - Current automation status (Running/Stopped)
   - Trading mode display
   - Last cycle time and cycle count
   - Active positions count

2. **Configuration Panel**
   - Mode selection (Paper Trading, Semi-Auto, Full Auto, Manual)
   - Risk parameters (max positions, position size, stop loss, take profit)
   - Watchlist management
   - Save/load configuration

3. **Position Management**
   - Real-time position tracking
   - P&L calculation and display
   - Position details (entry price, current price, duration)
   - Manual position closure

4. **Performance Metrics**
   - Total P&L and percentage return
   - Win rate and average return
   - Sharpe ratio and risk metrics
   - Historical performance charts

5. **Logs and Monitoring**
   - Real-time automation logs
   - Signal generation details
   - Error tracking and debugging
   - Export functionality

## API Endpoints

### Automation Control
- `POST /api/automation/start` - Start automation
- `POST /api/automation/stop` - Stop automation
- `POST /api/automation/cycle` - Run single cycle
- `GET /api/automation/status` - Get automation status

### Configuration
- `GET /api/automation/config` - Get current configuration
- `PUT /api/automation/config` - Update configuration

### Positions and Performance
- `GET /api/automation/positions` - Get current positions
- `GET /api/automation/performance` - Get performance metrics
- `POST /api/automation/positions/{symbol}/close` - Close position

### Logs and Monitoring
- `GET /api/automation/logs` - Get automation logs
- `DELETE /api/automation/logs` - Clear logs
- `GET /api/automation/logs/export` - Export logs

## Usage Examples

### Starting Paper Trading
```python
from src.real_time_trading.automation_engine import AutomationEngine
from src.utils.config_loader import config

# Initialize automation engine
engine = AutomationEngine(config)

# Start paper trading
engine.start_automation('paper_trading')

# Run a single cycle
result = engine.run_cycle()
print(f"Analyzed {len(result['analysis'])} stocks")
print(f"Generated {len(result['signals'])} signals")
print(f"Executed {len(result['executed_trades'])} trades")
```

### Manual Position Management
```python
from src.real_time_trading.position_manager import PositionManager

# Initialize position manager
pm = PositionManager()

# Add a position
pm.add_position('AAPL', 10, 150.00)

# Update price
pm.update_position_price('AAPL', 155.00)

# Get portfolio summary
summary = pm.get_portfolio_summary()
print(f"Total P&L: ${summary['total_pnl']:.2f}")
```

### Running Automation Scheduler
```python
from src.real_time_trading.automation_scheduler import AutomationScheduler
from src.utils.config_loader import config

# Initialize scheduler
scheduler = AutomationScheduler(config)

# Start automated trading
scheduler.start()

# Check status
status = scheduler.get_status()
print(f"Running: {status['is_running']}")
print(f"Cycles completed: {status['cycle_count']}")
```

## Testing

### Running Tests
```bash
# Test automation framework
python test_automation.py

# Test specific components
python -m pytest tests/test_automation_engine.py
python -m pytest tests/test_position_manager.py
```

### Test Coverage
- Automation engine initialization and modes
- Position management operations
- Signal generation and execution
- Risk management and position sizing
- Performance metrics calculation
- Scheduler functionality

## Best Practices

### 1. Start with Paper Trading
- Always test strategies in paper trading mode first
- Validate performance over multiple market cycles
- Ensure risk management is working correctly

### 2. Gradual Automation
- Begin with semi-automatic mode for oversight
- Move to full automatic only after thorough testing
- Monitor performance closely during transition

### 3. Risk Management
- Set conservative position limits initially
- Use stop losses to limit downside
- Diversify across multiple stocks and sectors

### 4. Regular Monitoring
- Check performance metrics daily
- Review automation logs for errors
- Adjust parameters based on market conditions

### 5. Configuration Management
- Save working configurations
- Document parameter changes
- Test configuration changes in paper trading

## Troubleshooting

### Common Issues

1. **No Signals Generated**
   - Check watchlist configuration
   - Verify market data availability
   - Review strategy parameters

2. **Poor Performance**
   - Analyze win rate and average return
   - Check risk management settings
   - Review market conditions

3. **System Errors**
   - Check automation logs
   - Verify data engine connectivity
   - Review configuration settings

### Debug Mode
Enable detailed logging for troubleshooting:
```python
import logging
logging.getLogger('src.real_time_trading').setLevel(logging.DEBUG)
```

## Future Enhancements

### Planned Features
1. **Broker Integration**: Support for real broker APIs
2. **Advanced Strategies**: More sophisticated trading strategies
3. **Machine Learning**: ML-based signal generation
4. **Portfolio Optimization**: Advanced portfolio management
5. **Real-time Alerts**: Email/SMS notifications
6. **Mobile Dashboard**: Mobile-friendly interface

### Performance Optimizations
1. **Parallel Processing**: Multi-threaded stock analysis
2. **Caching**: Improved data caching mechanisms
3. **Database Integration**: Persistent storage for historical data
4. **API Rate Limiting**: Smart API usage management

## Support

For questions, issues, or feature requests:
1. Check the logs for error details
2. Review configuration settings
3. Test with paper trading mode
4. Consult the troubleshooting guide

The automation framework provides a robust foundation for automated trading while maintaining safety through proper risk management and testing capabilities. 