#!/usr/bin/env python3
"""
Data Collection Scheduler
Handles automated updates for data collections.
"""

import logging
import schedule
import threading
import time
from datetime import datetime, time as dt_time
from typing import Dict, List, Optional
from .data_manager import DataCollectionManager
import pytz


class CollectionScheduler:
    """Individual scheduler for a specific collection."""
    
    def __init__(self, collection_id: str, data_manager: DataCollectionManager):
        self.collection_id = collection_id
        self.data_manager = data_manager
        self.logger = logging.getLogger(__name__)
        self.scheduler_thread = None
        self.is_running = False
        # Hands-off AI automation controls
        self.auto_execute_ai_trades = True
        # Default AI portfolio id (created at app bootstrap). Can be made configurable later.
        self.ai_portfolio_id = 2

        # Market window controls from config
        from src.utils.config_loader import config as global_config
        window_cfg = (global_config.get('data_collection.scheduler_window') or {})
        self.skip_outside_window = bool(window_cfg.get('enabled', True))
        self.market_timezone = window_cfg.get('timezone', 'America/New_York')
        start_str = window_cfg.get('start', '09:30')
        end_str = window_cfg.get('end', '16:00')
        try:
            start_h, start_m = [int(x) for x in start_str.split(':')]
            end_h, end_m = [int(x) for x in end_str.split(':')]
        except Exception:
            start_h, start_m, end_h, end_m = 9, 30, 16, 0
        self.active_window_start = dt_time(hour=start_h, minute=start_m)
        self.active_window_end = dt_time(hour=end_h, minute=end_m)
        w = window_cfg.get('weekdays', [1,2,3,4,5])
        # Convert to Python weekday 0-6 (Mon=0) from 1-7
        self.active_weekdays = { (d-1) % 7 for d in w }
        
        # Get interval from database or default to 24h
        collection_details = data_manager.get_collection_details(collection_id)
        if collection_details and collection_details.get('auto_update'):
            # Try to get interval from database, default to 24h
            self.update_interval = collection_details.get('update_interval', '24h')
        else:
            self.update_interval = "24h"  # Default interval
        
        # Available intervals for testing
        self.available_intervals = {
            "1min": "1 minute",
            "5min": "5 minutes",
            "10min": "10 minutes", 
            "30min": "30 minutes",
            "1h": "1 hour",
            "24h": "24 hours"
        }
        
        # Track last run and next run times
        self.last_run = None
        self.next_run = None
    
    def set_update_interval(self, interval: str) -> bool:
        """Set the update interval for this collection."""
        if interval in self.available_intervals:
            self.update_interval = interval
            self.logger.info(f"Collection {self.collection_id} interval set to: {self.available_intervals[interval]}")
            return True
        else:
            self.logger.error(f"Invalid interval: {interval}. Available: {list(self.available_intervals.keys())}")
            return False
    
    def get_available_intervals(self):
        """Get list of available intervals."""
        return self.available_intervals
    
    def get_current_interval(self):
        """Get current update interval."""
        return self.update_interval
    
    def start_scheduler(self):
        """Start the scheduler for this collection."""
        if self.is_running:
            self.logger.warning(f"Scheduler for collection {self.collection_id} is already running")
            return False
        
        # Set initial last_run time when scheduler starts
        from datetime import datetime
        self.last_run = datetime.now()
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        self.logger.info(f"Started scheduler for collection {self.collection_id}")
        return True
    
    def stop_scheduler(self):
        """Stop the scheduler for this collection."""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        self.logger.info(f"Stopped scheduler for collection {self.collection_id}")
    
    def _run_scheduler(self):
        """Run the scheduler loop for this collection."""
        # Clear any existing schedules
        schedule.clear()
        
        # Calculate next run time based on interval
        self._calculate_next_run()
        
        # Schedule based on the current interval
        if self.update_interval == "1min":
            schedule.every(1).minutes.do(self._update_collection)
        elif self.update_interval == "5min":
            schedule.every(5).minutes.do(self._update_collection)
        elif self.update_interval == "10min":
            schedule.every(10).minutes.do(self._update_collection)
        elif self.update_interval == "30min":
            schedule.every(30).minutes.do(self._update_collection)
        elif self.update_interval == "1h":
            schedule.every().hour.do(self._update_collection)
        elif self.update_interval == "24h":
            schedule.every().day.at("18:00").do(self._update_collection)
        
        self.logger.info(f"Collection {self.collection_id} scheduler configured with interval: {self.available_intervals[self.update_interval]}")
        
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            # Don't recalculate next run time here - it should only be calculated once at start
    
    def _calculate_next_run(self):
        """Calculate the next run time based on current interval."""
        from datetime import datetime, timedelta
        
        now = datetime.now()
        
        if self.update_interval == "1min":
            # Next run in 1 minute from now
            self.next_run = now + timedelta(minutes=1)
        elif self.update_interval == "5min":
            # Next run in 5 minutes from now
            self.next_run = now + timedelta(minutes=5)
        elif self.update_interval == "10min":
            self.next_run = now + timedelta(minutes=10)
        elif self.update_interval == "30min":
            self.next_run = now + timedelta(minutes=30)
        elif self.update_interval == "1h":
            self.next_run = now + timedelta(hours=1)
        elif self.update_interval == "24h":
            # Next run at 18:00 today or tomorrow
            next_run = now.replace(hour=18, minute=0, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            self.next_run = next_run
    
    def _update_collection(self):
        """Update this specific collection and calculate technical indicators."""
        try:
            self.logger.info(f"Running scheduled update for collection {self.collection_id}")
            self.last_run = datetime.now()
            
            # If configured, skip actual data updates outside market hours
            if self.skip_outside_window and not self._is_within_active_window():
                self.logger.info(
                    f"⏸️ Outside active market window ({self.active_window_start.strftime('%H:%M')} - "
                    f"{self.active_window_end.strftime('%H:%M')} {self.market_timezone}). Skipping data update."
                )
                # Still update next/last run bookkeeping so UI status looks alive
                self.last_result = {
                    'success': True,
                    'skipped_due_to_market_window': True,
                    'timestamp': self.last_run.isoformat()
                }
                self._update_database_times()
                return
            
            result = self.data_manager.update_collection(self.collection_id)
            
            if result.get('success'):
                self.logger.info(f"Collection {self.collection_id} updated successfully: {result.get('updated_symbols', 0)} symbols updated")
                
                # Calculate technical indicators for all symbols in this collection
                self._calculate_technical_indicators()
                
                # Trigger AI ranking recalculation with new data
                self._trigger_ai_ranking_recalculation()

                # Optionally execute AI-managed portfolio trades based on fresh rankings
                ai_actions = None
                if self.auto_execute_ai_trades:
                    ai_actions = self._execute_ai_portfolio_trades()
                
                # Store result for status reporting
                self.last_result = {
                    'success': True,
                    'updated_symbols': result.get('updated_symbols', 0),
                    'failed_symbols': result.get('failed_symbols', 0),
                    'indicators_calculated': True,
                    'ai_ranking_updated': True,
                    'ai_trades_executed': bool(ai_actions),
                    'ai_actions_taken': (ai_actions or {}).get('actions_taken') if isinstance(ai_actions, dict) else None,
                    'timestamp': self.last_run.isoformat()
                }
            else:
                self.logger.error(f"Failed to update collection {self.collection_id}: {result.get('error', 'Unknown error')}")
                self.last_result = {
                    'success': False,
                    'error': result.get('error', 'Unknown error'),
                    'timestamp': self.last_run.isoformat()
                }
            
            # Update the database with new last_run and next_run times
            self._update_database_times()
                
        except Exception as e:
            self.logger.error(f"Error updating collection {self.collection_id}: {e}")
            self.last_run = datetime.now()
            self.last_result = {
                'success': False,
                'error': str(e),
                'timestamp': self.last_run.isoformat()
            }
            # Still update database times even if update failed
            self._update_database_times()
    
    def _execute_ai_portfolio_trades(self):
        """Run AI portfolio decisioning and execute trades hands-off."""
        try:
            self.logger.info("🤖 Executing AI portfolio automation")
            from ..ai_ranking.hybrid_ranking_engine import HybridRankingEngine
            from ..portfolio_management.portfolio_manager import PortfolioManager
            
            ranking_engine = HybridRankingEngine(self.data_manager)
            portfolio_manager = PortfolioManager(self.data_manager, ranking_engine)
            result = portfolio_manager.manage_ai_portfolio(
                portfolio_id=self.ai_portfolio_id,
                collection_id=self.collection_id
            )
            if result.get('success'):
                actions = result.get('actions_taken', [])
                self.logger.info(f"✅ AI automation complete. Actions taken: {len(actions)}")
            else:
                self.logger.warning(f"⚠️ AI automation did not run successfully: {result.get('error')}")
            return result
        except Exception as e:
            self.logger.error(f"Error executing AI portfolio automation: {e}")
            return {'success': False, 'error': str(e)}

    def _is_within_active_window(self) -> bool:
        """Return True if current time (market TZ) is within configured active window and weekday."""
        try:
            tz = pytz.timezone(self.market_timezone)
            now_local = datetime.now(tz)
            if now_local.weekday() not in self.active_weekdays:
                return False
            current_tod = now_local.time()
            return self.active_window_start <= current_tod <= self.active_window_end
        except Exception:
            # Fail open to avoid blocking updates
            return True

    def _calculate_technical_indicators(self):
        """Calculate technical indicators for all symbols in this collection."""
        try:
            from src.indicators import indicator_manager
            
            # Get all symbols for this collection
            collection_details = self.data_manager.get_collection_details(self.collection_id)
            if not collection_details:
                self.logger.error(f"Could not get collection details for {self.collection_id}")
                return
            
            # Get symbols from the collection
            symbols = self.data_manager.get_collection_symbols(self.collection_id)
            if not symbols:
                self.logger.warning(f"No symbols found for collection {self.collection_id}")
                return
            
            self.logger.info(f"Calculating technical indicators for {len(symbols)} symbols in collection {self.collection_id}")
            
            calculated_count = 0
            for symbol in symbols:
                try:
                    # Get the symbol data
                    symbol_data = self.data_manager.get_symbol_data(self.collection_id, symbol)
                    if symbol_data is None or symbol_data.empty:
                        self.logger.warning(f"No data found for symbol {symbol} in collection {self.collection_id}")
                        continue
                    
                    # Calculate all technical indicators
                    enhanced_data = indicator_manager.calculate_all_indicators(symbol_data)
                    
                    # Store the enhanced data with indicators
                    self.data_manager.store_symbol_indicators(self.collection_id, symbol, enhanced_data)
                    
                    calculated_count += 1
                    
                except Exception as e:
                    self.logger.error(f"Error calculating indicators for symbol {symbol}: {e}")
                    continue
            
            self.logger.info(f"Successfully calculated technical indicators for {calculated_count}/{len(symbols)} symbols in collection {self.collection_id}")
            
        except Exception as e:
            self.logger.error(f"Error in technical indicator calculation for collection {self.collection_id}: {e}")
    
    def _update_database_times(self):
        """Update the database with current last_run and next_run times."""
        try:
            from datetime import datetime, timedelta
            
            # Calculate next run time
            now = datetime.now()
            if self.update_interval == "1min":
                next_run = now + timedelta(minutes=1)
            elif self.update_interval == "5min":
                next_run = now + timedelta(minutes=5)
            elif self.update_interval == "10min":
                next_run = now + timedelta(minutes=10)
            elif self.update_interval == "30min":
                next_run = now + timedelta(minutes=30)
            elif self.update_interval == "1h":
                next_run = now + timedelta(hours=1)
            elif self.update_interval == "24h":
                next_run = now + timedelta(hours=24)
            else:
                next_run = now + timedelta(hours=24)
            
            # Update the database
            self.data_manager.enable_auto_update(
                self.collection_id,
                True,
                self.update_interval,
                self.last_run.isoformat(),
                next_run.isoformat()
            )
            
            self.next_run = next_run
            self.logger.info(f"Updated database times for collection {self.collection_id}: last_run={self.last_run.isoformat()}, next_run={next_run.isoformat()}")
            
        except Exception as e:
            self.logger.error(f"Error updating database times for collection {self.collection_id}: {e}")
    
    def _trigger_ai_ranking_recalculation(self):
        """Trigger AI ranking recalculation after data update."""
        try:
            self.logger.info("=" * 60)
            self.logger.info("🤖 AI RANKING RECALCULATION STARTED")
            self.logger.info(f"📊 Collection: {self.collection_id}")
            self.logger.info(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.logger.info("=" * 60)
            
            # Import AI integration components
            from ..ai_ranking.ranking_engine import StockRankingEngine
            from ..ai_ranking.strategy_analyzer import StrategyAnalyzer
            
            # Initialize ranking engine with current data manager
            ranking_engine = StockRankingEngine(self.data_manager)
            
            # Perform ranking calculation with all stocks
            ranking_result = ranking_engine.rank_collection(self.collection_id, max_stocks=1000)
            
            if ranking_result and ranking_result.ranked_stocks:
                self.logger.info(f"✅ AI ranking recalculation completed successfully!")
                self.logger.info(f"📈 Total stocks ranked: {len(ranking_result.ranked_stocks)}")
                
                # Log top 5 stocks for monitoring
                self.logger.info("🏆 TOP 5 STOCKS (Updated Rankings):")
                top_stocks = ranking_result.ranked_stocks[:5]
                for i, stock in enumerate(top_stocks, 1):
                    self.logger.info(f"   {i}. {stock.symbol}: {stock.total_score:.2f} (Tech: {stock.technical_score:.2f}, Risk: {stock.risk_score:.2f})")
                
                # Store ranking metadata for tracking
                self._store_ranking_metadata(ranking_result)
                
                self.logger.info("=" * 60)
                self.logger.info("🤖 AI RANKING RECALCULATION COMPLETED")
                self.logger.info("=" * 60)
                
            else:
                self.logger.warning(f"❌ No ranking results generated for collection {self.collection_id}")
                
        except Exception as e:
            self.logger.error("=" * 60)
            self.logger.error("❌ AI RANKING RECALCULATION FAILED")
            self.logger.error(f"📊 Collection: {self.collection_id}")
            self.logger.error(f"💥 Error: {e}")
            self.logger.error("=" * 60)
    
    def _store_ranking_metadata(self, ranking_result):
        """Store ranking metadata for tracking and monitoring."""
        try:
            # Store basic ranking metadata
            metadata = {
                'collection_id': self.collection_id,
                'ranking_timestamp': datetime.now().isoformat(),
                'total_stocks_ranked': len(ranking_result.ranked_stocks),
                'top_stocks': [
                    {
                        'symbol': stock.symbol,
                        'total_score': stock.total_score,
                        'technical_score': stock.technical_score,
                        'risk_score': stock.risk_score,
                        'rank': i + 1
                    }
                    for i, stock in enumerate(ranking_result.ranked_stocks[:10])  # Top 10
                ]
            }
            
            # Store ranking metadata in instance for status reporting
            self.last_ai_ranking_update = datetime.now()
            self.last_ai_ranking_metadata = metadata
            
            # Store in database or cache for later retrieval
            # This could be used for tracking ranking changes over time
            self.logger.info(f"✅ Stored ranking metadata for collection {self.collection_id}")
            
        except Exception as e:
            self.logger.error(f"❌ Error storing ranking metadata for collection {self.collection_id}: {e}")
    
    def get_status(self) -> Dict:
        """Get the current status of this scheduler."""
        from datetime import datetime
        
        status = {
            'collection_id': self.collection_id,
            'is_running': self.is_running,
            'interval': self.update_interval,
            'interval_description': self.available_intervals.get(self.update_interval, 'Unknown'),
            'ai_ranking_integrated': True  # Indicate that AI ranking is now integrated
        }
        
        # Add next run time if scheduler is running
        if self.is_running and self.next_run:
            status['next_run'] = self.next_run.isoformat()
            status['next_run_formatted'] = self.next_run.strftime('%Y-%m-%d %H:%M:%S')
        
        # Add last run time and results if available
        if self.last_run:
            status['last_run'] = self.last_run.isoformat()
            status['last_run_formatted'] = self.last_run.strftime('%Y-%m-%d %H:%M:%S')
        
        if hasattr(self, 'last_result') and self.last_result:
            status['last_result'] = self.last_result
        
        # Add AI ranking information
        if hasattr(self, 'last_ai_ranking_update') and self.last_ai_ranking_update:
            status['ai_ranking_last_update'] = self.last_ai_ranking_update.isoformat()
            status['ai_ranking_last_update_formatted'] = self.last_ai_ranking_update.strftime('%Y-%m-%d %H:%M:%S')
        
        if hasattr(self, 'last_ai_ranking_metadata') and self.last_ai_ranking_metadata:
            status['ai_ranking_metadata'] = self.last_ai_ranking_metadata
        
        return status


class DataCollectionScheduler:
    """Manager for multiple collection-specific schedulers."""
    
    def __init__(self, data_manager: DataCollectionManager):
        self.logger = logging.getLogger(__name__)
        self.data_manager = data_manager
        self.collection_schedulers: Dict[str, CollectionScheduler] = {}
    
    def get_or_create_scheduler(self, collection_id: str) -> CollectionScheduler:
        """Get existing scheduler or create new one for collection."""
        if collection_id not in self.collection_schedulers:
            self.collection_schedulers[collection_id] = CollectionScheduler(collection_id, self.data_manager)
        return self.collection_schedulers[collection_id]
    
    def start_collection_scheduler(self, collection_id: str) -> bool:
        """Start scheduler for a specific collection."""
        scheduler = self.get_or_create_scheduler(collection_id)
        return scheduler.start_scheduler()
    
    def stop_collection_scheduler(self, collection_id: str) -> bool:
        """Stop scheduler for a specific collection."""
        if collection_id in self.collection_schedulers:
            scheduler = self.collection_schedulers[collection_id]
            scheduler.stop_scheduler()
            return True
        return False
    
    def set_collection_interval(self, collection_id: str, interval: str) -> bool:
        """Set update interval for a specific collection."""
        scheduler = self.get_or_create_scheduler(collection_id)
        return scheduler.set_update_interval(interval)
    
    def get_collection_status(self, collection_id: str) -> Optional[Dict]:
        """Get status of a specific collection scheduler."""
        if collection_id in self.collection_schedulers:
            return self.collection_schedulers[collection_id].get_status()
        else:
            # Create scheduler if it doesn't exist to get status
            scheduler = self.get_or_create_scheduler(collection_id)
            return scheduler.get_status()
    
    def get_all_scheduler_status(self) -> List[Dict]:
        """Get status of all collection schedulers."""
        status_list = []
        for collection_id, scheduler in self.collection_schedulers.items():
            status = scheduler.get_status()
            status_list.append(status)
        return status_list
    
    def get_available_intervals(self):
        """Get available intervals (same for all schedulers)."""
        if self.collection_schedulers:
            return list(self.collection_schedulers.values())[0].get_available_intervals()
        return {
            "5min": "5 minutes",
            "10min": "10 minutes", 
            "30min": "30 minutes",
            "1h": "1 hour",
            "24h": "24 hours"
        }
    
    def stop_all_schedulers(self):
        """Stop all collection schedulers."""
        for collection_id in list(self.collection_schedulers.keys()):
            self.stop_collection_scheduler(collection_id) 