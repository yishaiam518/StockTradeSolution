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
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            # Create collections table
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
                    status TEXT DEFAULT 'completed',
                    last_updated TEXT,
                    auto_update BOOLEAN DEFAULT FALSE,
                    update_interval TEXT DEFAULT '24h',
                    last_run TEXT,
                    next_run TEXT
                )
            ''')
            
            # Create collection_data table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS collection_data (
                    collection_id TEXT,
                    symbol TEXT,
                    data TEXT,
                    last_updated TEXT,
                    PRIMARY KEY (collection_id, symbol),
                    FOREIGN KEY (collection_id) REFERENCES collections (collection_id)
                )
            ''')
            
            # Create technical_indicators table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS technical_indicators (
                    collection_id TEXT,
                    symbol TEXT,
                    indicators_data TEXT,
                    calculated_date TEXT,
                    last_updated TEXT,
                    PRIMARY KEY (collection_id, symbol),
                    FOREIGN KEY (collection_id) REFERENCES collections (collection_id)
                )
            ''')
            
            # Migrate existing collections to add missing columns
            self._migrate_existing_collections()
            
            conn.commit()
    
    def _migrate_existing_collections(self):
        """Migrate existing collections to add new columns if they don't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check if last_updated column exists
                cursor = conn.execute("PRAGMA table_info(collections)")
                columns = [column[1] for column in cursor.fetchall()]
                
                # Add missing columns if they don't exist
                if 'last_updated' not in columns:
                    conn.execute('ALTER TABLE collections ADD COLUMN last_updated TEXT')
                    # Set default value for existing records
                    conn.execute('UPDATE collections SET last_updated = collection_date WHERE last_updated IS NULL')
                
                if 'auto_update' not in columns:
                    conn.execute('ALTER TABLE collections ADD COLUMN auto_update BOOLEAN DEFAULT FALSE')
                
                if 'update_interval' not in columns:
                    conn.execute('ALTER TABLE collections ADD COLUMN update_interval TEXT DEFAULT "24h"')
                
                if 'last_run' not in columns:
                    conn.execute('ALTER TABLE collections ADD COLUMN last_run TEXT')
                
                if 'next_run' not in columns:
                    conn.execute('ALTER TABLE collections ADD COLUMN next_run TEXT')
                
                # Check if last_updated column exists in collection_data
                cursor = conn.execute("PRAGMA table_info(collection_data)")
                data_columns = [column[1] for column in cursor.fetchall()]
                
                if 'last_updated' not in data_columns:
                    conn.execute('ALTER TABLE collection_data ADD COLUMN last_updated TEXT')
                    # Set default value for existing records
                    conn.execute('UPDATE collection_data SET last_updated = datetime("now") WHERE last_updated IS NULL')
                
                conn.commit()
                self.logger.info("Database migration completed successfully")
                
        except Exception as e:
            self.logger.error(f"Error during database migration: {e}")
    
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
                    total_symbols, successful_symbols, failed_count, collection_date,
                    last_updated, auto_update
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                collection_id, config.exchange.value, config.start_date, config.end_date,
                json.dumps(config.symbols) if config.symbols else None,
                json.dumps(config.sectors) if config.sectors else None,
                config.market_cap_min, config.market_cap_max,
                config.include_etfs, config.include_penny_stocks,
                total_symbols, successful_symbols, failed_count,
                datetime.now().isoformat(),
                datetime.now().isoformat(),  # last_updated
                False  # auto_update (default to False)
            ))
            conn.commit()
    
    def _save_collection_data_to_db(self, collection_id: str, collected_data: Dict[str, pd.DataFrame]):
        """Save collected data to database."""
        with sqlite3.connect(self.db_path) as conn:
            for symbol, data in collected_data.items():
                # Convert DataFrame to JSON for storage
                data_json = data.to_json(orient='records')
                conn.execute('''
                    INSERT OR REPLACE INTO collection_data (collection_id, symbol, data, last_updated)
                    VALUES (?, ?, ?, ?)
                ''', (collection_id, symbol, data_json, datetime.now().isoformat()))
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
            # Check if auto_update and update_interval columns exist
            cursor = conn.execute("PRAGMA table_info(collections)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Build query based on available columns
            if 'auto_update' in columns and 'update_interval' in columns and 'last_run' in columns and 'next_run' in columns:
                cursor = conn.execute('''
                    SELECT collection_id, exchange, start_date, end_date, total_symbols,
                           successful_symbols, failed_count, collection_date, status,
                           auto_update, update_interval, last_run, next_run
                    FROM collections ORDER BY collection_date DESC
                ''')
            elif 'auto_update' in columns and 'update_interval' in columns:
                cursor = conn.execute('''
                    SELECT collection_id, exchange, start_date, end_date, total_symbols,
                           successful_symbols, failed_count, collection_date, status,
                           auto_update, update_interval
                    FROM collections ORDER BY collection_date DESC
                ''')
            elif 'auto_update' in columns:
                cursor = conn.execute('''
                    SELECT collection_id, exchange, start_date, end_date, total_symbols,
                           successful_symbols, failed_count, collection_date, status,
                           auto_update
                    FROM collections ORDER BY collection_date DESC
                ''')
            else:
                cursor = conn.execute('''
                    SELECT collection_id, exchange, start_date, end_date, total_symbols,
                           successful_symbols, failed_count, collection_date, status
                    FROM collections ORDER BY collection_date DESC
                ''')
            
            rows = cursor.fetchall()
            
            collections = []
            for row in rows:
                collection_data = {
                    'collection_id': row[0],
                    'exchange': row[1],
                    'start_date': row[2],
                    'end_date': row[3],
                    'total_symbols': row[4],
                    'successful_symbols': row[5],
                    'failed_count': row[6],
                    'collection_date': row[7],
                    'status': row[8]
                }
                
                # Add auto_update field if available
                if 'auto_update' in columns and len(row) > 9:
                    collection_data['auto_update'] = bool(row[9])
                else:
                    collection_data['auto_update'] = False
                
                # Add update_interval field if available
                if 'update_interval' in columns and len(row) > 10:
                    collection_data['update_interval'] = row[10] or '24h'
                else:
                    collection_data['update_interval'] = '24h'
                
                # Add last_run field if available
                if 'last_run' in columns and len(row) > 11:
                    collection_data['last_run'] = row[11]
                else:
                    collection_data['last_run'] = None
                
                # Add next_run field if available
                if 'next_run' in columns and len(row) > 12:
                    collection_data['next_run'] = row[12]
                else:
                    collection_data['next_run'] = None
                
                collections.append(collection_data)
            
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
    
    def update_collection(self, collection_id: str) -> Dict[str, any]:
        """
        Update an existing collection to include data up to today.
        
        Args:
            collection_id: The collection ID to update
            
        Returns:
            Dictionary with update results
        """
        try:
            # Get existing collection data
            existing_data = self.get_collected_data(collection_id)
            if not existing_data:
                return {'success': False, 'error': 'Collection not found'}
            
            # Get collection metadata
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT exchange, start_date, end_date, symbols FROM collections 
                    WHERE collection_id = ?
                ''', (collection_id,))
                row = cursor.fetchone()
                
                if not row:
                    return {'success': False, 'error': 'Collection metadata not found'}
                
                exchange, start_date, end_date, symbols_json = row
                symbols = json.loads(symbols_json) if symbols_json else []
            
            # Calculate new end date (today)
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Update symbols with missing data
            updated_symbols = []
            failed_symbols = []
            
            for symbol in symbols:
                try:
                    # Fetch data from the last existing date to today
                    new_data = self._fetch_symbol_data(symbol, end_date, today)
                    if new_data is not None and not new_data.empty:
                        # Get existing data for this symbol
                        existing_symbol_data = existing_data['data'].get(symbol)
                        if existing_symbol_data is not None:
                            # Combine existing and new data
                            combined_data = pd.concat([existing_symbol_data, new_data])
                            combined_data = combined_data[~combined_data.index.duplicated(keep='last')]
                            combined_data = combined_data.sort_index()
                            
                            # Update in database
                            self._update_symbol_data(collection_id, symbol, combined_data)
                            updated_symbols.append(symbol)
                        else:
                            # Symbol doesn't exist in original collection, skip
                            continue
                    else:
                        failed_symbols.append(symbol)
                except Exception as e:
                    self.logger.error(f"Error updating {symbol}: {e}")
                    failed_symbols.append(symbol)
            
            # Update collection metadata
            with sqlite3.connect(self.db_path) as conn:
                # Check if last_updated column exists
                cursor = conn.execute("PRAGMA table_info(collections)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'last_updated' in columns:
                    conn.execute('''
                        UPDATE collections 
                        SET end_date = ?, last_updated = ?, failed_count = ?
                        WHERE collection_id = ?
                    ''', (today, datetime.now().isoformat(), len(failed_symbols), collection_id))
                else:
                    conn.execute('''
                        UPDATE collections 
                        SET end_date = ?, failed_count = ?
                        WHERE collection_id = ?
                    ''', (today, len(failed_symbols), collection_id))
                conn.commit()
            
            return {
                'success': True,
                'collection_id': collection_id,
                'updated_symbols': len(updated_symbols),
                'failed_symbols': len(failed_symbols),
                'new_end_date': today,
                'updated_symbols_list': updated_symbols,
                'failed_symbols_list': failed_symbols
            }
            
        except Exception as e:
            self.logger.error(f"Error updating collection {collection_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def _update_symbol_data(self, collection_id: str, symbol: str, data: pd.DataFrame):
        """Update symbol data in the database."""
        try:
            data_json = data.to_json()
            with sqlite3.connect(self.db_path) as conn:
                # Check if last_updated column exists
                cursor = conn.execute("PRAGMA table_info(collection_data)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'last_updated' in columns:
                    conn.execute('''
                        UPDATE collection_data 
                        SET data = ?, last_updated = ?
                        WHERE collection_id = ? AND symbol = ?
                    ''', (data_json, datetime.now().isoformat(), collection_id, symbol))
                else:
                    conn.execute('''
                        UPDATE collection_data 
                        SET data = ?
                        WHERE collection_id = ? AND symbol = ?
                    ''', (data_json, collection_id, symbol))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error updating symbol data for {symbol}: {e}")
    
    def enable_auto_update(self, collection_id: str, enable: bool = True, interval: str = "24h", last_run: str = None, next_run: str = None) -> bool:
        """
        Enable or disable automatic updates for a collection.
        
        Args:
            collection_id: The collection ID
            enable: Whether to enable auto-update
            interval: Update interval (5min, 10min, 30min, 1h, 24h)
            last_run: ISO format timestamp of last run
            next_run: ISO format timestamp of next run
            
        Returns:
            Success status
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check if auto_update column exists
                cursor = conn.execute("PRAGMA table_info(collections)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'auto_update' in columns and 'update_interval' in columns and 'last_run' in columns and 'next_run' in columns:
                    self.logger.info(f"Updating collection {collection_id} with auto_update={enable}, interval={interval}, last_run={last_run}, next_run={next_run}")
                    conn.execute('''
                        UPDATE collections 
                        SET auto_update = ?, update_interval = ?, last_run = ?, next_run = ?
                        WHERE collection_id = ?
                    ''', (enable, interval, last_run, next_run, collection_id))
                elif 'auto_update' in columns and 'update_interval' in columns:
                    conn.execute('''
                        UPDATE collections 
                        SET auto_update = ?, update_interval = ?
                        WHERE collection_id = ?
                    ''', (enable, interval, collection_id))
                elif 'auto_update' in columns:
                    conn.execute('''
                        UPDATE collections 
                        SET auto_update = ?
                        WHERE collection_id = ?
                    ''', (enable, collection_id))
                else:
                    # If column doesn't exist, we can't set auto_update
                    self.logger.warning(f"auto_update column not found for {collection_id}")
                    return False
                conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error setting auto-update for {collection_id}: {e}")
            return False
    
    def get_collections_for_auto_update(self) -> List[str]:
        """Get list of collection IDs that have auto-update enabled."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check if auto_update column exists
                cursor = conn.execute("PRAGMA table_info(collections)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'auto_update' in columns:
                    cursor = conn.execute('''
                        SELECT collection_id FROM collections 
                        WHERE auto_update = TRUE
                    ''')
                else:
                    # If column doesn't exist, return empty list
                    return []
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Error getting auto-update collections: {e}")
            return []
    
    def get_collection_details(self, collection_id: str) -> Optional[Dict]:
        """Get detailed information about a specific collection."""
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
                    'symbols': row[4],
                    'sectors': row[5],
                    'market_cap_min': row[6],
                    'market_cap_max': row[7],
                    'include_etfs': row[8],
                    'include_penny_stocks': row[9],
                    'total_symbols': row[10],
                    'successful_symbols': row[11],
                    'failed_count': row[12],
                    'collection_date': row[13],
                    'status': row[14],
                    'last_updated': row[15],
                    'auto_update': row[16],
                    'update_interval': row[17],
                    'last_run': row[18],
                    'next_run': row[19]
                }
        return None
    
    def get_collection_symbols(self, collection_id: str) -> List[str]:
        """Get all symbols for a specific collection."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT symbol FROM collection_data WHERE collection_id = ?
            ''', (collection_id,))
            
            symbols = [row[0] for row in cursor.fetchall()]
            return symbols
    
    def get_symbol_data(self, collection_id: str, symbol: str) -> Optional[pd.DataFrame]:
        """Get data for a specific symbol in a collection."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT data FROM collection_data 
                WHERE collection_id = ? AND symbol = ?
            ''', (collection_id, symbol))
            
            row = cursor.fetchone()
            if row and row[0]:
                try:
                    data = pd.read_json(row[0])
                    return data
                except Exception as e:
                    self.logger.error(f"Error parsing data for {symbol}: {e}")
                    return None
        return None
    
    def store_symbol_indicators(self, collection_id: str, symbol: str, enhanced_data: pd.DataFrame) -> bool:
        """Store technical indicators data for a symbol."""
        try:
            # Convert the enhanced DataFrame to JSON
            indicators_json = enhanced_data.to_json()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO technical_indicators 
                    (collection_id, symbol, indicators_data, calculated_date, last_updated)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    collection_id,
                    symbol,
                    indicators_json,
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                conn.commit()
            
            self.logger.info(f"Stored technical indicators for {symbol} in collection {collection_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing indicators for {symbol}: {e}")
            return False
    
    def get_symbol_indicators(self, collection_id: str, symbol: str) -> Optional[pd.DataFrame]:
        """Get technical indicators data for a symbol."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT indicators_data FROM technical_indicators 
                WHERE collection_id = ? AND symbol = ?
            ''', (collection_id, symbol))
            
            row = cursor.fetchone()
            if row and row[0]:
                try:
                    data = pd.read_json(row[0])
                    return data
                except Exception as e:
                    self.logger.error(f"Error parsing indicators for {symbol}: {e}")
                    return None
        return None
    
    def get_collection_indicators_status(self, collection_id: str) -> Dict:
        """Get the status of technical indicators for a collection."""
        with sqlite3.connect(self.db_path) as conn:
            # Get total symbols in collection
            cursor = conn.execute('''
                SELECT COUNT(*) FROM collection_data WHERE collection_id = ?
            ''', (collection_id,))
            total_symbols = cursor.fetchone()[0]
            
            # Get symbols with indicators
            cursor = conn.execute('''
                SELECT COUNT(*) FROM technical_indicators WHERE collection_id = ?
            ''', (collection_id,))
            symbols_with_indicators = cursor.fetchone()[0]
            
            # Get latest calculation date
            cursor = conn.execute('''
                SELECT MAX(calculated_date) FROM technical_indicators WHERE collection_id = ?
            ''', (collection_id,))
            latest_calculation = cursor.fetchone()[0]
            
            return {
                'total_symbols': total_symbols,
                'symbols_with_indicators': symbols_with_indicators,
                'indicators_coverage': f"{(symbols_with_indicators/total_symbols*100):.1f}%" if total_symbols > 0 else "0%",
                'latest_calculation': latest_calculation,
                'indicators_available': symbols_with_indicators > 0
            }
    
    def calculate_collection_indicators(self, collection_id: str) -> Dict:
        """Manually trigger technical indicator calculation for a collection."""
        try:
            from src.indicators import indicator_manager
            
            symbols = self.get_collection_symbols(collection_id)
            if not symbols:
                return {'success': False, 'error': 'No symbols found for collection'}
            
            calculated_count = 0
            errors = []
            
            for symbol in symbols:
                try:
                    # Get the symbol data
                    symbol_data = self.get_symbol_data(collection_id, symbol)
                    if symbol_data is None or symbol_data.empty:
                        errors.append(f"No data for {symbol}")
                        continue
                    
                    # Calculate all technical indicators
                    enhanced_data = indicator_manager.calculate_all_indicators(symbol_data)
                    
                    # Store the enhanced data with indicators
                    if self.store_symbol_indicators(collection_id, symbol, enhanced_data):
                        calculated_count += 1
                    else:
                        errors.append(f"Failed to store indicators for {symbol}")
                    
                except Exception as e:
                    errors.append(f"Error calculating indicators for {symbol}: {e}")
                    continue
            
            return {
                'success': True,
                'calculated_count': calculated_count,
                'total_symbols': len(symbols),
                'errors': errors,
                'coverage': f"{(calculated_count/len(symbols)*100):.1f}%" if symbols else "0%"
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)} 