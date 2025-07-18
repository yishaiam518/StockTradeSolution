# Unified Architecture for Stock Trading System

## Overview

The new unified architecture addresses the user's requirements by creating a consistent building block system where:

1. **Strategy + Profile Selection** → **Scoring System** → **Trading System**
2. Different modes (Backtesting, Historical Backtesting, Automation) use the same building blocks
3. Separate lists for testing, automation, and historical backtesting
4. The scoring system creates "profiles" for each mode

## Architecture Components

### 1. Unified Stock Scorer (`src/machine_learning/stock_scorer.py`)

The `UnifiedStockScorer` class provides the core scoring functionality with three distinct modes:

#### Scoring Modes
- **BACKTESTING**: Single stock scoring for specific symbol backtesting
- **HISTORICAL**: Multi-stock scoring using all available stocks from data sources
- **AUTOMATION**: Watchlist-based scoring for real-time automation

#### Key Features
- Separate scoring lists for each mode
- Strategy+profile integration
- Caching system with mode-specific caches
- Trading signal generation
- Confidence scoring

### 2. Enhanced Trading System (`src/trading_system.py`)

The trading system now integrates with the unified scoring system:

#### New Methods
- `create_scoring_list()`: Create scoring lists for different modes
- `get_scoring_list()`: Retrieve current scoring lists
- `generate_trading_signals()`: Generate trading signals from scoring lists
- `set_strategy_profile()`: Set strategy profiles dynamically

#### Profile Management
- Support for multiple profiles: balanced, canonical, aggressive, conservative
- Dynamic profile switching
- Profile-specific configuration management

### 3. Updated Backtesting Engine (`src/backtesting/backtest_engine.py`)

The backtesting engine now supports:

#### Single Stock Backtesting
- Strategy+profile selection
- Unified scoring integration
- Comprehensive performance metrics

#### Historical Backtesting
- Multi-stock simulation
- Strategy+profile across all selected stocks
- Portfolio-level performance analysis

### 4. GUI Integration

#### Backtesting Tab
- Strategy dropdown (MACD)
- Profile dropdown (balanced, canonical, aggressive, conservative)
- Dynamic strategy descriptions based on profile selection

#### Historical Backtesting Tab
- Strategy+profile selection
- Period and benchmark selection
- Enhanced results display

## Data Flow

### Backtesting Flow
```
User selects: Strategy (MACD) + Profile (balanced) + Symbol (AAPL)
    ↓
UnifiedScorer.create_scoring_list(mode=BACKTESTING, symbol=AAPL)
    ↓
TradingSystem generates signals
    ↓
BacktestEngine runs simulation
    ↓
Results with strategy+profile metadata
```

### Historical Backtesting Flow
```
User selects: Strategy (MACD) + Profile (canonical) + Period (1y)
    ↓
UnifiedScorer.create_scoring_list(mode=HISTORICAL, max_stocks=20)
    ↓
TradingSystem selects top stocks from scoring list
    ↓
BacktestEngine runs multi-stock simulation
    ↓
Portfolio-level results with strategy+profile metadata
```

### Automation Flow
```
System uses: Strategy (MACD) + Profile (aggressive)
    ↓
UnifiedScorer.create_scoring_list(mode=AUTOMATION, max_stocks=10)
    ↓
TradingSystem generates signals for top stocks
    ↓
AutomationEngine executes trades
    ↓
Real-time position management
```

## Configuration

### Strategy Profiles (config/settings.yaml)
```yaml
strategies:
  MACD:
    profiles:
      balanced:
        entry_threshold: 0.3
        take_profit_pct: 5.0
        stop_loss_pct: 3.0
      canonical:
        entry_threshold: 0.4
        take_profit_pct: 5.0
        stop_loss_pct: 3.0
      aggressive:
        entry_threshold: 0.2
        take_profit_pct: 3.0
        stop_loss_pct: 2.0
      conservative:
        entry_threshold: 0.6
        take_profit_pct: 10.0
        stop_loss_pct: 5.0
```

## Benefits

### 1. Consistency
- Same building blocks for all modes
- Unified interface for strategy+profile selection
- Consistent scoring methodology

### 2. Flexibility
- Easy to add new strategies
- Easy to add new profiles
- Easy to modify scoring algorithms

### 3. Separation of Concerns
- Scoring system focuses on stock selection and signal generation
- Trading system focuses on trade execution
- Backtesting system focuses on simulation and performance analysis

### 4. Scalability
- Separate lists prevent interference between modes
- Caching system improves performance
- Modular design allows easy extension

## Usage Examples

### Backtesting a Single Stock
```python
from src.backtesting.backtest_engine import BacktestEngine

engine = BacktestEngine()
results = engine.run_backtest(
    symbol="AAPL",
    strategy="MACD",
    profile="balanced",
    start_date="2023-01-01",
    end_date="2023-12-31"
)
```

### Historical Backtesting
```python
results = engine.run_historical_backtest(
    strategy="MACD",
    profile="canonical",
    start_date="2023-01-01",
    end_date="2023-12-31",
    benchmark="SPY"
)
```

### Creating Scoring Lists
```python
from src.machine_learning.stock_scorer import UnifiedStockScorer, ScoringMode

scorer = UnifiedStockScorer()

# Backtesting mode
backtest_scores = scorer.create_scoring_list(
    mode=ScoringMode.BACKTESTING,
    strategy="MACD",
    profile="balanced",
    symbol="AAPL"
)

# Historical mode
historical_scores = scorer.create_scoring_list(
    mode=ScoringMode.HISTORICAL,
    strategy="MACD",
    profile="canonical",
    max_stocks=20
)

# Automation mode
automation_scores = scorer.create_scoring_list(
    mode=ScoringMode.AUTOMATION,
    strategy="MACD",
    profile="aggressive",
    max_stocks=10
)
```

## Testing

Run the unified architecture test:
```bash
python test_unified_architecture.py
```

This will test:
1. Unified scoring system with different modes
2. Trading system integration
3. Backtesting engine functionality
4. Profile configurations

## Migration from Old System

The new architecture is backward compatible but provides enhanced functionality:

1. **Old**: Strategy-only selection
   **New**: Strategy+profile selection

2. **Old**: Single scoring list
   **New**: Separate lists for different modes

3. **Old**: Direct strategy execution
   **New**: Scoring → Signal Generation → Trading

4. **Old**: Fixed configuration
   **New**: Dynamic profile-based configuration

## Future Enhancements

1. **Additional Strategies**: Easy to add new strategies (RSI, Bollinger Bands, etc.)
2. **Machine Learning**: Enhanced scoring with ML models
3. **Real-time Optimization**: Dynamic profile adjustment based on market conditions
4. **Multi-timeframe**: Support for different timeframes in scoring
5. **Risk Management**: Enhanced risk controls per profile

## Conclusion

The unified architecture successfully addresses the user's requirements by:

✅ **Strategy+Profile Selection**: Users can now select both strategy and profile in the GUI
✅ **Separate Lists**: Different modes have separate scoring lists
✅ **Unified Building Blocks**: Same components work for backtesting, historical, and automation
✅ **Consistent Interface**: All modes use the same strategy+profile approach
✅ **Enhanced Flexibility**: Easy to modify and extend the system

The architecture provides a solid foundation for future enhancements while maintaining simplicity and consistency across all trading modes. 