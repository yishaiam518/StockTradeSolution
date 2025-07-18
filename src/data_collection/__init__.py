"""
Data Collection Module for the SMART STOCK TRADING SYSTEM.

This module handles:
- Bulk historical data collection
- Scheduled daily updates
- Real-time position monitoring
- Multiple data source management
"""

from .collector import DataCollector
from .scheduler import DataScheduler
from .sources import DataSource

__all__ = ['DataCollector', 'DataScheduler', 'DataSource'] 