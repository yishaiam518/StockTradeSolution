#!/usr/bin/env python3
"""
Clear data cache and test GUI with fresh data.
"""

import sys
import os
import requests
import json
from datetime import datetime

# Add src to path
sys.path.append('src')

from src.data_engine.data_cache import DataCache
from src.utils.logger import get_logger

def clear_cache_and_test():
    """Clear the data cache and test the GUI."""
    
    logger = get_logger('clear_cache_test')
    logger.info("🧹 Clearing data cache...")
    
    try:
        # Initialize cache
        cache = DataCache()
        
        # Clear all cached data
        cache.clear_all_data()
        logger.info("✅ Cache cleared successfully")
        
        # Test the GUI API with fresh data
        logger.info("🔄 Testing GUI API with fresh data...")
        
        # Wait for dashboard to be ready
        import time
        time.sleep(5)
        
        # Test the historical backtest API
        response = requests.post(
            'http://localhost:8080/api/automation/historical-backtest',
            json={
                'start_date': '2023-01-01',
                'end_date': '2023-12-31',
                'strategy': 'macd_canonical',
                'profile': 'aggressive'
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            logger.info("✅ GUI API call successful")
            logger.info(f"📊 Trades returned: {len(data.get('trades', []))}")
            logger.info(f"📈 Unique symbols: {len(set(trade['symbol'] for trade in data.get('trades', [])))}")
            
            # Check for fractional shares
            fractional_shares = [t for t in data.get('trades', []) if t.get('shares', 0) % 1 != 0]
            logger.info(f"🔍 Trades with fractional shares: {len(fractional_shares)}")
            
            # Check for same buy/sell prices
            symbols = {}
            for trade in data.get('trades', []):
                symbol = trade['symbol']
                if symbol not in symbols:
                    symbols[symbol] = {'buys': [], 'sells': []}
                
                if trade['action'] == 'BUY':
                    symbols[symbol]['buys'].append(trade['price'])
                else:
                    symbols[symbol]['sells'].append(trade['price'])
            
            same_prices = 0
            for symbol, prices in symbols.items():
                if prices['buys'] and prices['sells']:
                    if any(buy in prices['sells'] for buy in prices['buys']):
                        same_prices += 1
            
            logger.info(f"🔍 Symbols with same buy/sell prices: {same_prices}")
            
            # Show sample trades
            logger.info("📋 Sample trades:")
            for i, trade in enumerate(data.get('trades', [])[:5]):
                logger.info(f"   {trade}")
            
        else:
            logger.error(f"❌ GUI API call failed: {response.status_code}")
            logger.error(f"Response: {response.text}")
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")

if __name__ == "__main__":
    clear_cache_and_test() 