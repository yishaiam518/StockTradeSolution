"""
Automation Scheduler for running automated trading cycles
"""

import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass

from .automation_engine import AutomationEngine, TradingMode
from ..utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

@dataclass
class CycleResult:
    """Result of an automation cycle"""
    timestamp: datetime
    analysis_count: int
    signals_generated: int
    trades_executed: int
    errors: list
    performance_metrics: Dict[str, Any]

class AutomationScheduler:
    """
    Scheduler for running automated trading cycles
    """
    
    def __init__(self, config: ConfigLoader, mode: TradingMode = TradingMode.PAPER_TRADING):
        self.config = config
        self.mode = mode
        self.automation_engine = AutomationEngine(config, mode)
        
        # Scheduler settings
        self.cycle_interval = config.get('automation.cycle_interval', 300)  # 5 minutes
        self.market_hours_only = config.get('automation.market_hours_only', True)
        self.is_running = False
        self.thread = None
        
        # Cycle tracking
        self.cycle_count = 0
        self.last_cycle_time = None
        self.cycle_results = []
        
        # Performance tracking
        self.start_time = None
        self.total_signals = 0
        self.total_trades = 0
        self.total_errors = 0
        
        logger.info(f"Automation Scheduler initialized in {mode.value} mode")
    
    def start(self) -> None:
        """
        Start the automation scheduler
        """
        if self.is_running:
            logger.warning("Automation scheduler is already running")
            return
        
        self.is_running = True
        self.start_time = datetime.now()
        
        # Start scheduler thread
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        
        logger.info("Automation scheduler started")
    
    def stop(self) -> None:
        """
        Stop the automation scheduler
        """
        if not self.is_running:
            logger.warning("Automation scheduler is not running")
            return
        
        self.is_running = False
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=10)
        
        logger.info("Automation scheduler stopped")
    
    def _run_scheduler(self) -> None:
        """
        Main scheduler loop
        """
        logger.info("Starting automation scheduler loop")
        
        while self.is_running:
            try:
                # Check if we should run during market hours
                if self.market_hours_only and not self._is_market_hours():
                    logger.info("Outside market hours, skipping cycle")
                    time.sleep(60)  # Check every minute
                    continue
                
                # Run automation cycle
                self._run_cycle()
                
                # Wait for next cycle
                time.sleep(self.cycle_interval)
                
            except Exception as e:
                logger.error(f"Error in automation scheduler: {e}")
                time.sleep(60)  # Wait before retrying
    
    def _run_cycle(self) -> None:
        """
        Run one automation cycle
        """
        cycle_start = datetime.now()
        logger.info(f"Starting automation cycle {self.cycle_count + 1}")
        
        try:
            # Run automation engine
            result = self.automation_engine.run_cycle()
            
            # Process results
            analysis_count = len(result['analysis'])
            signals_generated = len(result['signals'])
            trades_executed = len(result['executed_trades'])
            
            # Log results
            logger.info(f"Cycle {self.cycle_count + 1} completed:")
            logger.info(f"  - Analyzed {analysis_count} stocks")
            logger.info(f"  - Generated {signals_generated} signals")
            logger.info(f"  - Executed {trades_executed} trades")
            
            # Update tracking
            self.cycle_count += 1
            self.last_cycle_time = cycle_start
            self.total_signals += signals_generated
            self.total_trades += trades_executed
            
            # Store cycle result
            cycle_result = CycleResult(
                timestamp=cycle_start,
                analysis_count=analysis_count,
                signals_generated=signals_generated,
                trades_executed=trades_executed,
                errors=[],
                performance_metrics=self._calculate_performance_metrics()
            )
            self.cycle_results.append(cycle_result)
            
            # Keep only last 100 cycle results
            if len(self.cycle_results) > 100:
                self.cycle_results = self.cycle_results[-100:]
            
        except Exception as e:
            logger.error(f"Error in automation cycle: {e}")
            self.total_errors += 1
            
            # Store error result
            cycle_result = CycleResult(
                timestamp=cycle_start,
                analysis_count=0,
                signals_generated=0,
                trades_executed=0,
                errors=[str(e)],
                performance_metrics={}
            )
            self.cycle_results.append(cycle_result)
    
    def _is_market_hours(self) -> bool:
        """
        Check if current time is during market hours (9:30 AM - 4:00 PM ET)
        """
        try:
            import pytz
            et_tz = pytz.timezone('America/New_York')
            now_et = datetime.now(et_tz)
            
            # Market hours: 9:30 AM - 4:00 PM ET, Monday-Friday
            if now_et.weekday() >= 5:  # Weekend
                logger.debug(f"Market closed: Weekend ({now_et.strftime('%A')})")
                return False
            
            # Check if before market open
            if now_et.hour < 9 or (now_et.hour == 9 and now_et.minute < 30):
                logger.debug(f"Market closed: Before market open ({now_et.strftime('%H:%M')} ET)")
                return False
            
            # Check if after market close
            if now_et.hour >= 16:
                logger.debug(f"Market closed: After market close ({now_et.strftime('%H:%M')} ET)")
                return False
            
            logger.debug(f"Market open: {now_et.strftime('%A %H:%M')} ET")
            return True
            
        except ImportError:
            # Fallback if pytz is not available
            logger.warning("pytz not available, using simplified timezone conversion")
            now = datetime.now()
            
            # Rough conversion from local time to ET (assumes local time is close to ET)
            # This is not accurate but better than nothing
            et_hour = now.hour
            
            # Market hours: 9:30 AM - 4:00 PM ET
            if now.weekday() >= 5:  # Weekend
                return False
            
            if et_hour < 9 or (et_hour == 9 and now.minute < 30):
                return False
            
            if et_hour >= 16:
                return False
            
            return True
    
    def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """
        Calculate performance metrics for the automation system
        """
        try:
            # Get portfolio summary
            portfolio = self.automation_engine.broker.get_account()
            positions = self.automation_engine.position_manager.get_position_summary()
            
            # Calculate metrics
            total_value = portfolio['cash'] + portfolio['buying_power']
            total_pnl = positions['total_pnl']
            pnl_pct = (total_pnl / portfolio['initial_cash']) * 100 if portfolio['initial_cash'] > 0 else 0
            
            return {
                'total_value': total_value,
                'cash': portfolio['cash'],
                'buying_power': portfolio['buying_power'],
                'total_pnl': total_pnl,
                'pnl_pct': pnl_pct,
                'total_positions': positions['total_positions'],
                'avg_pnl_pct': positions['avg_pnl_pct'],
                'cycle_count': self.cycle_count,
                'total_signals': self.total_signals,
                'total_trades': self.total_trades,
                'total_errors': self.total_errors
            }
            
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {e}")
            return {}
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current scheduler status
        """
        return {
            'is_running': self.is_running,
            'mode': self.mode.value,
            'cycle_count': self.cycle_count,
            'last_cycle_time': self.last_cycle_time.isoformat() if self.last_cycle_time else None,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'cycle_interval': self.cycle_interval,
            'market_hours_only': self.market_hours_only,
            'performance_metrics': self._calculate_performance_metrics(),
            'recent_cycles': [
                {
                    'timestamp': result.timestamp.isoformat(),
                    'analysis_count': result.analysis_count,
                    'signals_generated': result.signals_generated,
                    'trades_executed': result.trades_executed,
                    'errors': result.errors
                }
                for result in self.cycle_results[-10:]  # Last 10 cycles
            ]
        }
    
    def run_single_cycle(self) -> Dict[str, Any]:
        """
        Run a single automation cycle manually
        """
        logger.info("Running single automation cycle")
        
        try:
            result = self.automation_engine.run_cycle()
            
            # Calculate performance metrics
            performance_metrics = self._calculate_performance_metrics()
            
            return {
                'success': True,
                'result': result,
                'performance_metrics': performance_metrics,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in single cycle: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_pending_signals(self) -> list:
        """
        Get pending signals for approval (semi-auto mode)
        """
        if self.mode == TradingMode.SEMI_AUTO:
            return self.automation_engine.get_pending_signals()
        return []
    
    def approve_signal(self, signal_id: str) -> bool:
        """
        Approve a pending signal (semi-auto mode)
        """
        if self.mode == TradingMode.SEMI_AUTO:
            return self.automation_engine.approve_signal(signal_id)
        return False
    
    def reject_signal(self, signal_id: str) -> bool:
        """
        Reject a pending signal (semi-auto mode)
        """
        if self.mode == TradingMode.SEMI_AUTO:
            return self.automation_engine.reject_signal(signal_id)
        return False 