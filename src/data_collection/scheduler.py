"""
Data Scheduler for the SMART STOCK TRADING SYSTEM.

Handles:
- Scheduled daily data updates
- Real-time position monitoring
- Automated data collection tasks
"""

import schedule
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
import logging

from src.utils.logger import logger
from .collector import DataCollector


class DataScheduler:
    """Scheduler for automated data collection tasks."""
    
    def __init__(self, collector: Optional[DataCollector] = None):
        """Initialize the data scheduler."""
        self.collector = collector or DataCollector()
        self.running = False
        self.scheduler_thread = None
        self.callbacks = {
            'daily_update': [],
            'realtime_update': [],
            'error': []
        }
        
        logger.info("Data Scheduler initialized")
    
    def start(self):
        """Start the scheduler."""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        self.running = True
        
        # Schedule daily updates at market close (4:00 PM ET)
        schedule.every().day.at("16:00").do(self._daily_update_task)
        
        # Schedule real-time updates every 5 minutes during market hours
        schedule.every(5).minutes.do(self._realtime_update_task)
        
        # Start scheduler in a separate thread
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Data Scheduler started")
    
    def stop(self):
        """Stop the scheduler."""
        if not self.running:
            logger.warning("Scheduler is not running")
            return
        
        self.running = False
        schedule.clear()
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        logger.info("Data Scheduler stopped")
    
    def _run_scheduler(self):
        """Run the scheduler loop."""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}")
                self._notify_callbacks('error', str(e))
    
    def _daily_update_task(self):
        """Daily data update task."""
        try:
            logger.info("Starting scheduled daily data update")
            
            # Get active positions for real-time monitoring
            active_positions = self._get_active_positions()
            
            # Update all data
            updated_data = self.collector.update_daily_data()
            
            # Update real-time data for active positions
            if active_positions:
                realtime_data = self.collector.get_realtime_data(active_positions)
            
            logger.info(f"Daily update completed. Updated {len(updated_data)} symbols")
            self._notify_callbacks('daily_update', updated_data)
            
        except Exception as e:
            logger.error(f"Error in daily update task: {str(e)}")
            self._notify_callbacks('error', str(e))
    
    def _realtime_update_task(self):
        """Real-time update task for active positions."""
        try:
            # Only run during market hours
            if not self._is_market_hours():
                return
            
            active_positions = self._get_active_positions()
            
            if active_positions:
                logger.debug(f"Updating real-time data for {len(active_positions)} active positions")
                realtime_data = self.collector.get_realtime_data(active_positions)
                self._notify_callbacks('realtime_update', realtime_data)
            
        except Exception as e:
            logger.error(f"Error in real-time update task: {str(e)}")
            self._notify_callbacks('error', str(e))
    
    def _get_active_positions(self) -> List[str]:
        """Get list of active positions for real-time monitoring."""
        # This would typically come from the portfolio manager
        # For now, return an empty list
        return []
    
    def _is_market_hours(self) -> bool:
        """Check if it's currently market hours."""
        now = datetime.now()
        
        # Simple check for market hours (9:30 AM - 4:00 PM ET)
        # In production, this should use proper timezone handling
        market_start = now.replace(hour=9, minute=30, second=0, microsecond=0)
        market_end = now.replace(hour=16, minute=0, second=0, microsecond=0)
        
        return market_start <= now <= market_end
    
    def add_callback(self, event_type: str, callback: Callable):
        """Add a callback for scheduler events."""
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)
            logger.debug(f"Added callback for {event_type}")
        else:
            logger.warning(f"Unknown event type: {event_type}")
    
    def _notify_callbacks(self, event_type: str, data):
        """Notify all callbacks for an event."""
        if event_type in self.callbacks:
            for callback in self.callbacks[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Error in callback for {event_type}: {str(e)}")
    
    def get_scheduler_status(self) -> Dict:
        """Get the current status of the scheduler."""
        return {
            'running': self.running,
            'next_daily_update': schedule.next_run(),
            'active_positions': self._get_active_positions(),
            'market_hours': self._is_market_hours()
        }
    
    def manual_daily_update(self):
        """Manually trigger a daily update."""
        logger.info("Manual daily update triggered")
        self._daily_update_task()
    
    def manual_realtime_update(self):
        """Manually trigger a real-time update."""
        logger.info("Manual real-time update triggered")
        self._realtime_update_task() 