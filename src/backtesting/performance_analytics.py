"""
Advanced Performance Analytics for Backtesting
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
import logging
from dataclasses import dataclass
from datetime import datetime

@dataclass
class PerformanceMetrics:
    """Container for all performance metrics"""
    # Basic metrics
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    
    # Advanced risk-adjusted metrics
    sortino_ratio: float
    calmar_ratio: float
    information_ratio: float
    omega_ratio: float
    treynor_ratio: float
    
    # Risk metrics
    max_drawdown: float
    max_drawdown_duration: int
    var_95: float
    cvar_95: float
    downside_deviation: float
    
    # Trade metrics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    profit_factor: float
    average_win: float
    average_loss: float
    largest_win: float
    largest_loss: float
    
    # Additional metrics
    avg_trade_duration: float
    best_month: float
    worst_month: float
    positive_months: int
    negative_months: int

class PerformanceAnalytics:
    """Advanced performance analytics for backtesting results"""
    
    def __init__(self, risk_free_rate: float = 0.02):
        self.risk_free_rate = risk_free_rate
        self.logger = logging.getLogger(__name__)
    
    def calculate_performance_metrics(self, 
                                   equity_curve: pd.Series,
                                   trades: List[Dict],
                                   benchmark_returns: Optional[pd.Series] = None) -> PerformanceMetrics:
        """
        Calculate comprehensive performance metrics
        
        Args:
            equity_curve: Series of portfolio values over time
            trades: List of trade dictionaries
            benchmark_returns: Optional benchmark returns for comparison
            
        Returns:
            PerformanceMetrics object with all calculated metrics
        """
        try:
            # Calculate returns
            returns = equity_curve.pct_change().dropna()
            
            # Basic metrics
            total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1
            annualized_return = self._calculate_annualized_return(returns)
            volatility = returns.std() * np.sqrt(252)  # Annualized volatility
            sharpe_ratio = self._calculate_sharpe_ratio(returns)
            
            # Advanced risk-adjusted metrics
            sortino_ratio = self._calculate_sortino_ratio(returns)
            calmar_ratio = self._calculate_calmar_ratio(returns, total_return)
            information_ratio = self._calculate_information_ratio(returns, benchmark_returns)
            omega_ratio = self._calculate_omega_ratio(returns)
            treynor_ratio = self._calculate_treynor_ratio(returns, total_return)
            
            # Risk metrics
            max_drawdown, max_drawdown_duration = self._calculate_max_drawdown(equity_curve)
            var_95, cvar_95 = self._calculate_var_cvar(returns)
            downside_deviation = self._calculate_downside_deviation(returns)
            
            # Trade metrics
            trade_metrics = self._calculate_trade_metrics(trades)
            
            # Additional metrics
            monthly_metrics = self._calculate_monthly_metrics(returns)
            
            return PerformanceMetrics(
                total_return=total_return,
                annualized_return=annualized_return,
                volatility=volatility,
                sharpe_ratio=sharpe_ratio,
                sortino_ratio=sortino_ratio,
                calmar_ratio=calmar_ratio,
                information_ratio=information_ratio,
                omega_ratio=omega_ratio,
                treynor_ratio=treynor_ratio,
                max_drawdown=max_drawdown,
                max_drawdown_duration=max_drawdown_duration,
                var_95=var_95,
                cvar_95=cvar_95,
                downside_deviation=downside_deviation,
                **trade_metrics,
                **monthly_metrics
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating performance metrics: {e}")
            raise
    
    def _calculate_annualized_return(self, returns: pd.Series) -> float:
        """Calculate annualized return"""
        total_days = len(returns)
        total_return = (1 + returns).prod() - 1
        return (1 + total_return) ** (252 / total_days) - 1
    
    def _calculate_sharpe_ratio(self, returns: pd.Series) -> float:
        """Calculate Sharpe ratio"""
        excess_returns = returns - self.risk_free_rate / 252
        if returns.std() == 0:
            return 0
        return (excess_returns.mean() / returns.std()) * np.sqrt(252)
    
    def _calculate_sortino_ratio(self, returns: pd.Series) -> float:
        """Calculate Sortino ratio using downside deviation"""
        excess_returns = returns - self.risk_free_rate / 252
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0
        downside_deviation = downside_returns.std()
        return (excess_returns.mean() / downside_deviation) * np.sqrt(252)
    
    def _calculate_calmar_ratio(self, returns: pd.Series, total_return: float) -> float:
        """Calculate Calmar ratio (return / max drawdown)"""
        max_dd, _ = self._calculate_max_drawdown((1 + returns).cumprod())
        if max_dd == 0:
            return 0
        return total_return / abs(max_dd)
    
    def _calculate_information_ratio(self, returns: pd.Series, 
                                   benchmark_returns: Optional[pd.Series]) -> float:
        """Calculate Information ratio"""
        if benchmark_returns is None:
            return 0
        
        # Align returns and benchmark
        aligned_data = pd.concat([returns, benchmark_returns], axis=1).dropna()
        if len(aligned_data) == 0:
            return 0
        
        excess_returns = aligned_data.iloc[:, 0] - aligned_data.iloc[:, 1]
        tracking_error = excess_returns.std()
        
        if tracking_error == 0:
            return 0
        
        return (excess_returns.mean() / tracking_error) * np.sqrt(252)
    
    def _calculate_omega_ratio(self, returns: pd.Series, threshold: float = 0) -> float:
        """Calculate Omega ratio"""
        positive_returns = returns[returns > threshold]
        negative_returns = returns[returns <= threshold]
        
        if len(negative_returns) == 0:
            return float('inf')
        
        expected_gain = positive_returns.mean() if len(positive_returns) > 0 else 0
        expected_loss = abs(negative_returns.mean())
        
        if expected_loss == 0:
            return 0
        
        return expected_gain / expected_loss
    
    def _calculate_treynor_ratio(self, returns: pd.Series, total_return: float) -> float:
        """Calculate Treynor ratio (assuming market beta = 1 for simplicity)"""
        # For simplicity, we'll use correlation with a simple market proxy
        # In practice, you'd calculate actual beta from market data
        beta = 1.0  # Placeholder - should calculate actual beta
        if beta == 0:
            return 0
        return (total_return - self.risk_free_rate) / beta
    
    def _calculate_max_drawdown(self, equity_curve: pd.Series) -> Tuple[float, int]:
        """Calculate maximum drawdown and its duration"""
        peak = equity_curve.expanding().max()
        drawdown = (equity_curve - peak) / peak
        
        max_dd = drawdown.min()
        max_dd_idx = drawdown.idxmin()
        
        # Find duration of max drawdown
        recovery_idx = equity_curve[max_dd_idx:].idxmax()
        if recovery_idx <= max_dd_idx:
            duration = len(equity_curve) - equity_curve.index.get_loc(max_dd_idx)
        else:
            duration = equity_curve.index.get_loc(recovery_idx) - equity_curve.index.get_loc(max_dd_idx)
        
        return max_dd, duration
    
    def _calculate_var_cvar(self, returns: pd.Series, confidence: float = 0.95) -> Tuple[float, float]:
        """Calculate Value at Risk and Conditional Value at Risk"""
        var = np.percentile(returns, (1 - confidence) * 100)
        cvar = returns[returns <= var].mean()
        return var, cvar
    
    def _calculate_downside_deviation(self, returns: pd.Series) -> float:
        """Calculate downside deviation"""
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0:
            return 0
        return downside_returns.std()
    
    def _calculate_trade_metrics(self, trades: List[Any]) -> Dict[str, Any]:
        """Calculate trade-specific metrics"""
        if not trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'average_win': 0.0,
                'average_loss': 0.0,
                'largest_win': 0.0,
                'largest_loss': 0.0,
                'avg_trade_duration': 0.0
            }
        
        # Extract trade P&L values - handle both Trade objects and dictionaries
        trade_pnls = []
        trade_times = []
        
        for trade in trades:
            if hasattr(trade, 'pnl'):  # Trade object
                trade_pnls.append(trade.pnl)
                trade_times.append((trade.entry_time, trade.exit_time))
            elif isinstance(trade, dict):  # Dictionary
                trade_pnls.append(trade.get('pnl', 0))
                trade_times.append((trade.get('entry_time'), trade.get('exit_time')))
            else:  # Other object types
                trade_pnls.append(getattr(trade, 'pnl', 0))
                trade_times.append((getattr(trade, 'entry_time', None), getattr(trade, 'exit_time', None)))
        
        winning_trades = [pnl for pnl in trade_pnls if pnl > 0]
        losing_trades = [pnl for pnl in trade_pnls if pnl < 0]
        
        total_trades = len(trades)
        winning_count = len(winning_trades)
        losing_count = len(losing_trades)
        
        win_rate = winning_count / total_trades if total_trades > 0 else 0
        
        # Profit factor
        gross_profit = sum(winning_trades) if winning_trades else 0
        gross_loss = abs(sum(losing_trades)) if losing_trades else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Average wins/losses
        average_win = np.mean(winning_trades) if winning_trades else 0
        average_loss = np.mean(losing_trades) if losing_trades else 0
        
        # Largest wins/losses
        largest_win = max(trade_pnls) if trade_pnls else 0
        largest_loss = min(trade_pnls) if trade_pnls else 0
        
        # Average trade duration
        durations = []
        for entry_time, exit_time in trade_times:
            if entry_time and exit_time:
                if isinstance(entry_time, str):
                    entry_time = pd.to_datetime(entry_time)
                if isinstance(exit_time, str):
                    exit_time = pd.to_datetime(exit_time)
                duration = (exit_time - entry_time).total_seconds() / 3600  # hours
                durations.append(duration)
        
        avg_trade_duration = np.mean(durations) if durations else 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_count,
            'losing_trades': losing_count,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'average_win': average_win,
            'average_loss': average_loss,
            'largest_win': largest_win,
            'largest_loss': largest_loss,
            'avg_trade_duration': avg_trade_duration
        }
    
    def _calculate_monthly_metrics(self, returns: pd.Series) -> Dict[str, Any]:
        """Calculate monthly performance metrics"""
        # Resample to monthly returns
        monthly_returns = returns.resample('M').apply(lambda x: (1 + x).prod() - 1)
        
        if len(monthly_returns) == 0:
            return {
                'best_month': 0.0,
                'worst_month': 0.0,
                'positive_months': 0,
                'negative_months': 0
            }
        
        best_month = monthly_returns.max()
        worst_month = monthly_returns.min()
        positive_months = (monthly_returns > 0).sum()
        negative_months = (monthly_returns < 0).sum()
        
        return {
            'best_month': best_month,
            'worst_month': worst_month,
            'positive_months': positive_months,
            'negative_months': negative_months
        }
    
    def generate_performance_report(self, metrics: PerformanceMetrics) -> str:
        """Generate a comprehensive performance report"""
        report = f"""
