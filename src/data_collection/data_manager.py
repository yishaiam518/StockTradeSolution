#!/usr/bin/env python3
"""
Data Collection Manager
Handles exchange-based data collection with filtering capabilities.
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from enum import Enum
import sqlite3
import json
import os

class Exchange(Enum):
    """Supported stock exchanges."""
    NASDAQ = "NASDAQ"
    NYSE = "NYSE"
    AMEX = "AMEX"
    ALL = "ALL"

@dataclass
class DataCollectionConfig:
    """Configuration for data collection."""
    exchange: Exchange
    start_date: str
    end_date: str
    symbols: Optional[List[str]] = None
    sectors: Optional[List[str]] = None
    market_cap_min: Optional[float] = None
    market_cap_max: Optional[float] = None
    include_etfs: bool = True
    include_penny_stocks: bool = False

class DataCollectionManager:
    """Manages data collection from various exchanges."""
    
    def __init__(self, db_path: str = "data/collections.db"):
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path
        self._init_database()
        
        # Exchange symbol mappings
        self.exchange_symbols = {
            Exchange.NASDAQ: self._get_nasdaq_symbols,
            Exchange.NYSE: self._get_nyse_symbols,
            Exchange.AMEX: self._get_amex_symbols,
            Exchange.ALL: self._get_all_symbols
        }
    
    def _init_database(self):
        """Initialize the database for storing collections."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS collections (
                    collection_id TEXT PRIMARY KEY,
                    exchange TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    symbols TEXT,
                    sectors TEXT,
                    market_cap_min REAL,
                    market_cap_max REAL,
                    include_etfs BOOLEAN,
                    include_penny_stocks BOOLEAN,
                    total_symbols INTEGER,
                    successful_symbols INTEGER,
                    failed_count INTEGER,
                    collection_date TEXT,
                    status TEXT DEFAULT 'completed'
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS collection_data (
                    collection_id TEXT,
                    symbol TEXT,
                    data TEXT,
                    PRIMARY KEY (collection_id, symbol),
                    FOREIGN KEY (collection_id) REFERENCES collections (collection_id)
                )
            ''')
            
            conn.commit()
    
    def collect_data(self, config: DataCollectionConfig) -> Dict[str, any]:
        """
        Collect data based on configuration.
        
        Args:
            config: DataCollectionConfig object
            
        Returns:
            Dictionary with collection results
        """
        try:
            self.logger.info(f"Starting data collection for {config.exchange.value}")
            
            # Get symbols for the exchange
            symbols = self._get_symbols_for_exchange(config)
            self.logger.info(f"Found {len(symbols)} symbols for {config.exchange.value}")
            
            # Apply filters
            filtered_symbols = self._apply_filters(symbols, config)
            self.logger.info(f"After filtering: {len(filtered_symbols)} symbols")
            
            # Collect data for each symbol
            collected_data = {}
            failed_symbols = []
            
            for i, symbol in enumerate(filtered_symbols):
                try:
                    self.logger.info(f"Collecting data for {symbol} ({i+1}/{len(filtered_symbols)})")
                    
                    data = self._fetch_symbol_data(symbol, config.start_date, config.end_date)
                    if data is not None and len(data) > 0:
                        collected_data[symbol] = data
                        self.logger.info(f"✅ Collected {len(data)} data points for {symbol}")
                    else:
                        failed_symbols.append(symbol)
                        self.logger.warning(f"❌ No data for {symbol}")
                        
                except Exception as e:
                    failed_symbols.append(symbol)
                    self.logger.error(f"❌ Error collecting data for {symbol}: {e}")
            
            # Store results in database
            collection_id = f"{config.exchange.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            self._save_collection_to_db(collection_id, config, len(filtered_symbols), 
                                      len(collected_data), len(failed_symbols))
            
            # Save collected data
            self._save_collection_data_to_db(collection_id, collected_data)
            
            return {
                'collection_id': collection_id,
                'status': 'success',
                'total_symbols': len(filtered_symbols),
                'successful_symbols': len(collected_data),
                'failed_symbols': failed_symbols,
                'data': collected_data
            }
            
        except Exception as e:
            self.logger.error(f"Error in data collection: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _save_collection_to_db(self, collection_id: str, config: DataCollectionConfig, 
                              total_symbols: int, successful_symbols: int, failed_count: int):
        """Save collection metadata to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO collections (
                    collection_id, exchange, start_date, end_date, symbols, sectors,
                    market_cap_min, market_cap_max, include_etfs, include_penny_stocks,
                    total_symbols, successful_symbols, failed_count, collection_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                collection_id, config.exchange.value, config.start_date, config.end_date,
                json.dumps(config.symbols) if config.symbols else None,
                json.dumps(config.sectors) if config.sectors else None,
                config.market_cap_min, config.market_cap_max,
                config.include_etfs, config.include_penny_stocks,
                total_symbols, successful_symbols, failed_count,
                datetime.now().isoformat()
            ))
            conn.commit()
    
    def _save_collection_data_to_db(self, collection_id: str, collected_data: Dict[str, pd.DataFrame]):
        """Save collected data to database."""
        with sqlite3.connect(self.db_path) as conn:
            for symbol, data in collected_data.items():
                # Convert DataFrame to JSON for storage
                data_json = data.to_json(orient='records')
                conn.execute('''
                    INSERT OR REPLACE INTO collection_data (collection_id, symbol, data)
                    VALUES (?, ?, ?)
                ''', (collection_id, symbol, data_json))
            conn.commit()
    
    def _get_symbols_for_exchange(self, config: DataCollectionConfig) -> List[str]:
        """Get symbols for the specified exchange."""
        if config.symbols:
            return config.symbols
        
        # Use the appropriate function for the exchange
        symbol_function = self.exchange_symbols.get(config.exchange)
        if symbol_function:
            return symbol_function()
        
        return []
    
    def _get_nasdaq_symbols(self) -> List[str]:
        """Get NASDAQ symbols."""
        # For now, return a subset of popular NASDAQ symbols
        # In production, you'd fetch this from a proper source
        return [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMD', 'INTC',
            'ADBE', 'CRM', 'PYPL', 'COST', 'PEP', 'AVGO', 'QCOM', 'TXN', 'MU', 'ADP',
            'ORCL', 'CSCO', 'NFLX', 'CMCSA', 'COST', 'TMUS', 'ABNB', 'UBER', 'LYFT', 'ZM',
            'SNOW', 'PLTR', 'CRWD', 'ZS', 'OKTA', 'TEAM', 'SHOP', 'SQ', 'ROKU', 'SPOT',
            'PINS', 'SNAP', 'TWTR', 'FB', 'GOOG', 'AMZN', 'TSLA', 'NVDA', 'AMD', 'INTC'
        ]
    
    def _get_nyse_symbols(self) -> List[str]:
        """Get NYSE symbols."""
        return [
            'JNJ', 'JPM', 'V', 'PG', 'UNH', 'HD', 'MA', 'BAC', 'DIS', 'VZ',
            'KO', 'PFE', 'ABT', 'TMO', 'MRK', 'WMT', 'CVX', 'XOM', 'LLY', 'ABBV',
            'PEP', 'T', 'COST', 'ACN', 'DHR', 'NEE', 'TXN', 'HON', 'UPS', 'LOW',
            'RTX', 'SPGI', 'QCOM', 'TMO', 'ISRG', 'GILD', 'ADI', 'MDLZ', 'REGN', 'BKNG',
            'VRTX', 'KLAC', 'MU', 'PANW', 'CDNS', 'SNPS', 'MCHP', 'MRVL', 'AVGO', 'QCOM'
        ]
    
    def _get_amex_symbols(self) -> List[str]:
        """Get AMEX symbols."""
        return [
            'SPY', 'QQQ', 'IWM', 'VTI', 'VEA', 'VWO', 'BND', 'TLT', 'GLD', 'SLV',
            'XLE', 'XLF', 'XLK', 'XLV', 'XLI', 'XLP', 'XLY', 'XLU', 'XLB', 'XLC',
            'XBI', 'XOP', 'XRT', 'XHB', 'XME', 'XSD', 'XSW', 'XTH', 'XTL', 'XTN'
        ]
    
    def _get_all_symbols(self) -> List[str]:
        """Get symbols from all exchanges."""
        nasdaq = self._get_nasdaq_symbols()
        nyse = self._get_nyse_symbols()
        amex = self._get_amex_symbols()
        return nasdaq + nyse + amex
    
    def _apply_filters(self, symbols: List[str], config: DataCollectionConfig) -> List[str]:
        """Apply filters to the symbol list."""
        filtered_symbols = symbols.copy()
        
        # Filter by sectors (if specified)
        if config.sectors:
            # This would require sector data - for now, return all
            pass
        
        # Filter by market cap (if specified)
        if config.market_cap_min or config.market_cap_max:
            # This would require market cap data - for now, return all
            pass
        
        # Filter ETFs
        if not config.include_etfs:
            filtered_symbols = [s for s in filtered_symbols if not self._is_etf(s)]
        
        # Filter penny stocks
        if not config.include_penny_stocks:
            # This would require price data - for now, return all
            pass
        
        return filtered_symbols
    
    def _is_etf(self, symbol: str) -> bool:
        """Check if symbol is an ETF."""
        etf_indicators = ['SPY', 'QQQ', 'IWM', 'VTI', 'VEA', 'VWO', 'BND', 'TLT', 'GLD', 'SLV',
                         'XLE', 'XLF', 'XLK', 'XLV', 'XLI', 'XLP', 'XLY', 'XLU', 'XLB', 'XLC',
                         'XBI', 'XOP', 'XRT', 'XHB', 'XME', 'XSD', 'XSW', 'XTH', 'XTL', 'XTN']
        return symbol in etf_indicators
    
    def _fetch_symbol_data(self, symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """Fetch data for a specific symbol."""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date)
            
            if data is not None and len(data) > 0:
                # Reset index to make date a column
                data = data.reset_index()
                return data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error fetching data for {symbol}: {e}")
            return None
    
    def get_collection_status(self, collection_id: str) -> Optional[Dict]:
        """Get status of a data collection job."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT * FROM collections WHERE collection_id = ?
            ''', (collection_id,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'collection_id': row[0],
                    'exchange': row[1],
                    'start_date': row[2],
                    'end_date': row[3],
                    'total_symbols': row[10],
                    'successful_symbols': row[11],
                    'failed_count': row[12],
                    'collection_date': row[13],
                    'status': row[14]
                }
            return None
    
    def get_collected_data(self, collection_id: str) -> Optional[Dict]:
        """Get collected data for a specific collection ID."""
        with sqlite3.connect(self.db_path) as conn:
            # Get collection metadata
            cursor = conn.execute('''
                SELECT * FROM collections WHERE collection_id = ?
            ''', (collection_id,))
            collection_row = cursor.fetchone()
            
            if not collection_row:
                return None
            
            # Get collection data
            cursor = conn.execute('''
                SELECT symbol, data FROM collection_data WHERE collection_id = ?
            ''', (collection_id,))
            data_rows = cursor.fetchall()
            
            collected_data = {}
            for symbol, data_json in data_rows:
                try:
                    from io import StringIO
                    data = pd.read_json(StringIO(data_json))
                    collected_data[symbol] = data
                except Exception as e:
                    self.logger.error(f"Error parsing data for {symbol}: {e}")
            
            return {
                'collection_id': collection_id,
                'config': {
                    'exchange': collection_row[1],
                    'start_date': collection_row[2],
                    'end_date': collection_row[3]
                },
                'data': collected_data,
                'total_symbols': collection_row[10],
                'successful_symbols': collection_row[11],
                'failed_count': collection_row[12],
                'collection_date': collection_row[13]
            }
    
    def list_collections(self) -> List[Dict]:
        """List all data collections."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT collection_id, exchange, start_date, end_date, total_symbols,
                       successful_symbols, failed_count, collection_date, status
                FROM collections ORDER BY collection_date DESC
            ''')
            rows = cursor.fetchall()
            
            collections = []
            for row in rows:
                collections.append({
                    'collection_id': row[0],
                    'exchange': row[1],
                    'start_date': row[2],
                    'end_date': row[3],
                    'total_symbols': row[4],
                    'successful_symbols': row[5],
                    'failed_count': row[6],
                    'collection_date': row[7],
                    'status': row[8]
                })
            return collections
    
    def delete_collection(self, collection_id: str) -> bool:
        """Delete a data collection."""
        with sqlite3.connect(self.db_path) as conn:
            # Delete collection data first
            conn.execute('DELETE FROM collection_data WHERE collection_id = ?', (collection_id,))
            # Delete collection metadata
            conn.execute('DELETE FROM collections WHERE collection_id = ?', (collection_id,))
            conn.commit()
            return True 