"""
Data engine for fetching and managing stock data using yfinance.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
import sqlite3
import json
from src.utils.config_loader import config
from src.utils.logger import logger


class DataEngine:
    """Data engine for fetching and managing stock data."""
    
    def __init__(self):
        self.config = config.get_data_engine_config()
        self.data_dir = Path(self.config.get('data_directory', 'data/'))
        self.data_dir.mkdir(exist_ok=True)
        self.cache_duration = self.config.get('cache_duration', 3600)
        self.use_adjusted_close = self.config.get('use_adjusted_close', True)
        self.max_retries = self.config.get('max_retries', 3)
        
        # Initialize database
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize SQLite database for data storage."""
        db_config = config.get('database', {})
        db_path = db_config.get('path', 'data/trading_system.db')
        
        # Ensure data directory exists
        db_path = Path(db_path)
        db_path.parent.mkdir(exist_ok=True)
        
        self.db_path = db_path
        self._create_tables()
    
    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS stock_data (
                    ticker TEXT,
                    date TEXT,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume REAL,
                    adj_close REAL,
                    PRIMARY KEY (ticker, date)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS data_cache (
                    ticker TEXT,
                    last_updated TEXT,
                    data_hash TEXT,
                    PRIMARY KEY (ticker)
                )
            """)
            
            # Add trades table for persistent trade storage
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    strategy TEXT NOT NULL,
                    entry_date TEXT NOT NULL,
                    exit_date TEXT,
                    entry_price REAL NOT NULL,
                    exit_price REAL,
                    shares REAL NOT NULL,
                    pnl_pct REAL,
                    pnl_dollars REAL,
                    entry_reason TEXT,
                    exit_reason TEXT,
                    what_learned TEXT,
                    status TEXT DEFAULT 'open',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Add index for efficient querying
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_trades_ticker_date 
                ON trades(ticker, entry_date)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_trades_strategy 
                ON trades(strategy)
            """)
            
            conn.commit()
    
    def get_data(self, ticker: str, start_date: str = None, end_date: str = None, 
                 period: str = '1y', interval: str = '1d') -> pd.DataFrame:
        """
        Get stock data for a given ticker (alias for fetch_data with period support).
        
        Args:
            ticker: Stock ticker symbol
            start_date: Start date in YYYY-MM-DD format (optional if period provided)
            end_date: End date in YYYY-MM-DD format (optional if period provided)
            period: Period string (e.g., '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
            interval: Data interval (e.g., '1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo')
            
        Returns:
            DataFrame with OHLCV data
        """
        # If period is provided, calculate start_date and end_date
        if start_date is None or end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
            
            # Convert period to days for start_date calculation
            period_days = {
                '1d': 1, '5d': 5, '1mo': 30, '3mo': 90, '6mo': 180,
                '1y': 365, '2y': 730, '5y': 1825, '10y': 3650,
                'ytd': (datetime.now() - datetime(datetime.now().year, 1, 1)).days,
                'max': 3650  # Default to 10 years for 'max'
            }
            
            days = period_days.get(period, 365)  # Default to 1 year
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        return self.fetch_data(ticker, start_date, end_date)

    def fetch_data(self, ticker: str, start_date: str, end_date: str, 
                   force_refresh: bool = False) -> pd.DataFrame:
        """
        Fetch stock data for a given ticker and date range.
        
        Args:
            ticker: Stock ticker symbol
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            force_refresh: Force refresh from API even if cached
            
        Returns:
            DataFrame with OHLCV data
        """
        logger.info(f"Fetching data for {ticker} from {start_date} to {end_date}")
        
        # Check cache first
        if not force_refresh:
            cached_data = self._get_cached_data(ticker, start_date, end_date)
            if cached_data is not None:
                logger.info(f"Using cached data for {ticker}")
                return cached_data
        
        # Fetch from API
        data = self._fetch_from_api(ticker, start_date, end_date)
        
        if data is not None and not data.empty:
            # Store in cache
            self._store_data(ticker, data)
            logger.info(f"Successfully fetched {len(data)} records for {ticker}")
            return data
        else:
            logger.error(f"Failed to fetch data for {ticker}")
            return pd.DataFrame()
    
    def _fetch_from_api(self, ticker: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """Fetch data from yfinance API."""
        try:
            ticker_obj = yf.Ticker(ticker)
            data = ticker_obj.history(start=start_date, end=end_date)
            
            if data.empty:
                logger.warning(f"No data returned for {ticker}")
                return None
            
            # Reset index to make date a column
            data.reset_index(inplace=True)
            
            # Rename columns to match our standard
            data.columns = [col.lower() for col in data.columns]
            
            # Ensure all required columns exist
            required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
            for col in required_columns:
                if col not in data.columns:
                    logger.error(f"Missing required column: {col}")
                    return None
            
            # Use adjusted close if available and configured
            if self.use_adjusted_close and 'adj close' in data.columns:
                data['close'] = data['adj close']
            
            # Select only required columns
            data = data[required_columns]
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {str(e)}")
            return None
    
    def _get_cached_data(self, ticker: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """Get data from local cache/database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT date, open, high, low, close, volume
                    FROM stock_data 
                    WHERE ticker = ? AND date BETWEEN ? AND ?
                    ORDER BY date
                """
                
                df = pd.read_sql_query(query, conn, params=(ticker, start_date, end_date))
                
                if not df.empty:
                    df['date'] = pd.to_datetime(df['date'])
                    return df
                
        except Exception as e:
            logger.error(f"Error reading cached data: {str(e)}")
        
        return None
    
    def _store_data(self, ticker: str, data: pd.DataFrame) -> None:
        """Store data in local database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Prepare data for storage
                data_to_store = data.copy()
                data_to_store['ticker'] = ticker
                data_to_store['date'] = data_to_store['date'].dt.strftime('%Y-%m-%d')
                
                # Store in database
                data_to_store.to_sql('stock_data', conn, if_exists='append', index=False)
                
                # Update cache metadata
                data_hash = str(hash(str(data_to_store)))
                conn.execute("""
                    INSERT OR REPLACE INTO data_cache (ticker, last_updated, data_hash)
                    VALUES (?, ?, ?)
                """, (ticker, datetime.now().isoformat(), data_hash))
                
                conn.commit()
        except Exception as e:
            logger.error(f"Error storing data: {str(e)}")
    
    def get_latest_data(self, ticker: str, days: int = 30) -> pd.DataFrame:
        """Get the latest N days of data for a ticker."""
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        return self.fetch_data(ticker, start_date, end_date)
    
    def get_multiple_tickers(self, tickers: List[str], start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """Fetch data for multiple tickers."""
        results = {}
        
        for ticker in tickers:
            try:
                data = self.fetch_data(ticker, start_date, end_date)
                if not data.empty:
                    results[ticker] = data
                else:
                    logger.warning(f"No data available for {ticker}")
            except Exception as e:
                logger.error(f"Error fetching {ticker}: {str(e)}")
        
        return results
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """Validate that data meets minimum requirements."""
        if data.empty:
            return False
        
        required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        
        # Check columns
        if not all(col in data.columns for col in required_columns):
            return False
        
        # Check for missing values
        if data[required_columns].isnull().any().any():
            return False
        
        # Check for negative prices
        price_columns = ['open', 'high', 'low', 'close']
        if (data[price_columns] <= 0).any().any():
            return False
        
        # Check for negative volume
        if (data['volume'] < 0).any():
            return False
        
        return True
    
    def get_data_info(self, ticker: str) -> Dict[str, Any]:
        """Get information about available data for a ticker."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get date range
                date_range = conn.execute("""
                    SELECT MIN(date), MAX(date), COUNT(*) as count
                    FROM stock_data 
                    WHERE ticker = ?
                """, (ticker,)).fetchone()
                
                if date_range and date_range[0]:
                    return {
                        'ticker': ticker,
                        'start_date': date_range[0],
                        'end_date': date_range[1],
                        'total_records': date_range[2],
                        'available': True
                    }
                else:
                    return {
                        'ticker': ticker,
                        'available': False
                    }
                    
        except Exception as e:
            logger.error(f"Error getting data info for {ticker}: {str(e)}")
            return {
                'ticker': ticker,
                'available': False,
                'error': str(e)
            }
    
    def clear_cache(self, ticker: Optional[str] = None) -> None:
        """Clear cached data for a ticker or all tickers."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if ticker:
                    conn.execute("DELETE FROM stock_data WHERE ticker = ?", (ticker,))
                    conn.execute("DELETE FROM data_cache WHERE ticker = ?", (ticker,))
                    logger.info(f"Cleared cache for {ticker}")
                else:
                    conn.execute("DELETE FROM stock_data")
                    conn.execute("DELETE FROM data_cache")
                    logger.info("Cleared all cached data")
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
    
    def store_trade(self, trade_data: Dict[str, Any]) -> int:
        """
        Store a trade in the database.
        
        Args:
            trade_data: Dictionary containing trade information
            
        Returns:
            Trade ID
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = """
                    INSERT INTO trades (
                        ticker, strategy, entry_date, exit_date, entry_price, exit_price,
                        shares, pnl_pct, pnl_dollars, entry_reason, exit_reason, what_learned, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                cursor.execute(query, (
                    trade_data.get('ticker'),
                    trade_data.get('strategy'),
                    trade_data.get('entry_date'),
                    trade_data.get('exit_date'),
                    trade_data.get('entry_price'),
                    trade_data.get('exit_price'),
                    trade_data.get('shares'),
                    trade_data.get('pnl_pct'),
                    trade_data.get('pnl_dollars'),
                    trade_data.get('entry_reason'),
                    trade_data.get('exit_reason'),
                    trade_data.get('what_learned'),
                    trade_data.get('status', 'closed')
                ))
                
                trade_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Stored trade {trade_id} for {trade_data.get('ticker')}")
                return trade_id
                
        except Exception as e:
            logger.error(f"Error storing trade: {str(e)}")
            return -1
    
    def get_trades(self, ticker: str = None, strategy: str = None, 
                   start_date: str = None, end_date: str = None,
                   status: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve trades from the database with filtering options.
        
        Args:
            ticker: Filter by ticker symbol
            strategy: Filter by strategy name
            start_date: Filter by entry date (YYYY-MM-DD)
            end_date: Filter by entry date (YYYY-MM-DD)
            status: Filter by trade status ('open', 'closed')
            limit: Maximum number of trades to return
            
        Returns:
            List of trade dictionaries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM trades WHERE 1=1"
                params = []
                
                if ticker:
                    query += " AND ticker = ?"
                    params.append(ticker)
                
                if strategy:
                    query += " AND strategy = ?"
                    params.append(strategy)
                
                if start_date:
                    query += " AND entry_date >= ?"
                    params.append(start_date)
                
                if end_date:
                    query += " AND entry_date <= ?"
                    params.append(end_date)
                
                if status:
                    query += " AND status = ?"
                    params.append(status)
                
                query += " ORDER BY entry_date DESC LIMIT ?"
                params.append(limit)
                
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                columns = [description[0] for description in cursor.description]
                trades = []
                
                for row in cursor.fetchall():
                    trade = dict(zip(columns, row))
                    trades.append(trade)
                
                return trades
                
        except Exception as e:
            logger.error(f"Error retrieving trades: {str(e)}")
            return []
    
    def update_trade_learning(self, trade_id: int, what_learned: str) -> bool:
        """
        Update the "What I Learned" field for a trade.
        
        Args:
            trade_id: ID of the trade to update
            what_learned: Learning notes
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE trades 
                    SET what_learned = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (what_learned, trade_id))
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"Updated learning for trade {trade_id}")
                    return True
                else:
                    logger.warning(f"Trade {trade_id} not found")
                    return False
                    
        except Exception as e:
            logger.error(f"Error updating trade learning: {str(e)}")
            return False
    
    def get_trade_statistics(self, ticker: str = None, strategy: str = None,
                            start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """
        Get trade statistics for analysis.
        
        Args:
            ticker: Filter by ticker symbol
            strategy: Filter by strategy name
            start_date: Filter by entry date
            end_date: Filter by entry date
            
        Returns:
            Dictionary with trade statistics
        """
        try:
            trades = self.get_trades(ticker, strategy, start_date, end_date, limit=10000)
            
            if not trades:
                return {
                    'total_trades': 0,
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'win_rate': 0.0,
                    'avg_pnl_pct': 0.0,
                    'total_pnl_dollars': 0.0,
                    'best_trade_pct': 0.0,
                    'worst_trade_pct': 0.0
                }
            
            # Calculate statistics
            total_trades = len(trades)
            winning_trades = len([t for t in trades if t.get('pnl_pct', 0) > 0])
            losing_trades = len([t for t in trades if t.get('pnl_pct', 0) < 0])
            
            pnl_percentages = [t.get('pnl_pct', 0) for t in trades if t.get('pnl_pct') is not None]
            total_pnl_dollars = sum(t.get('pnl_dollars', 0) for t in trades)
            
            return {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': (winning_trades / total_trades * 100) if total_trades > 0 else 0.0,
                'avg_pnl_pct': sum(pnl_percentages) / len(pnl_percentages) if pnl_percentages else 0.0,
                'total_pnl_dollars': total_pnl_dollars,
                'best_trade_pct': max(pnl_percentages) if pnl_percentages else 0.0,
                'worst_trade_pct': min(pnl_percentages) if pnl_percentages else 0.0
            }
            
        except Exception as e:
            logger.error(f"Error calculating trade statistics: {str(e)}")
            return {} 