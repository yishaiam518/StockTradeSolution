"""
Real-time Trading Engine

Handles real-time trading operations including order execution,
position management, and risk controls.
"""

import asyncio
import logging
from datetime import datetime, time
from typing import Dict, List, Optional, Tuple
import pandas as pd
import pytz

from ..utils.config_loader import ConfigLoader
from ..utils.logger import get_logger
from .paper_trading import PaperTradingBroker
from .order_manager import OrderManager
from .position_manager import PositionManager
from ..data_engine.data_engine import DataEngine
from ..strategies.base_strategy import BaseStrategy


class TradingEngine:
    """Main trading engine for real-time trading operations."""
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        """Initialize the trading engine."""
        self.config = ConfigLoader(config_path)
        self.logger = get_logger(__name__)
        
        # Initialize components
        self.data_engine = DataEngine()
        self.order_manager = OrderManager()
        self.position_manager = PositionManager()
        
        # Trading state
        self.is_running = False
        self.current_positions = {}
        self.pending_orders = {}
        self.daily_pnl = 0.0
        self.total_pnl = 0.0
        
        # Initialize broker
        self.broker = self._initialize_broker()
        
        # Trading hours
        self.trading_hours = self.config.get('real_time_trading.execution_settings.trading_hours')
        self.timezone = pytz.timezone(self.trading_hours['timezone'])
        
        # Risk management
        self.max_daily_trades = self.config.get('real_time_trading.execution_settings.max_daily_trades')
        self.daily_trade_count = 0
        self.last_trade_date = None
        
    def _initialize_broker(self):
        """Initialize the appropriate broker based on configuration."""
        broker_type = self.config.get('real_time_trading.broker')
        
        if broker_type == 'paper_trading':
            return PaperTradingBroker(
                initial_balance=self.config.get('real_time_trading.paper_trading.initial_balance'),
                commission=self.config.get('real_time_trading.paper_trading.commission'),
                slippage=self.config.get('real_time_trading.paper_trading.slippage')
            )
        elif broker_type == 'alpaca':
            # TODO: Implement Alpaca integration
            self.logger.warning("Alpaca integration not yet implemented")
            return PaperTradingBroker()
        elif broker_type == 'interactive_brokers':
            # TODO: Implement IB integration
            self.logger.warning("Interactive Brokers integration not yet implemented")
            return PaperTradingBroker()
        else:
            self.logger.error(f"Unknown broker type: {broker_type}")
            return PaperTradingBroker()
    
    def is_market_open(self) -> bool:
        """Check if the market is currently open."""
        now = datetime.now(self.timezone)
        start_time = datetime.strptime(self.trading_hours['start'], '%H:%M').time()
        end_time = datetime.strptime(self.trading_hours['end'], '%H:%M').time()
        
        # Check if it's a weekday
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
            
        # Check if current time is within trading hours
        current_time = now.time()
        return start_time <= current_time <= end_time
    
    def reset_daily_counters(self):
        """Reset daily trading counters."""
        today = datetime.now().date()
        if self.last_trade_date != today:
            self.daily_trade_count = 0
            self.daily_pnl = 0.0
            self.last_trade_date = today
    
    def can_place_trade(self) -> bool:
        """Check if we can place a new trade based on risk limits."""
        self.reset_daily_counters()
        
        if not self.is_market_open():
            self.logger.info("Market is closed")
            return False
            
        if self.daily_trade_count >= self.max_daily_trades:
            self.logger.warning(f"Daily trade limit reached: {self.max_daily_trades}")
            return False
            
        return True
    
    async def execute_strategy(self, strategy: BaseStrategy, ticker: str):
        """Execute a trading strategy for a given ticker."""
        if not self.can_place_trade():
            return
            
        try:
            # Get current market data
            data = self.data_engine.get_data(ticker, period='1d', interval='1m')
            if data.empty:
                self.logger.warning(f"No data available for {ticker}")
                return
                
            # Get strategy signals
            signals = strategy.generate_signals(data)
            current_position = self.position_manager.get_position(ticker)
            
            # Process signals
            if signals['action'] == 'BUY' and current_position <= 0:
                await self._execute_buy_order(ticker, strategy, data)
            elif signals['action'] == 'SELL' and current_position > 0:
                await self._execute_sell_order(ticker, strategy, data)
            elif signals['action'] == 'HOLD':
                self.logger.debug(f"Holding position in {ticker}")
                
        except Exception as e:
            self.logger.error(f"Error executing strategy for {ticker}: {e}")
    
    async def _execute_buy_order(self, ticker: str, strategy: BaseStrategy, data: pd.DataFrame):
        """Execute a buy order."""
        try:
            # Calculate position size
            position_size = strategy.calculate_position_size(data)
            
            # Get current price
            current_price = data['Close'].iloc[-1]
            
            # Place order
            order = await self.broker.place_order(
                symbol=ticker,
                quantity=position_size,
                side='buy',
                order_type='market'
            )
            
            if order['status'] == 'filled':
                self.daily_trade_count += 1
                self.position_manager.add_position(ticker, position_size, current_price)
                self.logger.info(f"Buy order executed for {ticker}: {position_size} shares at ${current_price:.2f}")
                
                # Update P&L
                self.daily_pnl -= position_size * current_price
                
        except Exception as e:
            self.logger.error(f"Error executing buy order for {ticker}: {e}")
    
    async def _execute_sell_order(self, ticker: str, strategy: BaseStrategy, data: pd.DataFrame):
        """Execute a sell order."""
        try:
            current_position = self.position_manager.get_position(ticker)
            if current_position <= 0:
                return
                
            # Get current price
            current_price = data['Close'].iloc[-1]
            
            # Place order
            order = await self.broker.place_order(
                symbol=ticker,
                quantity=current_position,
                side='sell',
                order_type='market'
            )
            
            if order['status'] == 'filled':
                self.daily_trade_count += 1
                
                # Calculate P&L
                avg_cost = self.position_manager.get_avg_cost(ticker)
                pnl = (current_price - avg_cost) * current_position
                
                self.position_manager.close_position(ticker)
                self.logger.info(f"Sell order executed for {ticker}: {current_position} shares at ${current_price:.2f}, P&L: ${pnl:.2f}")
                
                # Update P&L
                self.daily_pnl += pnl
                self.total_pnl += pnl
                
        except Exception as e:
            self.logger.error(f"Error executing sell order for {ticker}: {e}")
    
    async def run_trading_session(self, strategies: Dict[str, BaseStrategy], tickers: List[str]):
        """Run a complete trading session."""
        self.is_running = True
        self.logger.info("Starting trading session")
        
        try:
            while self.is_running:
                if not self.is_market_open():
                    await asyncio.sleep(60)  # Wait 1 minute
                    continue
                    
                # Execute strategies for each ticker
                for ticker in tickers:
                    if ticker in strategies:
                        await self.execute_strategy(strategies[ticker], ticker)
                        
                # Wait before next iteration
                await asyncio.sleep(30)  # Check every 30 seconds
                
        except KeyboardInterrupt:
            self.logger.info("Trading session stopped by user")
        except Exception as e:
            self.logger.error(f"Error in trading session: {e}")
        finally:
            self.is_running = False
            await self._close_session()
    
    async def _close_session(self):
        """Close the trading session and clean up."""
        self.logger.info("Closing trading session")
        
        # Close all positions if needed
        positions = self.position_manager.get_all_positions()
        for ticker, position in positions.items():
            if position > 0:
                self.logger.info(f"Closing position in {ticker}: {position} shares")
                # TODO: Implement position closing logic
        
        # Log session summary
        self.logger.info(f"Session summary - Daily P&L: ${self.daily_pnl:.2f}, Total P&L: ${self.total_pnl:.2f}")
    
    def stop_trading(self):
        """Stop the trading session."""
        self.is_running = False
        self.logger.info("Trading session stop requested")
    
    def get_portfolio_summary(self) -> Dict:
        """Get current portfolio summary."""
        positions = self.position_manager.get_all_positions()
        portfolio_value = sum(
            self.position_manager.get_position_value(ticker) 
            for ticker in positions.keys()
        )
        
        return {
            'total_value': portfolio_value,
            'cash_balance': self.broker.get_balance(),
            'total_pnl': self.total_pnl,
            'daily_pnl': self.daily_pnl,
            'positions': positions,
            'daily_trades': self.daily_trade_count
        } 