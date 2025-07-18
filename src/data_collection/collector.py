"""
Data Collector for the SMART STOCK TRADING SYSTEM.

Handles:
- Initial bulk data collection (5 years historical)
- Daily scheduled updates
- Real-time updates for active positions
- Multiple data source management
- Caching and optimization
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
from pathlib import Path
import json
import time

from src.utils.logger import logger
from src.utils.config_loader import ConfigLoader


class DataCollector:
    """Main data collection engine."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the data collector."""
        if config is None:
            config_loader = ConfigLoader()
            config = config_loader.config
        
        self.config = config
        self.data_collection_config = self.config.get('data_collection', {})
        
        # Initialize data storage
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Cache for real-time data
        self.realtime_cache = {}
        self.cache_timestamps = {}
        
        # Data sources
        self.sources = self._initialize_sources()
        
        logger.info("Data Collector initialized")
    
    def _initialize_sources(self) -> Dict[str, List[str]]:
        """Initialize data sources from configuration."""
        sources_config = self.data_collection_config.get('sources', [])
        sources = {}
        
        for source in sources_config:
            name = source.get('name', 'default')
            symbols = source.get('symbols', [])
            sources[name] = symbols
        
        logger.info(f"Initialized {len(sources)} data sources")
        return sources
    
    def collect_initial_data(self, symbols: Optional[List[str]] = None) -> Dict[str, pd.DataFrame]:
        """
        Collect initial bulk historical data for all symbols.
        
        Args:
            symbols: List of symbols to collect. If None, uses all configured symbols.
        
        Returns:
            Dictionary mapping symbols to their historical data
        """
        if symbols is None:
            symbols = self._get_all_symbols()
        
        initial_years = self.data_collection_config.get('initial_years', 5)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=initial_years * 365)
        
        logger.info(f"Starting initial data collection for {len(symbols)} symbols")
        logger.info(f"Date range: {start_date.date()} to {end_date.date()}")
        
        collected_data = {}
        
        for symbol in symbols:
            try:
                logger.info(f"Collecting data for {symbol}")
                data = self._fetch_historical_data(symbol, start_date, end_date)
                
                if data is not None and not data.empty:
                    collected_data[symbol] = data
                    self._save_data(symbol, data)
                    logger.info(f"Successfully collected {len(data)} data points for {symbol}")
                else:
                    logger.warning(f"No data collected for {symbol}")
                    
            except Exception as e:
                logger.error(f"Error collecting data for {symbol}: {str(e)}")
        
        logger.info(f"Initial data collection completed. Collected data for {len(collected_data)} symbols")
        return collected_data
    
    def update_daily_data(self, symbols: Optional[List[str]] = None) -> Dict[str, pd.DataFrame]:
        """
        Update data with the latest daily information.
        
        Args:
            symbols: List of symbols to update. If None, uses all configured symbols.
        
        Returns:
            Dictionary mapping symbols to their updated data
        """
        if symbols is None:
            symbols = self._get_all_symbols()
        
        logger.info(f"Starting daily data update for {len(symbols)} symbols")
        
        updated_data = {}
        
        for symbol in symbols:
            try:
                # Load existing data
                existing_data = self._load_data(symbol)
                
                if existing_data is not None and not existing_data.empty:
                    # Get the last date in existing data
                    last_date = existing_data.index[-1]
                    start_date = last_date + timedelta(days=1)
                    end_date = datetime.now()
                    
                    if start_date < end_date:
                        logger.info(f"Updating data for {symbol} from {start_date.date()}")
                        new_data = self._fetch_historical_data(symbol, start_date, end_date)
                        
                        if new_data is not None and not new_data.empty:
                            # Combine existing and new data
                            combined_data = pd.concat([existing_data, new_data])
                            combined_data = combined_data[~combined_data.index.duplicated(keep='last')]
                            
                            updated_data[symbol] = combined_data
                            self._save_data(symbol, combined_data)
                            logger.info(f"Successfully updated {symbol} with {len(new_data)} new data points")
                        else:
                            logger.info(f"No new data available for {symbol}")
                    else:
                        logger.info(f"Data for {symbol} is already up to date")
                        updated_data[symbol] = existing_data
                else:
                    logger.warning(f"No existing data found for {symbol}, collecting initial data")
                    initial_data = self.collect_initial_data([symbol])
                    if symbol in initial_data:
                        updated_data[symbol] = initial_data[symbol]
                        
            except Exception as e:
                logger.error(f"Error updating data for {symbol}: {str(e)}")
        
        logger.info(f"Daily data update completed. Updated {len(updated_data)} symbols")
        return updated_data
    
    def get_realtime_data(self, symbols: List[str]) -> Dict[str, pd.DataFrame]:
        """
        Get real-time data for active positions.
        
        Args:
            symbols: List of symbols to get real-time data for
        
        Returns:
            Dictionary mapping symbols to their real-time data
        """
        logger.info(f"Fetching real-time data for {len(symbols)} symbols")
        
        realtime_data = {}
        current_time = time.time()
        cache_duration = self.data_collection_config.get('cache_settings', {}).get('position_data', 60)
        
        for symbol in symbols:
            try:
                # Check cache first
                if (symbol in self.realtime_cache and 
                    symbol in self.cache_timestamps and
                    current_time - self.cache_timestamps[symbol] < cache_duration):
                    
                    realtime_data[symbol] = self.realtime_cache[symbol]
                    logger.debug(f"Using cached real-time data for {symbol}")
                else:
                    # Fetch fresh data
                    data = self._fetch_realtime_data(symbol)
                    if data is not None and not data.empty:
                        realtime_data[symbol] = data
                        self.realtime_cache[symbol] = data
                        self.cache_timestamps[symbol] = current_time
                        logger.debug(f"Fetched fresh real-time data for {symbol}")
                    else:
                        logger.warning(f"No real-time data available for {symbol}")
                        
            except Exception as e:
                logger.error(f"Error fetching real-time data for {symbol}: {str(e)}")
        
        return realtime_data
    
    def _fetch_historical_data(self, symbol: str, start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
        """Fetch historical data for a symbol."""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date)
            
            if data.empty:
                return None
            
            # Standardize column names
            data.columns = [col.lower() for col in data.columns]
            
            # Add symbol column
            data['symbol'] = symbol
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
            return None
    
    def _fetch_realtime_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Fetch real-time data for a symbol."""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d", interval="1m")
            
            if data.empty:
                return None
            
            # Standardize column names
            data.columns = [col.lower() for col in data.columns]
            
            # Add symbol column
            data['symbol'] = symbol
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching real-time data for {symbol}: {str(e)}")
            return None
    
    def _get_all_symbols(self) -> List[str]:
        """Get all symbols from all configured sources."""
        all_symbols = []
        for source_symbols in self.sources.values():
            all_symbols.extend(source_symbols)
        return list(set(all_symbols))  # Remove duplicates
    
    def _save_data(self, symbol: str, data: pd.DataFrame) -> None:
        """Save data to disk."""
        try:
            file_path = self.data_dir / f"{symbol}_data.csv"
            data.to_csv(file_path)
            logger.debug(f"Saved data for {symbol} to {file_path}")
        except Exception as e:
            logger.error(f"Error saving data for {symbol}: {str(e)}")
    
    def _load_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Load data from disk."""
        try:
            file_path = self.data_dir / f"{symbol}_data.csv"
            if file_path.exists():
                data = pd.read_csv(file_path, index_col=0, parse_dates=True)
                logger.debug(f"Loaded data for {symbol} from {file_path}")
                return data
            else:
                logger.debug(f"No saved data found for {symbol}")
                return None
        except Exception as e:
            logger.error(f"Error loading data for {symbol}: {str(e)}")
            return None
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Get a summary of collected data."""
        summary = {
            'total_symbols': len(self._get_all_symbols()),
            'saved_symbols': 0,
            'data_sources': list(self.sources.keys()),
            'cache_status': {
                'realtime_cache_size': len(self.realtime_cache),
                'cache_timestamps': len(self.cache_timestamps)
            }
        }
        
        # Count saved data files
        for file_path in self.data_dir.glob("*_data.csv"):
            summary['saved_symbols'] += 1
        
        return summary 