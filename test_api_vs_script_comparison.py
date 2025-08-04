#!/usr/bin/env python3
"""
Test to compare GUI API results with script results for historical backtesting.
This will help identify why the GUI shows different results than our test script.
"""

import requests
import json
import pandas as pd
from datetime import datetime
import sys
import os

# Add src to path
sys.path.append('src')

from src.backtesting.backtest_engine import BacktestEngine
from src.data_engine.data_cache import DataCache
from src.utils.logger import get_logger

def test_gui_api_vs_script():
    """Compare GUI API results with direct script execution."""
    
    logger = get_logger('test_comparison')
    logger.info("🔍 Starting GUI API vs Script comparison test")
    
    # Test parameters (same as GUI)
    start_date = "2023-01-01"
    end_date = "2023-12-31"
    strategy = "macd_canonical"
    profile = "aggressive"
    
    logger.info(f"📊 Test Parameters:")
    logger.info(f"   Start Date: {start_date}")
    logger.info(f"   End Date: {end_date}")
    logger.info(f"   Strategy: {strategy}")
    logger.info(f"   Profile: {profile}")
    
    # 1. Call GUI API
    logger.info("\n🌐 Calling GUI API...")
    try:
        api_url = "http://localhost:8080/api/automation/historical-backtest"
        payload = {
            "start_date": start_date,
            "end_date": end_date,
            "strategy": strategy,
            "profile": profile
        }
        
        response = requests.post(api_url, json=payload, timeout=60)
        logger.info(f"   API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            api_result = response.json()
            logger.info("   ✅ API call successful")
            
            # Extract trades from API response
            if 'trades' in api_result:
                api_trades = api_result['trades']
                logger.info(f"   📈 API returned {len(api_trades)} trades")
                
                # Convert to DataFrame for analysis
                api_df = pd.DataFrame(api_trades)
                logger.info(f"   📊 API trades columns: {list(api_df.columns)}")
                
                # Analyze API trades
                logger.info("\n📊 API Trades Analysis:")
                logger.info(f"   Unique symbols: {api_df['symbol'].nunique()}")
                logger.info(f"   Buy trades: {len(api_df[api_df['action'] == 'BUY'])}")
                logger.info(f"   Sell trades: {len(api_df[api_df['action'] == 'SELL'])}")
                
                # Check for issues
                if 'price' in api_df.columns and 'value' in api_df.columns:
                    # Check for same buy/sell prices
                    same_prices = api_df.groupby('symbol').apply(
                        lambda x: len(x[x['action'] == 'BUY']) == len(x[x['action'] == 'SELL']) and
                        all(x[x['action'] == 'BUY']['price'].values == x[x['action'] == 'SELL']['price'].values)
                    )
                    logger.info(f"   🔍 Symbols with same buy/sell prices: {same_prices.sum()}")
                
                # Check for fractional shares
                if 'shares' in api_df.columns:
                    fractional_shares = (api_df['shares'] % 1 != 0).sum()
                    logger.info(f"   🔍 Trades with fractional shares: {fractional_shares}")
                
                # Show sample of API trades
                logger.info("\n📋 Sample API Trades:")
                for i, trade in enumerate(api_trades[:5]):
                    logger.info(f"   {trade}")
                    
            else:
                logger.error("   ❌ No 'trades' key in API response")
                logger.info(f"   API Response keys: {list(api_result.keys())}")
                
        else:
            logger.error(f"   ❌ API call failed: {response.status_code}")
            logger.error(f"   Response: {response.text}")
            
    except Exception as e:
        logger.error(f"   ❌ API call error: {e}")
    
    # 2. Run direct script execution
    logger.info("\n🔧 Running direct script execution...")
    try:
        # Initialize components
        cache = DataCache()
        backtest_engine = BacktestEngine()
        
        # Run backtest
        result = backtest_engine.run_historical_backtest(
            strategy=strategy,
            profile=profile,
            start_date=start_date,
            end_date=end_date
        )
        
        logger.info("   ✅ Script execution successful")
        
        # Extract trades from script result
        if 'trades' in result:
            script_trades = result['trades']
            logger.info(f"   📈 Script returned {len(script_trades)} trades")
            
            # Convert to DataFrame for analysis
            script_df = pd.DataFrame(script_trades)
            logger.info(f"   📊 Script trades columns: {list(script_df.columns)}")
            
            # Analyze script trades
            logger.info("\n📊 Script Trades Analysis:")
            logger.info(f"   Unique symbols: {script_df['symbol'].nunique()}")
            logger.info(f"   Buy trades: {len(script_df[script_df['action'] == 'BUY'])}")
            logger.info(f"   Sell trades: {len(script_df[script_df['action'] == 'SELL'])}")
            
            # Check for issues
            if 'price' in script_df.columns and 'value' in script_df.columns:
                # Check for same buy/sell prices
                same_prices = script_df.groupby('symbol').apply(
                    lambda x: len(x[x['action'] == 'BUY']) == len(x[x['action'] == 'SELL']) and
                    all(x[x['action'] == 'BUY']['price'].values == x[x['action'] == 'SELL']['price'].values)
                )
                logger.info(f"   🔍 Symbols with same buy/sell prices: {same_prices.sum()}")
            
            # Check for fractional shares
            if 'shares' in script_df.columns:
                fractional_shares = (script_df['shares'] % 1 != 0).sum()
                logger.info(f"   🔍 Trades with fractional shares: {fractional_shares}")
            
            # Show sample of script trades
            logger.info("\n📋 Sample Script Trades:")
            for i, trade in enumerate(script_trades[:5]):
                logger.info(f"   {trade}")
                
        else:
            logger.error("   ❌ No 'trades' key in script result")
            logger.info(f"   Script Result keys: {list(result.keys())}")
            
    except Exception as e:
        logger.error(f"   ❌ Script execution error: {e}")
        import traceback
        logger.error(f"   Traceback: {traceback.format_exc()}")
    
    # 3. Compare results
    logger.info("\n🔍 Comparing Results...")
    
    if 'api_df' in locals() and 'script_df' in locals():
        logger.info(f"   📊 API trades count: {len(api_df)}")
        logger.info(f"   📊 Script trades count: {len(script_df)}")
        
        # Compare key metrics
        if len(api_df) > 0 and len(script_df) > 0:
            logger.info("\n📈 Key Differences:")
            
            # Compare unique symbols
            api_symbols = set(api_df['symbol'].unique())
            script_symbols = set(script_df['symbol'].unique())
            logger.info(f"   API unique symbols: {len(api_symbols)}")
            logger.info(f"   Script unique symbols: {len(script_symbols)}")
            logger.info(f"   Symbols only in API: {api_symbols - script_symbols}")
            logger.info(f"   Symbols only in Script: {script_symbols - api_symbols}")
            
            # Compare trade counts
            api_buys = len(api_df[api_df['action'] == 'BUY'])
            api_sells = len(api_df[api_df['action'] == 'SELL'])
            script_buys = len(script_df[script_df['action'] == 'BUY'])
            script_sells = len(script_df[script_df['action'] == 'SELL'])
            
            logger.info(f"   API - Buys: {api_buys}, Sells: {api_sells}")
            logger.info(f"   Script - Buys: {script_buys}, Sells: {script_sells}")
            
            # Compare price ranges
            if 'price' in api_df.columns and 'price' in script_df.columns:
                api_price_range = (api_df['price'].min(), api_df['price'].max())
                script_price_range = (script_df['price'].min(), script_df['price'].max())
                logger.info(f"   API price range: {api_price_range}")
                logger.info(f"   Script price range: {script_price_range}")
            
            # Compare share ranges
            if 'shares' in api_df.columns and 'shares' in script_df.columns:
                api_share_range = (api_df['shares'].min(), api_df['shares'].max())
                script_share_range = (script_df['shares'].min(), script_df['shares'].max())
                logger.info(f"   API share range: {api_share_range}")
                logger.info(f"   Script share range: {script_share_range}")
    
    logger.info("\n✅ Comparison test completed")

if __name__ == "__main__":
    test_gui_api_vs_script() 