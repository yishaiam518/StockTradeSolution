"""
Web Dashboard Module

This module provides a web-based dashboard for the trading system including:
- Real-time portfolio monitoring
- Interactive charts and visualizations
- Performance metrics display
- Trade history and analysis
- Strategy management interface
"""

from .dashboard_app import DashboardApp
from .chart_generator import ChartGenerator

__all__ = [
    'DashboardApp',
    'ChartGenerator'
]