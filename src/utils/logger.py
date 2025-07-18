"""
Logging utility for the SMART STOCK TRADING SYSTEM.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from src.utils.config_loader import config


def get_logger(name: str = None) -> logging.Logger:
    """Get a logger instance for the given name."""
    if name is None:
        name = "TradingSystem"
    
    logger = logging.getLogger(name)
    
    if not logger.handlers:  # Only setup if not already configured
        logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        log_config = config.get('logging', {})
        log_file = log_config.get('file_path', 'logs/trading_system.log')
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger


class TradingLogger:
    """Centralized logging for the trading system."""
    
    def __init__(self, name: str = "TradingSystem"):
        self.name = name
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger with file and console handlers."""
        logger = logging.getLogger(self.name)
        
        if logger.handlers:  # Already configured
            return logger
        
        logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        log_config = config.get('logging', {})
        log_file = log_config.get('file_path', 'logs/trading_system.log')
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def info(self, message: str) -> None:
        """Log info message."""
        self.logger.info(message)
    
    def warning(self, message: str) -> None:
        """Log warning message."""
        self.logger.warning(message)
    
    def error(self, message: str) -> None:
        """Log error message."""
        self.logger.error(message)
    
    def debug(self, message: str) -> None:
        """Log debug message."""
        self.logger.debug(message)
    
    def critical(self, message: str) -> None:
        """Log critical message."""
        self.logger.critical(message)
    
    def log_trade(self, trade_data: dict) -> None:
        """Log trade information."""
        trade_msg = f"TRADE: {trade_data.get('ticker', 'Unknown')} - " \
                   f"Entry: {trade_data.get('entry_price', 0):.2f} " \
                   f"Exit: {trade_data.get('exit_price', 0):.2f} " \
                   f"PnL: {trade_data.get('pnl_pct', 0):.2f}%"
        self.info(trade_msg)
    
    def log_strategy_performance(self, strategy_name: str, metrics: dict) -> None:
        """Log strategy performance metrics."""
        perf_msg = f"STRATEGY PERFORMANCE - {strategy_name}: " \
                  f"Return: {metrics.get('total_return', 0):.2f}% " \
                  f"Sharpe: {metrics.get('sharpe_ratio', 0):.2f} " \
                  f"MaxDD: {metrics.get('max_drawdown', 0):.2f}%"
        self.info(perf_msg)


# Global logger instance
logger = TradingLogger() 