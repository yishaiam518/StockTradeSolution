"""
Data Sources for the SMART STOCK TRADING SYSTEM.

Handles:
- Multiple data providers (Yahoo Finance, Alpha Vantage, etc.)
- Data source abstraction
- Provider-specific implementations
"""

import pandas as pd
import yfinance as yf
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
import logging

from src.utils.logger import logger


class DataSource(ABC):
    """Abstract base class for data sources."""
    
    @abstractmethod
    def fetch_historical_data(self, symbol: str, start_date, end_date) -> Optional[pd.DataFrame]:
        """Fetch historical data for a symbol."""
        pass
    
    @abstractmethod
    def fetch_realtime_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Fetch real-time data for a symbol."""
        pass
    
    @abstractmethod
    def get_source_name(self) -> str:
        """Get the name of this data source."""
        pass


class YahooFinanceSource(DataSource):
    """Yahoo Finance data source implementation."""
    
    def __init__(self):
        self.name = "Yahoo Finance"
        logger.info(f"Initialized {self.name} data source")
    
    def fetch_historical_data(self, symbol: str, start_date, end_date) -> Optional[pd.DataFrame]:
        """Fetch historical data from Yahoo Finance."""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date)
            
            if data.empty:
                logger.warning(f"No historical data available for {symbol}")
                return None
            
            # Standardize column names
            data.columns = [col.lower() for col in data.columns]
            
            # Add metadata
            data['symbol'] = symbol
            data['source'] = self.name
            
            logger.debug(f"Fetched {len(data)} historical data points for {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol} from {self.name}: {str(e)}")
            return None
    
    def fetch_realtime_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Fetch real-time data from Yahoo Finance."""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d", interval="1m")
            
            if data.empty:
                logger.warning(f"No real-time data available for {symbol}")
                return None
            
            # Standardize column names
            data.columns = [col.lower() for col in data.columns]
            
            # Add metadata
            data['symbol'] = symbol
            data['source'] = self.name
            
            logger.debug(f"Fetched {len(data)} real-time data points for {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching real-time data for {symbol} from {self.name}: {str(e)}")
            return None
    
    def get_source_name(self) -> str:
        """Get the name of this data source."""
        return self.name


class DataSourceManager:
    """Manager for multiple data sources."""
    
    def __init__(self):
        self.sources: Dict[str, DataSource] = {}
        self.default_source = None
        
        # Initialize default sources
        self._initialize_default_sources()
        
        logger.info("Data Source Manager initialized")
    
    def _initialize_default_sources(self):
        """Initialize default data sources."""
        # Add Yahoo Finance as default source
        yahoo_source = YahooFinanceSource()
        self.add_source('yahoo', yahoo_source)
        self.default_source = yahoo_source
        
        logger.info("Default data sources initialized")
    
    def add_source(self, name: str, source: DataSource):
        """Add a data source."""
        self.sources[name] = source
        logger.info(f"Added data source: {name} ({source.get_source_name()})")
    
    def get_source(self, name: str) -> Optional[DataSource]:
        """Get a data source by name."""
        return self.sources.get(name)
    
    def get_default_source(self) -> DataSource:
        """Get the default data source."""
        return self.default_source
    
    def fetch_historical_data(self, symbol: str, start_date, end_date, source_name: str = None) -> Optional[pd.DataFrame]:
        """Fetch historical data using the specified or default source."""
        source = self.get_source(source_name) if source_name else self.get_default_source()
        
        if source is None:
            logger.error(f"No data source available for {symbol}")
            return None
        
        return source.fetch_historical_data(symbol, start_date, end_date)
    
    def fetch_realtime_data(self, symbol: str, source_name: str = None) -> Optional[pd.DataFrame]:
        """Fetch real-time data using the specified or default source."""
        source = self.get_source(source_name) if source_name else self.get_default_source()
        
        if source is None:
            logger.error(f"No data source available for {symbol}")
            return None
        
        return source.fetch_realtime_data(symbol)
    
    def get_available_sources(self) -> List[str]:
        """Get list of available data source names."""
        return list(self.sources.keys())
    
    def get_source_info(self) -> Dict[str, Any]:
        """Get information about all data sources."""
        info = {}
        for name, source in self.sources.items():
            info[name] = {
                'name': source.get_source_name(),
                'type': type(source).__name__
            }
        return info 