PERFORMANCE ANALYTICS REPORT
{'=' * 50}

RETURN METRICS:
Total Return: {metrics.total_return:.2%}
Annualized Return: {metrics.annualized_return:.2%}
Volatility: {metrics.volatility:.2%}

RISK-ADJUSTED METRICS:
Sharpe Ratio: {metrics.sharpe_ratio:.2f}
Sortino Ratio: {metrics.sortino_ratio:.2f}
Calmar Ratio: {metrics.calmar_ratio:.2f}
Information Ratio: {metrics.information_ratio:.2f}
Omega Ratio: {metrics.omega_ratio:.2f}
Treynor Ratio: {metrics.treynor_ratio:.2f}

RISK METRICS:
Maximum Drawdown: {metrics.max_drawdown:.2%}
Max Drawdown Duration: {metrics.max_drawdown_duration} periods
Value at Risk (95%): {metrics.var_95:.2%}
Conditional VaR (95%): {metrics.cvar_95:.2%}
Downside Deviation: {metrics.downside_deviation:.2%}

TRADE METRICS:
Total Trades: {metrics.total_trades}
Winning Trades: {metrics.winning_trades}
Losing Trades: {metrics.losing_trades}
Win Rate: {metrics.win_rate:.2%}
Profit Factor: {metrics.profit_factor:.2f}
Average Win: ${metrics.average_win:.2f}
Average Loss: ${metrics.average_loss:.2f}
Largest Win: ${metrics.largest_win:.2f}
Largest Loss: ${metrics.largest_loss:.2f}
Average Trade Duration: {metrics.avg_trade_duration:.1f} hours

MONTHLY METRICS:
Best Month: {metrics.best_month:.2%}
Worst Month: {metrics.worst_month:.2%}
Positive Months: {metrics.positive_months}
Negative Months: {metrics.negative_months}
"""
        return report 