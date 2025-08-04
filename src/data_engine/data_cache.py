#!/usr/bin/env python3
"""
Data Cache System for StockTradeSolution

Provides local caching of stock data to avoid repeated API calls.
Stores daily transactions for historical analysis.
"""

import os
import json
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pickle
import hashlib
from pathlib import Path

from src.utils.logger import get_logger

class DataCache:
    """Local database for caching stock data and transaction logs."""
    
    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger(__name__)
        
        # Initialize database
        self.db_path = self.cache_dir / "trading_cache.db"
        self._init_database()
        
        self.logger.info(f"Data cache initialized at {self.cache_dir}")
    
    def _init_database(self):
        """Initialize SQLite database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Stock data cache table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_data_cache (
                symbol TEXT,
                start_date TEXT,
                end_date TEXT,
                data_hash TEXT,
                last_updated TIMESTAMP,
                data_path TEXT,
                PRIMARY KEY (symbol, start_date, end_date)
            )
        ''')
        
        # Transaction logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transaction_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                backtest_id TEXT,
                date TEXT,
                symbol TEXT,
                action TEXT,
                shares REAL,
                price REAL,
                value REAL,
                reason TEXT,
                portfolio_value REAL,
                strategy TEXT,
                profile TEXT
            )
        ''')
        
        # Backtest results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backtest_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                backtest_id TEXT UNIQUE,
                strategy TEXT,
                profile TEXT,
                start_date TEXT,
                end_date TEXT,
                initial_capital REAL,
                final_portfolio_value REAL,
                total_trades INTEGER,
                total_return REAL,
                max_drawdown REAL,
                sharpe_ratio REAL,
                results_path TEXT
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_backtest ON transaction_logs(backtest_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_symbol ON transaction_logs(symbol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_date ON transaction_logs(date)')
        
        conn.commit()
        conn.close()
        
        self.logger.info("Database initialized with stock cache, transaction logs, and backtest results tables")
    
    def get_cached_data(self, symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """Retrieve cached stock data if available and fresh."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT data_path, last_updated FROM stock_data_cache 
                WHERE symbol = ? AND start_date = ? AND end_date = ?
            ''', (symbol, start_date, end_date))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                data_path, last_updated = result
                last_updated = datetime.fromisoformat(last_updated)
                
                # Check if cache is fresh (less than 24 hours old)
                if datetime.now() - last_updated < timedelta(hours=24):
                    cache_file = Path(data_path)
                    if cache_file.exists():
                        with open(cache_file, 'rb') as f:
                            data = pickle.load(f)
                        self.logger.info(f"Retrieved cached data for {symbol} ({start_date} to {end_date})")
                        return data
                    else:
                        self.logger.warning(f"Cache file missing for {symbol}, will re-fetch")
                else:
                    self.logger.info(f"Cache expired for {symbol}, will re-fetch")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error retrieving cached data for {symbol}: {e}")
            return None
    
    def cache_data(self, symbol: str, data: pd.DataFrame, start_date: str, end_date: str):
        """Cache stock data locally."""
        try:
            # Create data hash for integrity checking
            data_hash = hashlib.md5(pickle.dumps(data)).hexdigest()
            
            # Save data to pickle file
            cache_file = self.cache_dir / f"{symbol}_{start_date}_{end_date}.pkl"
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
            
            # Update database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO stock_data_cache 
                (symbol, start_date, end_date, data_hash, last_updated, data_path)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (symbol, start_date, end_date, data_hash, datetime.now().isoformat(), str(cache_file)))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Cached data for {symbol} ({start_date} to {end_date})")
            
        except Exception as e:
            self.logger.error(f"Error caching data for {symbol}: {e}")
    
    def log_transaction(self, backtest_id: str, transaction: Dict[str, Any]):
        """Log a single transaction."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO transaction_logs 
                (backtest_id, date, symbol, action, shares, price, value, reason, portfolio_value, strategy, profile)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                backtest_id,
                transaction.get('date'),
                transaction.get('symbol'),
                transaction.get('action'),
                transaction.get('shares'),
                transaction.get('price'),
                transaction.get('value'),
                transaction.get('reason'),
                transaction.get('portfolio_value'),
                transaction.get('strategy'),
                transaction.get('profile')
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error logging transaction: {e}")
    
    def log_backtest_result(self, backtest_id: str, result: Dict[str, Any]):
        """Log backtest results."""
        try:
            # Save detailed results to JSON file
            results_file = self.cache_dir / f"backtest_{backtest_id}.json"
            with open(results_file, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO backtest_results 
                (backtest_id, strategy, profile, start_date, end_date, initial_capital, 
                 final_portfolio_value, total_trades, total_return, max_drawdown, sharpe_ratio, results_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                backtest_id,
                result.get('strategy'),
                result.get('profile'),
                result.get('start_date'),
                result.get('end_date'),
                result.get('initial_capital'),
                result.get('final_portfolio_value'),
                result.get('total_trades'),
                result.get('total_return'),
                result.get('max_drawdown'),
                result.get('sharpe_ratio'),
                str(results_file)
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Logged backtest results for {backtest_id}")
            
        except Exception as e:
            self.logger.error(f"Error logging backtest result: {e}")
    
    def get_transaction_history(self, backtest_id: Optional[str] = None, 
                              symbol: Optional[str] = None, 
                              start_date: Optional[str] = None,
                              end_date: Optional[str] = None) -> pd.DataFrame:
        """Retrieve transaction history with optional filters."""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = "SELECT * FROM transaction_logs WHERE 1=1"
            params = []
            
            if backtest_id:
                query += " AND backtest_id = ?"
                params.append(backtest_id)
            
            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)
            
            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND date <= ?"
                params.append(end_date)
            
            query += " ORDER BY timestamp DESC"
            
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error retrieving transaction history: {e}")
            return pd.DataFrame()
    
    def get_backtest_history(self) -> pd.DataFrame:
        """Retrieve all backtest results."""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("SELECT * FROM backtest_results ORDER BY timestamp DESC", conn)
            conn.close()
            return df
            
        except Exception as e:
            self.logger.error(f"Error retrieving backtest history: {e}")
            return pd.DataFrame()
    
    def clear_old_cache(self, days: int = 30):
        """Clear cache older than specified days."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get old cache entries
            cursor.execute('''
                SELECT data_path FROM stock_data_cache 
                WHERE last_updated < ?
            ''', (cutoff_date.isoformat(),))
            
            old_files = cursor.fetchall()
            
            # Delete old files
            for (data_path,) in old_files:
                try:
                    Path(data_path).unlink(missing_ok=True)
                except Exception as e:
                    self.logger.warning(f"Could not delete old cache file {data_path}: {e}")
            
            # Delete old database entries
            cursor.execute('''
                DELETE FROM stock_data_cache 
                WHERE last_updated < ?
            ''', (cutoff_date.isoformat(),))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Cleared {len(old_files)} old cache entries")
            
        except Exception as e:
            self.logger.error(f"Error clearing old cache: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Count cached symbols
            cursor.execute('SELECT COUNT(DISTINCT symbol) FROM stock_data_cache')
            cached_symbols = cursor.fetchone()[0]
            
            # Count total cache entries
            cursor.execute('SELECT COUNT(*) FROM stock_data_cache')
            total_entries = cursor.fetchone()[0]
            
            # Count transactions
            cursor.execute('SELECT COUNT(*) FROM transaction_logs')
            total_transactions = cursor.fetchone()[0]
            
            # Count backtests
            cursor.execute('SELECT COUNT(*) FROM backtest_results')
            total_backtests = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'cached_symbols': cached_symbols,
                'total_cache_entries': total_entries,
                'total_transactions': total_transactions,
                'total_backtests': total_backtests,
                'cache_directory': str(self.cache_dir)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting cache stats: {e}")
            return {} 

    def get_cached_symbols(self) -> List[str]:
        """Get list of all cached symbols."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT symbol FROM stock_data_cache")
            symbols = [row[0] for row in cursor.fetchall()]
            conn.close()
            return symbols
        except Exception as e:
            self.logger.error(f"Error getting cached symbols: {e}")
            return []
    
    def clear_all_data(self):
        """Clear all cached data, transactions, and backtest results."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Clear all tables
            cursor.execute("DELETE FROM stock_data_cache")
            cursor.execute("DELETE FROM transaction_logs")
            cursor.execute("DELETE FROM backtest_results")
            
            # Reset auto-increment counters
            cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('transaction_logs', 'backtest_results')")
            
            conn.commit()
            conn.close()
            
            # Clear cache files
            for cache_file in self.cache_dir.glob("*.pkl"):
                try:
                    cache_file.unlink()
                except Exception as e:
                    self.logger.warning(f"Could not delete cache file {cache_file}: {e}")
            
            self.logger.info("✅ All cached data cleared successfully")
            
        except Exception as e:
            self.logger.error(f"Error clearing all data: {e}") 