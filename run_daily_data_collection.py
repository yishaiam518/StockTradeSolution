#!/usr/bin/env python3
"""
Daily Data Collection Job

Standalone script to run daily data collection for all tracked symbols.
This job should be scheduled to run daily (e.g., via cron) before any trading operations.

Usage:
    python run_daily_data_collection.py
"""

import sys
import os
import schedule
import time
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.data_collection.daily_collector import DailyDataCollector
from src.utils.logger import get_logger

def run_daily_job():
    """Run the daily data collection job."""
    logger = get_logger(__name__)
    
    logger.info("🌅 Starting Daily Data Collection Job")
    logger.info("=" * 50)
    
    try:
        # Initialize the daily collector
        collector = DailyDataCollector()
        
        # Run the collection
        results = collector.run_daily_job()
        
        # Log final summary
        logger.info("=" * 50)
        logger.info("✅ Daily Data Collection Job Completed")
        logger.info(f"📊 Summary:")
        logger.info(f"   - Symbols Updated: {results['symbols_updated']}")
        logger.info(f"   - Symbols Failed: {results['symbols_failed']}")
        logger.info(f"   - Duration: {(results['end_time'] - results['start_time']).total_seconds():.2f}s")
        
        if results['errors']:
            logger.error(f"❌ Errors: {len(results['errors'])}")
            for error in results['errors'][:3]:  # Show first 3 errors
                logger.error(f"   - {error}")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Fatal error in daily data collection: {str(e)}")
        return {'error': str(e)}

def schedule_daily_job():
    """Schedule the daily job to run at 6:00 AM every day."""
    logger = get_logger(__name__)
    
    logger.info("📅 Scheduling daily data collection job for 6:00 AM")
    schedule.every().day.at("06:00").do(run_daily_job)
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Daily Data Collection Job')
    parser.add_argument('--run-now', action='store_true', 
                       help='Run the job immediately instead of scheduling')
    parser.add_argument('--schedule', action='store_true',
                       help='Schedule the job to run daily at 6:00 AM')
    
    args = parser.parse_args()
    
    if args.run_now:
        # Run immediately
        run_daily_job()
    elif args.schedule:
        # Schedule the job
        schedule_daily_job()
    else:
        # Default: run immediately
        run_daily_job()

if __name__ == "__main__":
    main() 