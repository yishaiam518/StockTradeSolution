#!/usr/bin/env python3
"""
OpenAI Analysis Storage System

This module provides persistent storage for OpenAI analysis results,
enabling incremental updates and delta processing to avoid redundant calculations.
"""

import sqlite3
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import pandas as pd

from src.utils.logger import get_logger

class OpenAIAnalysisStorage:
    """Persistent storage for OpenAI analysis results with incremental updates."""
    
    def __init__(self, db_path: str = "data/openai_analysis.db"):
        self.db_path = db_path
        self.logger = get_logger(__name__)
        self._init_database()
        
    def _init_database(self):
        """Initialize database with tables for OpenAI analysis storage."""
        with sqlite3.connect(self.db_path) as conn:
            # OpenAI analysis results table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS openai_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    collection_id TEXT NOT NULL,
                    analysis_date TEXT NOT NULL,
                    data_hash TEXT NOT NULL,
                    openai_score REAL,
                    analysis_text TEXT,
                    technical_insights TEXT,
                    recommendation TEXT,
                    confidence_level TEXT,
                    market_context TEXT,
                    technical_data_hash TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, collection_id, analysis_date)
                )
            ''')
            
            # Analysis metadata table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS analysis_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    collection_id TEXT NOT NULL,
                    analysis_date TEXT NOT NULL,
                    total_symbols INTEGER,
                    analyzed_symbols INTEGER,
                    failed_symbols INTEGER,
                    average_score REAL,
                    score_std_dev REAL,
                    processing_time REAL,
                    status TEXT DEFAULT 'completed',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(collection_id, analysis_date)
                )
            ''')
            
            # Delta tracking table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS analysis_deltas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    collection_id TEXT NOT NULL,
                    previous_analysis_date TEXT,
                    current_analysis_date TEXT,
                    score_change REAL,
                    recommendation_change TEXT,
                    confidence_change TEXT,
                    data_changed BOOLEAN,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for better performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_openai_symbol_date ON openai_analysis(symbol, analysis_date)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_openai_collection ON openai_analysis(collection_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_metadata_collection ON analysis_metadata(collection_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_deltas_symbol ON analysis_deltas(symbol)')
            
            conn.commit()
            
        self.logger.info(f"OpenAI analysis storage initialized at {self.db_path}")
    
    def store_analysis_result(self, symbol: str, collection_id: str, analysis_data: Dict, 
                            technical_data: Optional[Dict] = None, market_context: Optional[Dict] = None) -> bool:
        """Store OpenAI analysis result for a symbol."""
        try:
            analysis_date = datetime.now().strftime('%Y-%m-%d')
            
            # Create data hash for change detection
            data_hash = self._create_data_hash(technical_data, market_context)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO openai_analysis 
                    (symbol, collection_id, analysis_date, data_hash, openai_score, 
                     analysis_text, technical_insights, recommendation, confidence_level,
                     market_context, technical_data_hash, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol,
                    collection_id,
                    analysis_date,
                    data_hash,
                    analysis_data.get('score', 50.0),
                    analysis_data.get('analysis', ''),
                    analysis_data.get('technical_insights', ''),
                    analysis_data.get('recommendation', ''),
                    analysis_data.get('confidence_level', 'Medium'),
                    json.dumps(market_context) if market_context else None,
                    self._create_data_hash(technical_data) if technical_data else None,
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                
            self.logger.info(f"Stored OpenAI analysis for {symbol} in collection {collection_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing analysis for {symbol}: {e}")
            return False
    
    def get_latest_analysis(self, symbol: str, collection_id: str) -> Optional[Dict]:
        """Get the latest OpenAI analysis for a symbol."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT openai_score, analysis_text, technical_insights, 
                           recommendation, confidence_level, analysis_date, data_hash
                    FROM openai_analysis 
                    WHERE symbol = ? AND collection_id = ?
                    ORDER BY analysis_date DESC, updated_at DESC
                    LIMIT 1
                ''', (symbol, collection_id))
                
                result = cursor.fetchone()
                if result:
                    return {
                        'score': result[0],
                        'analysis': result[1],
                        'technical_insights': result[2],
                        'recommendation': result[3],
                        'confidence_level': result[4],
                        'analysis_date': result[5],
                        'data_hash': result[6]
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting analysis for {symbol}: {e}")
            return None
    
    def check_data_changed(self, symbol: str, collection_id: str, technical_data: Optional[Dict] = None, 
                          market_context: Optional[Dict] = None) -> bool:
        """Check if data has changed since last analysis."""
        try:
            current_hash = self._create_data_hash(technical_data, market_context)
            latest_analysis = self.get_latest_analysis(symbol, collection_id)
            
            if not latest_analysis:
                return True  # No previous analysis, consider as changed
            
            return current_hash != latest_analysis['data_hash']
            
        except Exception as e:
            self.logger.error(f"Error checking data change for {symbol}: {e}")
            return True  # Assume changed on error
    
    def get_symbols_needing_analysis(self, collection_id: str, symbols: List[str], 
                                   technical_data_dict: Dict[str, Dict] = None,
                                   market_context: Optional[Dict] = None) -> List[str]:
        """Get list of symbols that need fresh analysis."""
        try:
            symbols_needing_analysis = []
            
            for symbol in symbols:
                technical_data = technical_data_dict.get(symbol) if technical_data_dict else None
                
                if self.check_data_changed(symbol, collection_id, technical_data, market_context):
                    symbols_needing_analysis.append(symbol)
            
            self.logger.info(f"Found {len(symbols_needing_analysis)} symbols needing analysis out of {len(symbols)}")
            return symbols_needing_analysis
            
        except Exception as e:
            self.logger.error(f"Error determining symbols needing analysis: {e}")
            return symbols  # Return all symbols on error
    
    def store_analysis_metadata(self, collection_id: str, analysis_stats: Dict):
        """Store metadata about a collection analysis."""
        try:
            analysis_date = datetime.now().strftime('%Y-%m-%d')
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO analysis_metadata 
                    (collection_id, analysis_date, total_symbols, analyzed_symbols, 
                     failed_symbols, average_score, score_std_dev, processing_time, 
                     status, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    collection_id,
                    analysis_date,
                    analysis_stats.get('total_symbols', 0),
                    analysis_stats.get('analyzed_symbols', 0),
                    analysis_stats.get('failed_symbols', 0),
                    analysis_stats.get('average_score', 0.0),
                    analysis_stats.get('score_std_dev', 0.0),
                    analysis_stats.get('processing_time', 0.0),
                    analysis_stats.get('status', 'completed'),
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                
            self.logger.info(f"Stored analysis metadata for collection {collection_id}")
            
        except Exception as e:
            self.logger.error(f"Error storing analysis metadata: {e}")
    
    def calculate_deltas(self, collection_id: str, symbols: List[str]) -> List[Dict]:
        """Calculate deltas between current and previous analysis."""
        try:
            deltas = []
            analysis_date = datetime.now().strftime('%Y-%m-%d')
            previous_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            
            with sqlite3.connect(self.db_path) as conn:
                for symbol in symbols:
                    # Get current analysis
                    current = conn.execute('''
                        SELECT openai_score, recommendation, confidence_level, analysis_date
                        FROM openai_analysis 
                        WHERE symbol = ? AND collection_id = ? AND analysis_date = ?
                    ''', (symbol, collection_id, analysis_date)).fetchone()
                    
                    # Get previous analysis
                    previous = conn.execute('''
                        SELECT openai_score, recommendation, confidence_level, analysis_date
                        FROM openai_analysis 
                        WHERE symbol = ? AND collection_id = ? AND analysis_date = ?
                    ''', (symbol, collection_id, previous_date)).fetchone()
                    
                    if current and previous:
                        score_change = current[0] - previous[0]
                        recommendation_change = current[1] if current[1] != previous[1] else None
                        confidence_change = current[2] if current[2] != previous[2] else None
                        
                        delta = {
                            'symbol': symbol,
                            'collection_id': collection_id,
                            'previous_analysis_date': previous[3],
                            'current_analysis_date': current[3],
                            'score_change': score_change,
                            'recommendation_change': recommendation_change,
                            'confidence_change': confidence_change,
                            'data_changed': abs(score_change) > 5.0  # Significant change threshold
                        }
                        
                        deltas.append(delta)
                        
                        # Store delta in database
                        conn.execute('''
                            INSERT INTO analysis_deltas 
                            (symbol, collection_id, previous_analysis_date, current_analysis_date,
                             score_change, recommendation_change, confidence_change, data_changed)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            symbol, collection_id, previous[3], current[3],
                            score_change, recommendation_change, confidence_change, delta['data_changed']
                        ))
                
                conn.commit()
            
            self.logger.info(f"Calculated deltas for {len(deltas)} symbols")
            return deltas
            
        except Exception as e:
            self.logger.error(f"Error calculating deltas: {e}")
            return []
    
    def get_analysis_summary(self, collection_id: str, analysis_date: Optional[str] = None) -> Dict:
        """Get summary of analysis results for a collection."""
        try:
            if not analysis_date:
                analysis_date = datetime.now().strftime('%Y-%m-%d')
            
            with sqlite3.connect(self.db_path) as conn:
                # Get metadata
                metadata = conn.execute('''
                    SELECT total_symbols, analyzed_symbols, failed_symbols, 
                           average_score, score_std_dev, processing_time, status
                    FROM analysis_metadata 
                    WHERE collection_id = ? AND analysis_date = ?
                ''', (collection_id, analysis_date)).fetchone()
                
                # Get all analysis results
                results = conn.execute('''
                    SELECT symbol, openai_score, recommendation, confidence_level
                    FROM openai_analysis 
                    WHERE collection_id = ? AND analysis_date = ?
                    ORDER BY openai_score DESC
                ''', (collection_id, analysis_date)).fetchall()
                
                if metadata:
                    summary = {
                        'collection_id': collection_id,
                        'analysis_date': analysis_date,
                        'total_symbols': metadata[0],
                        'analyzed_symbols': metadata[1],
                        'failed_symbols': metadata[2],
                        'average_score': metadata[3],
                        'score_std_dev': metadata[4],
                        'processing_time': metadata[5],
                        'status': metadata[6],
                        'results': [
                            {
                                'symbol': r[0],
                                'openai_score': r[1],
                                'recommendation': r[2],
                                'confidence_level': r[3]
                            }
                            for r in results
                        ]
                    }
                    
                    return summary
                
                return {}
                
        except Exception as e:
            self.logger.error(f"Error getting analysis summary: {e}")
            return {}
    
    def _create_data_hash(self, technical_data: Optional[Dict] = None, 
                         market_context: Optional[Dict] = None) -> str:
        """Create hash of data for change detection."""
        try:
            data_string = ""
            
            if technical_data:
                # Convert numpy types to native Python types for JSON serialization
                converted_data = self._convert_numpy_types(technical_data)
                # Sort keys for consistent hashing
                sorted_data = json.dumps(converted_data, sort_keys=True)
                data_string += sorted_data
            
            if market_context:
                # Convert numpy types to native Python types for JSON serialization
                converted_context = self._convert_numpy_types(market_context)
                sorted_context = json.dumps(converted_context, sort_keys=True)
                data_string += sorted_context
            
            return hashlib.md5(data_string.encode()).hexdigest()
            
        except Exception as e:
            self.logger.error(f"Error creating data hash: {e}")
            return "error_hash"
    
    def _convert_numpy_types(self, data: Any) -> Any:
        """Convert numpy types to native Python types for JSON serialization."""
        import numpy as np
        
        if isinstance(data, dict):
            return {key: self._convert_numpy_types(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._convert_numpy_types(item) for item in data]
        elif isinstance(data, np.integer):
            return int(data)
        elif isinstance(data, np.floating):
            return float(data)
        elif isinstance(data, np.ndarray):
            return data.tolist()
        else:
            return data
    
    def cleanup_old_analyses(self, days_to_keep: int = 30):
        """Clean up old analysis data to save space."""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime('%Y-%m-%d')
            
            with sqlite3.connect(self.db_path) as conn:
                # Delete old analyses
                deleted_analyses = conn.execute('''
                    DELETE FROM openai_analysis 
                    WHERE analysis_date < ?
                ''', (cutoff_date,)).rowcount
                
                # Delete old metadata
                deleted_metadata = conn.execute('''
                    DELETE FROM analysis_metadata 
                    WHERE analysis_date < ?
                ''', (cutoff_date,)).rowcount
                
                # Delete old deltas
                deleted_deltas = conn.execute('''
                    DELETE FROM analysis_deltas 
                    WHERE current_analysis_date < ?
                ''', (cutoff_date,)).rowcount
                
                conn.commit()
            
            self.logger.info(f"Cleaned up {deleted_analyses} analyses, {deleted_metadata} metadata, {deleted_deltas} deltas")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old analyses: {e}") 