#!/usr/bin/env python3
"""
Daily Data Collection System

Runs daily to collect and update all stock data before trading operations.
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any
import schedule
import time

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.data_collection.collector import DataCollector
from src.data_engine.data_cache import DataCache
from src.utils.logger import get_logger

class DailyDataCollector:
    """Daily data collection system for updating all stock data."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.collector = DataCollector()
        self.cache = DataCache()
        
        # Get all symbols to update daily
        self.all_symbols = self._get_all_tracked_symbols()
        
    def _get_all_tracked_symbols(self) -> List[str]:
        """Get all symbols that should be updated daily."""
        # Core portfolio symbols
        core_symbols = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX',
            'SPY', 'QQQ', 'VTI', 'VOO', 'VEA', 'VWO', 'BND', 'GLD', 'SLV',
            'JPM', 'JNJ', 'PG', 'UNH', 'HD', 'MA', 'V', 'PYPL', 'ADBE',
            'CRM', 'NKE', 'DIS', 'PFE', 'ABT', 'TMO', 'ABBV', 'LLY', 'AVGO',
            'PEP', 'COST', 'WMT', 'MCD', 'SBUX', 'KO', 'PEP', 'TXN', 'QCOM',
            'INTC', 'AMD', 'ORCL', 'CSCO', 'IBM', 'ACN', 'ADP', 'INTU'
        ]
        
        # Add any additional symbols from cache
        cached_symbols = self.cache.get_cached_symbols()
        all_symbols = list(set(core_symbols + cached_symbols))
        
        self.logger.info(f"📊 Daily collection will update {len(all_symbols)} symbols")
        return all_symbols
    
    def collect_daily_data(self) -> Dict[str, Any]:
        """Collect and update all stock data for the current day."""
        self.logger.info("🔄 Starting daily data collection...")
        
        start_time = datetime.now()
        results = {
            'start_time': start_time,
            'symbols_updated': 0,
            'symbols_failed': 0,
            'errors': [],
            'end_time': None
        }
        
        for symbol in self.all_symbols:
            try:
                self.logger.info(f"📈 Updating data for {symbol}...")
                
                # Get data for the last 2 years to ensure we have recent data
                end_date = datetime.now()
                start_date = datetime.now() - timedelta(days=730)
                
                # Collect fresh data
                data = self.collector._fetch_historical_data(symbol, start_date, end_date)
                
                if data is not None and not data.empty:
                    # Cache the updated data
                    self.cache.cache_data(symbol, data, start_date, end_date)
                    results['symbols_updated'] += 1
                    self.logger.info(f"✅ {symbol} updated successfully")
                else:
                    results['symbols_failed'] += 1
                    self.logger.warning(f"⚠️  {symbol} - No data received")
                    
            except Exception as e:
                results['symbols_failed'] += 1
                results['errors'].append(f"{symbol}: {str(e)}")
                self.logger.error(f"❌ Error updating {symbol}: {str(e)}")
        
        results['end_time'] = datetime.now()
        duration = (results['end_time'] - results['start_time']).total_seconds()
        
        self.logger.info(f"🎯 Daily collection completed in {duration:.2f}s")
        self.logger.info(f"📊 Results: {results['symbols_updated']} updated, {results['symbols_failed']} failed")
        
        return results
    
    def run_daily_job(self):
        """Run the daily data collection job."""
        self.logger.info("🌅 Starting daily data collection job...")
        results = self.collect_daily_data()
        
        # Log summary
        self.logger.info("📋 Daily Collection Summary:")
        self.logger.info(f"   - Symbols Updated: {results['symbols_updated']}")
        self.logger.info(f"   - Symbols Failed: {results['symbols_failed']}")
        self.logger.info(f"   - Duration: {(results['end_time'] - results['start_time']).total_seconds():.2f}s")
        
        if results['errors']:
            self.logger.error("❌ Errors encountered:")
            for error in results['errors'][:5]:  # Show first 5 errors
                self.logger.error(f"   - {error}")
        
        return results

def main():
    """Main function to run daily data collection."""
    collector = DailyDataCollector()
    collector.run_daily_job()

if __name__ == "__main__":
    main() 