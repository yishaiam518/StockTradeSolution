#!/usr/bin/env python3
"""
AI Backtesting Engine
Core engine for testing multiple strategies and combinations on historical data.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StrategyType(Enum):
    """Available trading strategies for backtesting."""
    MACD = "macd"
    RSI = "rsi"
    BOLLINGER_BANDS = "bollinger_bands"
    MOVING_AVERAGE = "moving_average"
    VOLUME_WEIGHTED = "volume_weighted"
    MOMENTUM = "momentum"


class RiskLevel(Enum):
    """Risk tolerance levels."""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


@dataclass
class BacktestParameters:
    """Parameters for backtesting configuration."""
    available_cash: float = 1_000_000.0  # $1M default
    transaction_limit_pct: float = 0.02   # 2% default
    stop_loss_pct: float = 0.05          # 5% default
    stop_gain_pct: float = 0.20          # 20% default
    safe_net: float = 10_000.0           # $10K default
    risk_tolerance: RiskLevel = RiskLevel.MODERATE
    recommendation_threshold: float = 0.20  # 20% default


@dataclass
class StrategyResult:
    """Results from a single strategy backtest."""
    strategy_name: str
    strategy_combination: List[str]
    total_return: float
    total_return_pct: float
    sharpe_ratio: float
    max_drawdown: float
    max_drawdown_pct: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    risk_score: float
    final_portfolio_value: float
    execution_time: float


@dataclass
class BacktestSummary:
    """Summary of all backtesting results."""
    total_strategies_tested: int
    best_strategy: StrategyResult
    worst_strategy: StrategyResult
    average_return: float
    average_sharpe: float
    recommendations: List[str]
    execution_timestamp: datetime
    total_execution_time: float


class AIBacktestingEngine:
    """
    Core engine for AI strategy backtesting.
    Tests individual strategies and combinations on historical data.
    """
    
    def __init__(self, data_manager=None):
        """Initialize the backtesting engine."""
        self.data_manager = data_manager
        self.parameters = BacktestParameters()
        self.results: List[StrategyResult] = []
        self.summary: Optional[BacktestSummary] = None
        
    def set_parameters(self, parameters: BacktestParameters):
        """Set backtesting parameters."""
        self.parameters = parameters
        logger.info(f"Backtesting parameters updated: {parameters}")
        
    def get_available_strategies(self) -> List[StrategyType]:
        """Get list of available strategies."""
        return list(StrategyType)
    
    def generate_strategy_combinations(self, max_combinations: int = 3) -> List[List[str]]:
        """
        Generate strategy combinations for testing.
        Excludes nonsensical combinations.
        """
        strategies = [s.value for s in StrategyType]
        combinations = []
        
        # Individual strategies
        combinations.extend([[s] for s in strategies])
        
        # 2-strategy combinations
        for i in range(len(strategies)):
            for j in range(i + 1, len(strategies)):
                combinations.append([strategies[i], strategies[j]])
        
        # 3+ strategy combinations (up to max_combinations)
        if max_combinations >= 3:
            for i in range(len(strategies)):
                for j in range(i + 1, len(strategies)):
                    for k in range(j + 1, len(strategies)):
                        combinations.append([strategies[i], strategies[j], strategies[k]])
        
        # Filter out nonsensical combinations
        filtered_combinations = self._filter_strategy_combinations(combinations)
        
        logger.info(f"Generated {len(filtered_combinations)} strategy combinations")
        return filtered_combinations
    
    def _filter_strategy_combinations(self, combinations: List[List[str]]) -> List[List[str]]:
        """Filter out nonsensical strategy combinations."""
        filtered = []
        
        for combo in combinations:
            # Skip if combination is too long
            if len(combo) > 4:
                continue
                
            # Skip if all strategies are the same
            if len(set(combo)) == 1:
                continue
                
            # Skip conflicting combinations (e.g., multiple trend indicators)
            if self._has_conflicting_strategies(combo):
                continue
                
            filtered.append(combo)
        
        return filtered
    
    def _has_conflicting_strategies(self, combo: List[str]) -> bool:
        """Check if strategy combination has conflicts."""
        # Multiple trend indicators might conflict
        trend_indicators = ['macd', 'moving_average', 'momentum']
        trend_count = sum(1 for s in combo if s in trend_indicators)
        
        # Multiple volatility indicators might conflict
        volatility_indicators = ['bollinger_bands', 'rsi']
        volatility_count = sum(1 for s in combo if s in volatility_indicators)
        
        # Too many trend indicators
        if trend_count > 2:
            return True
            
        # Too many volatility indicators
        if volatility_count > 2:
            return True
            
        return False
    
    def run_backtest(self, historical_data: pd.DataFrame, 
                    strategy_combinations: Optional[List[List[str]]] = None) -> BacktestSummary:
        """
        Run comprehensive backtesting on historical data.
        
        Args:
            historical_data: DataFrame with OHLCV data and indicators
            strategy_combinations: List of strategy combinations to test
            
        Returns:
            BacktestSummary with results and recommendations
        """
        start_time = datetime.now()
        logger.info("Starting AI backtesting...")
        
        if strategy_combinations is None:
            strategy_combinations = self.generate_strategy_combinations()
        
        self.results = []
        
        for combo in strategy_combinations:
            try:
                result = self._test_strategy_combination(historical_data, combo)
                self.results.append(result)
                logger.info(f"Strategy {combo} completed: {result.total_return_pct:.2f}% return")
            except Exception as e:
                logger.error(f"Error testing strategy {combo}: {e}")
                continue
        
        # Generate summary and recommendations
        self.summary = self._generate_summary(start_time)
        
        logger.info(f"Backtesting completed. Tested {len(self.results)} strategies.")
        return self.summary
    
    def _test_strategy_combination(self, data: pd.DataFrame, 
                                 strategy_combo: List[str]) -> StrategyResult:
        """Test a single strategy combination."""
        start_time = datetime.now()
        
        # Simulate trading based on strategy combination
        portfolio_value = self.parameters.available_cash
        positions = {}
        trades = []
        
        # Simple strategy simulation (placeholder for actual strategy logic)
        for i in range(len(data)):
            if i < 50:  # Skip first 50 periods for indicator calculation
                continue
                
            # Generate signals based on strategy combination
            signal = self._generate_signal(data.iloc[i], strategy_combo, data.iloc[:i+1])
            
            if signal == 'buy' and portfolio_value > self.parameters.safe_net:
                # Calculate position size based on transaction limit
                max_position_value = portfolio_value * self.parameters.transaction_limit_pct
                current_price = data.iloc[i]['close']
                shares = int(max_position_value / current_price)
                
                if shares > 0:
                    cost = shares * current_price
                    portfolio_value -= cost
                    positions[data.iloc[i]['symbol']] = {
                        'shares': shares,
                        'entry_price': current_price,
                        'entry_date': data.iloc[i]['date']
                    }
                    trades.append({
                        'type': 'buy',
                        'symbol': data.iloc[i]['symbol'],
                        'shares': shares,
                        'price': current_price,
                        'date': data.iloc[i]['date']
                    })
                    
            elif signal == 'sell' and data.iloc[i]['symbol'] in positions:
                position = positions[data.iloc[i]['symbol']]
                current_price = data.iloc[i]['close']
                proceeds = position['shares'] * current_price
                portfolio_value += proceeds
                
                # Calculate P&L
                pnl = proceeds - (position['shares'] * position['entry_price'])
                
                trades.append({
                    'type': 'sell',
                    'symbol': data.iloc[i]['symbol'],
                    'shares': position['shares'],
                    'price': current_price,
                    'date': data.iloc[i]['date'],
                    'pnl': pnl
                })
                
                del positions[data.iloc[i]['symbol']]
        
        # Close remaining positions at end
        final_portfolio_value = portfolio_value
        for symbol, position in positions.items():
            final_price = data.iloc[-1]['close']
            final_portfolio_value += position['shares'] * final_price
        
        # Calculate metrics
        total_return = final_portfolio_value - self.parameters.available_cash
        total_return_pct = (total_return / self.parameters.available_cash) * 100
        
        # Calculate Sharpe ratio (simplified)
        returns = self._calculate_returns(data, trades)
        sharpe_ratio = self._calculate_sharpe_ratio(returns) if len(returns) > 1 else 0
        
        # Calculate max drawdown
        max_drawdown, max_drawdown_pct = self._calculate_max_drawdown(data, trades)
        
        # Calculate win rate
        winning_trades = len([t for t in trades if t.get('pnl', 0) > 0])
        total_trades = len([t for t in trades if t['type'] == 'sell'])
        win_rate = (winning_trades / total_trades) if total_trades > 0 else 0
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(sharpe_ratio, max_drawdown_pct, win_rate)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return StrategyResult(
            strategy_name=" + ".join(strategy_combo),
            strategy_combination=strategy_combo,
            total_return=total_return,
            total_return_pct=total_return_pct,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            max_drawdown_pct=max_drawdown_pct,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=total_trades - winning_trades,
            win_rate=win_rate,
            risk_score=risk_score,
            final_portfolio_value=final_portfolio_value,
            execution_time=execution_time
        )
    
    def _generate_signal(self, current_data: pd.Series, 
                        strategies: List[str], 
                        historical_data: pd.DataFrame) -> str:
        """Generate buy/sell signal based on strategy combination."""
        # Placeholder for actual strategy logic
        # In real implementation, this would use actual technical indicators
        
        # Simple random signal for demonstration
        import random
        return random.choice(['buy', 'sell', 'hold'])
    
    def _calculate_returns(self, data: pd.DataFrame, trades: List[Dict]) -> List[float]:
        """Calculate returns from trades."""
        # Placeholder for return calculation
        return [0.01, -0.02, 0.03, -0.01, 0.02]  # Sample returns
    
    def _calculate_sharpe_ratio(self, returns: List[float], risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio."""
        if not returns:
            return 0.0
        
        returns_array = np.array(returns)
        excess_returns = returns_array - (risk_free_rate / 252)  # Daily risk-free rate
        
        if len(excess_returns) < 2:
            return 0.0
        
        return np.mean(excess_returns) / np.std(excess_returns) if np.std(excess_returns) > 0 else 0
    
    def _calculate_max_drawdown(self, data: pd.DataFrame, trades: List[Dict]) -> Tuple[float, float]:
        """Calculate maximum drawdown."""
        # Placeholder for drawdown calculation
        return 50000.0, 5.0  # $50K, 5%
    
    def _calculate_risk_score(self, sharpe_ratio: float, 
                             max_drawdown_pct: float, 
                             win_rate: float) -> float:
        """Calculate composite risk score (0-100, lower is better)."""
        # Normalize components
        sharpe_score = max(0, min(100, (sharpe_ratio + 2) * 25))  # -2 to 2 range
        drawdown_score = max(0, min(100, max_drawdown_pct * 2))    # 0 to 50% range
        win_rate_score = max(0, min(100, (1 - win_rate) * 100))   # Invert win rate
        
        # Weighted average
        risk_score = (sharpe_score * 0.4 + drawdown_score * 0.4 + win_rate_score * 0.2)
        return risk_score
    
    def _generate_summary(self, start_time: datetime) -> BacktestSummary:
        """Generate comprehensive summary of backtesting results."""
        if not self.results:
            raise ValueError("No results to summarize")
        
        # Sort by total return
        sorted_results = sorted(self.results, key=lambda x: x.total_return, reverse=True)
        
        best_strategy = sorted_results[0]
        worst_strategy = sorted_results[-1]
        
        # Calculate averages
        avg_return = np.mean([r.total_return_pct for r in self.results])
        avg_sharpe = np.mean([r.sharpe_ratio for r in self.results])
        
        # Generate recommendations
        recommendations = self._generate_recommendations(best_strategy, avg_return)
        
        total_execution_time = (datetime.now() - start_time).total_seconds()
        
        return BacktestSummary(
            total_strategies_tested=len(self.results),
            best_strategy=best_strategy,
            worst_strategy=worst_strategy,
            average_return=avg_return,
            average_sharpe=avg_sharpe,
            recommendations=recommendations,
            execution_timestamp=datetime.now(),
            total_execution_time=total_execution_time
        )
    
    def _generate_recommendations(self, best_strategy: StrategyResult, 
                                avg_return: float) -> List[str]:
        """Generate actionable recommendations based on results."""
        recommendations = []
        
        # Check if best strategy significantly outperforms average
        if best_strategy.total_return_pct > avg_return * (1 + self.parameters.recommendation_threshold):
            recommendations.append(
                f"Consider switching to {best_strategy.strategy_name} strategy "
                f"(outperformed average by {best_strategy.total_return_pct - avg_return:.2f}%)"
            )
        
        # Risk-based recommendations
        if best_strategy.risk_score > 70:
            recommendations.append(
                f"Warning: {best_strategy.strategy_name} has high risk score "
                f"({best_strategy.risk_score:.1f}). Consider risk management adjustments."
            )
        
        # Performance recommendations
        if best_strategy.sharpe_ratio > 1.5:
            recommendations.append(
                f"Excellent risk-adjusted returns with {best_strategy.strategy_name} "
                f"(Sharpe ratio: {best_strategy.sharpe_ratio:.2f})"
            )
        
        # Win rate recommendations
        if best_strategy.win_rate < 0.4:
            recommendations.append(
                f"Low win rate with {best_strategy.strategy_name} "
                f"({best_strategy.win_rate:.1%}). Consider entry/exit optimization."
            )
        
        if not recommendations:
            recommendations.append("No significant changes recommended at this time.")
        
        return recommendations
    
    def reset_results(self):
        """Reset all backtesting results."""
        self.results = []
        self.summary = None
        logger.info("Backtesting results reset")
    
    def get_results(self) -> List[StrategyResult]:
        """Get all backtesting results."""
        return self.results
    
    def get_summary(self) -> Optional[BacktestSummary]:
        """Get backtesting summary."""
        return self.summary
    
    def export_results(self, filename: str = None) -> str:
        """Export results to CSV file."""
        if not self.results:
            raise ValueError("No results to export")
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ai_backtest_results_{timestamp}.csv"
        
        # Convert results to DataFrame
        data = []
        for result in self.results:
            data.append({
                'Strategy': result.strategy_name,
                'Total Return ($)': result.total_return,
                'Total Return (%)': result.total_return_pct,
                'Sharpe Ratio': result.sharpe_ratio,
                'Max Drawdown ($)': result.max_drawdown,
                'Max Drawdown (%)': result.max_drawdown_pct,
                'Total Trades': result.total_trades,
                'Win Rate': result.win_rate,
                'Risk Score': result.risk_score,
                'Final Portfolio Value': result.final_portfolio_value,
                'Execution Time (s)': result.execution_time
            })
        
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        logger.info(f"Results exported to {filename}")
        return filename
