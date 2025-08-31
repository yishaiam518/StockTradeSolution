import sqlite3
import logging
import json
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class PortfolioType(Enum):
    USER_MANAGED = "user_managed"
    AI_MANAGED = "ai_managed"

class TransactionType(Enum):
    BUY = "buy"
    SELL = "sell"

@dataclass
class Portfolio:
    id: int
    name: str
    portfolio_type: PortfolioType
    initial_cash: float
    current_cash: float
    created_at: datetime
    updated_at: datetime
    settings: Dict

@dataclass
class Position:
    id: int
    portfolio_id: int
    symbol: str
    shares: float
    avg_price: float
    current_price: float
    created_at: datetime
    updated_at: datetime

@dataclass
class Transaction:
    id: int
    portfolio_id: int
    symbol: str
    transaction_type: TransactionType
    shares: float
    price: float
    total_amount: float
    pnl: Optional[float] = None
    pnl_percentage: Optional[float] = None
    timestamp: datetime = None
    notes: Optional[str] = None

@dataclass
class DailyPerformance:
    id: int
    portfolio_id: int
    date: date
    total_value: float
    pnl: float
    return_pct: float
    cash: float
    positions_value: float

class PortfolioDatabase:
    def __init__(self, db_path: str = "data/portfolio.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._init_database()
    
    def _init_database(self):
        """Initialize the portfolio database with required tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create portfolios table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS portfolios (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        portfolio_type TEXT NOT NULL,
                        initial_cash REAL NOT NULL,
                        current_cash REAL NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        settings TEXT DEFAULT '{}'
                    )
                """)
                
                # Create positions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS portfolio_positions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        portfolio_id INTEGER NOT NULL,
                        symbol TEXT NOT NULL,
                        shares REAL NOT NULL,
                        avg_price REAL NOT NULL,
                        current_price REAL NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (portfolio_id) REFERENCES portfolios (id),
                        UNIQUE(portfolio_id, symbol)
                    )
                """)
                
                # Create transactions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS portfolio_transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        portfolio_id INTEGER NOT NULL,
                        symbol TEXT NOT NULL,
                        transaction_type TEXT NOT NULL,
                        shares REAL NOT NULL,
                        price REAL NOT NULL,
                        total_amount REAL NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        notes TEXT,
                        FOREIGN KEY (portfolio_id) REFERENCES portfolios (id)
                    )
                """)
                
                # Create daily performance table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS daily_performance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        portfolio_id INTEGER NOT NULL,
                        date DATE NOT NULL,
                        total_value REAL NOT NULL,
                        pnl REAL NOT NULL,
                        return_pct REAL NOT NULL,
                        cash REAL NOT NULL,
                        positions_value REAL NOT NULL,
                        FOREIGN KEY (portfolio_id) REFERENCES portfolios (id),
                        UNIQUE(portfolio_id, date)
                    )
                """)
                
                # Create algorithm decisions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS algorithm_decisions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        portfolio_id INTEGER NOT NULL,
                        symbol TEXT NOT NULL,
                        decision TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        factors TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (portfolio_id) REFERENCES portfolios (id)
                    )
                """)
                
                conn.commit()
                self.logger.info("Portfolio database initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Error initializing portfolio database: {e}")
            raise
    
    def create_portfolio(self, name: str, portfolio_type: PortfolioType, 
                        initial_cash: float, settings: Dict = None) -> int:
        """Create a new portfolio and return its ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                settings_json = json.dumps(settings or {})
                
                cursor.execute("""
                    INSERT INTO portfolios (name, portfolio_type, initial_cash, current_cash, settings)
                    VALUES (?, ?, ?, ?, ?)
                """, (name, portfolio_type.value, initial_cash, initial_cash, settings_json))
                
                portfolio_id = cursor.lastrowid
                conn.commit()
                
                self.logger.info(f"Created portfolio '{name}' with ID {portfolio_id}")
                return portfolio_id
                
        except Exception as e:
            self.logger.error(f"Error creating portfolio: {e}")
            raise
    
    def get_portfolio(self, portfolio_id: int) -> Optional[Portfolio]:
        """Get portfolio by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, name, portfolio_type, initial_cash, current_cash, 
                           created_at, updated_at, settings
                    FROM portfolios WHERE id = ?
                """, (portfolio_id,))
                
                row = cursor.fetchone()
                if row:
                    return Portfolio(
                        id=row[0],
                        name=row[1],
                        portfolio_type=PortfolioType(row[2]),
                        initial_cash=row[3],
                        current_cash=row[4],
                        created_at=datetime.fromisoformat(row[5]),
                        updated_at=datetime.fromisoformat(row[6]),
                        settings=json.loads(row[7]) if row[7] else {}
                    )
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting portfolio {portfolio_id}: {e}")
            raise
    
    def get_all_portfolios(self) -> List[Portfolio]:
        """Get all portfolios."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, name, portfolio_type, initial_cash, current_cash, 
                           created_at, updated_at, settings
                    FROM portfolios ORDER BY created_at DESC
                """)
                
                portfolios = []
                for row in cursor.fetchall():
                    portfolios.append(Portfolio(
                        id=row[0],
                        name=row[1],
                        portfolio_type=PortfolioType(row[2]),
                        initial_cash=row[3],
                        current_cash=row[4],
                        created_at=datetime.fromisoformat(row[5]),
                        updated_at=datetime.fromisoformat(row[6]),
                        settings=json.loads(row[7]) if row[7] else {}
                    ))
                
                return portfolios
                
        except Exception as e:
            self.logger.error(f"Error getting all portfolios: {e}")
            raise
    
    def add_transaction(self, portfolio_id: int, symbol: str, 
                       transaction_type: TransactionType, shares: float, 
                       price: float, notes: str = None) -> int:
        """Add a transaction to the portfolio."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                total_amount = shares * price
                
                # Calculate P&L for sell transactions
                pnl = None
                pnl_percentage = None
                if transaction_type == TransactionType.SELL:
                    # Get average buy price for this symbol
                    cursor.execute("""
                        SELECT avg_price FROM portfolio_positions 
                        WHERE portfolio_id = ? AND symbol = ?
                    """, (portfolio_id, symbol))
                    
                    result = cursor.fetchone()
                    if result:
                        avg_price = result[0]
                        # Calculate P&L: (Sell Price - Buy Price) × Shares
                        pnl = (price - avg_price) * shares
                        pnl_percentage = (pnl / (avg_price * shares)) * 100 if avg_price > 0 else 0
                
                cursor.execute("""
                    INSERT INTO portfolio_transactions 
                    (portfolio_id, symbol, transaction_type, shares, price, total_amount, pnl, pnl_percentage, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (portfolio_id, symbol, transaction_type.value, shares, price, 
                     total_amount, pnl, pnl_percentage, notes))
                
                transaction_id = cursor.lastrowid
                
                # Update portfolio cash
                if transaction_type == TransactionType.BUY:
                    cursor.execute("""
                        UPDATE portfolios SET current_cash = current_cash - ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (total_amount, portfolio_id))
                else:  # SELL
                    cursor.execute("""
                        UPDATE portfolios SET current_cash = current_cash + ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (total_amount, portfolio_id))
                
                conn.commit()
                
                self.logger.info(f"Added {transaction_type.value} transaction for {symbol} in portfolio {portfolio_id}")
                return transaction_id
                
        except Exception as e:
            self.logger.error(f"Error adding transaction: {e}")
            raise
    
    def update_position(self, portfolio_id: int, symbol: str, 
                       shares: float, price: float) -> None:
        """Update or create a position."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if position exists
                cursor.execute("""
                    SELECT shares, avg_price FROM portfolio_positions 
                    WHERE portfolio_id = ? AND symbol = ?
                """, (portfolio_id, symbol))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing position
                    current_shares, current_avg_price = existing
                    new_shares = current_shares + shares
                    
                    if new_shares <= 0:
                        # Remove position if shares <= 0
                        cursor.execute("""
                            DELETE FROM portfolio_positions 
                            WHERE portfolio_id = ? AND symbol = ?
                        """, (portfolio_id, symbol))
                    else:
                        # Update position
                        new_avg_price = ((current_shares * current_avg_price) + (shares * price)) / new_shares
                        
                        cursor.execute("""
                            UPDATE portfolio_positions 
                            SET shares = ?, avg_price = ?, current_price = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE portfolio_id = ? AND symbol = ?
                        """, (new_shares, new_avg_price, price, portfolio_id, symbol))
                else:
                    # Create new position
                    
                    cursor.execute("""
                        INSERT INTO portfolio_positions 
                        (portfolio_id, symbol, shares, avg_price, current_price)
                        VALUES (?, ?, ?, ?, ?)
                    """, (portfolio_id, symbol, shares, price, price))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error updating position: {e}")
            raise
    
    def update_position_current_price(self, portfolio_id: int, symbol: str, current_price: float) -> None:
        """Update only the current price of a position without affecting shares or avg_price."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE portfolio_positions 
                    SET current_price = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE portfolio_id = ? AND symbol = ?
                """, (current_price, portfolio_id, symbol))
                
                if cursor.rowcount == 0:
                    self.logger.warning(f"No position found to update: portfolio {portfolio_id}, symbol {symbol}")
                else:
                    self.logger.info(f"Updated current price for {symbol} to ${current_price:.2f}")
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error updating position current price: {e}")
            raise
    
    def get_portfolio_positions(self, portfolio_id: int) -> List[Position]:
        """Get all positions for a portfolio."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, portfolio_id, symbol, shares, avg_price, current_price, 
                           created_at, updated_at
                    FROM portfolio_positions 
                    WHERE portfolio_id = ?
                    ORDER BY symbol
                """, (portfolio_id,))
                
                positions = []
                for row in cursor.fetchall():
                    positions.append(Position(
                        id=row[0],
                        portfolio_id=row[1],
                        symbol=row[2],
                        shares=row[3],
                        avg_price=row[4],
                        current_price=row[5],
                        created_at=datetime.fromisoformat(row[6]),
                        updated_at=datetime.fromisoformat(row[7])
                    ))
                
                return positions
                
        except Exception as e:
            self.logger.error(f"Error getting portfolio positions: {e}")
            raise
    
    def get_portfolio_transactions(self, portfolio_id: int, 
                                 limit: int = 100) -> List[Transaction]:
        """Get recent transactions for a portfolio."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, portfolio_id, symbol, transaction_type, shares, price, 
                           total_amount, pnl, pnl_percentage, timestamp, notes
                    FROM portfolio_transactions 
                    WHERE portfolio_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (portfolio_id, limit))
                
                transactions = []
                for row in cursor.fetchall():
                    transactions.append(Transaction(
                        id=row[0],
                        portfolio_id=row[1],
                        symbol=row[2],
                        transaction_type=TransactionType(row[3]),
                        shares=row[4],
                        price=row[5],
                        total_amount=row[6],
                        pnl=row[7],
                        pnl_percentage=row[8],
                        timestamp=datetime.fromisoformat(row[9]),
                        notes=row[10]
                    ))
                
                return transactions
                
        except Exception as e:
            self.logger.error(f"Error getting portfolio transactions: {e}")
            raise
    
    def record_daily_performance(self, portfolio_id: int, date: date, 
                                total_value: float, pnl: float, 
                                return_pct: float, cash: float, 
                                positions_value: float) -> None:
        """Record daily performance snapshot."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO daily_performance 
                    (portfolio_id, date, total_value, pnl, return_pct, cash, positions_value)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (portfolio_id, date.isoformat(), total_value, pnl, 
                     return_pct, cash, positions_value))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error recording daily performance: {e}")
            raise
    
    def get_portfolio_performance_history(self, portfolio_id: int, 
                                        days: int = 30) -> List[DailyPerformance]:
        """Get performance history for a portfolio."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, portfolio_id, date, total_value, pnl, return_pct, cash, positions_value
                    FROM daily_performance 
                    WHERE portfolio_id = ?
                    ORDER BY date DESC
                    LIMIT ?
                """, (portfolio_id, days))
                
                performances = []
                for row in cursor.fetchall():
                    performances.append(DailyPerformance(
                        id=row[0],
                        portfolio_id=row[1],
                        date=date.fromisoformat(row[2]),
                        total_value=row[3],
                        pnl=row[4],
                        return_pct=row[5],
                        cash=row[6],
                        positions_value=row[7]
                    ))
                
                return performances
                
        except Exception as e:
            self.logger.error(f"Error getting performance history: {e}")
            raise
    
    def record_algorithm_decision(self, portfolio_id: int, symbol: str, 
                                decision: str, confidence: float, 
                                factors: Dict) -> None:
        """Record an algorithm decision."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                factors_json = str(factors)
                
                cursor.execute("""
                    INSERT INTO algorithm_decisions 
                    (portfolio_id, symbol, decision, confidence, factors)
                    VALUES (?, ?, ?, ?, ?)
                """, (portfolio_id, symbol, decision, confidence, factors_json))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error recording algorithm decision: {e}")
            raise 