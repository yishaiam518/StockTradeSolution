"""
Portfolio Manager

Main portfolio management class that coordinates allocation, rebalancing,
and risk management operations.
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, fields
from enum import Enum
import sqlite3
import json

from .portfolio_database import (
    PortfolioDatabase, Portfolio, Position, Transaction, 
    DailyPerformance, PortfolioType, TransactionType
)
from ..data_collection.data_manager import DataCollectionManager as DataManager
from ..ai_ranking.hybrid_ranking_engine import HybridRankingEngine

class RiskLevel(Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"

@dataclass
class PortfolioSettings:
    initial_cash: float = 100000.0
    max_position_size: float = 0.10  # 10% of portfolio
    max_positions: int = 20
    cash_reserve_pct: float = 0.10  # 10%
    risk_level: RiskLevel = RiskLevel.MODERATE
    rebalance_frequency: str = "monthly"  # daily, weekly, monthly
    
    # Trading cash management
    cash_for_trading: float = 100000.0  # Total cash allocated for trading
    available_cash_for_trading: float = 100000.0  # Current available cash for trading
    transaction_limit_pct: float = 0.02  # 2% limit per transaction
    safe_net: float = 1000.0  # Minimum cash to always keep available
    
    # Risk management
    stop_loss_pct: float = 0.15  # 15% stop loss
    stop_gain_pct: float = 0.25  # 25% stop gain (renamed from take_profit_pct)

@dataclass
class PortfolioSummary:
    portfolio_id: int
    name: str
    portfolio_type: PortfolioType
    total_value: float
    cash: float
    positions_value: float
    total_pnl: float
    total_pnl_pct: float
    positions_count: int
    best_position: Optional[Position]
    worst_position: Optional[Position]

class PortfolioManager:
    def __init__(self, data_manager: DataManager = None, 
                 hybrid_ranking_engine: HybridRankingEngine = None):
        self.db = PortfolioDatabase()
        self.data_manager = data_manager
        self.hybrid_ranking_engine = hybrid_ranking_engine
        self.logger = logging.getLogger(__name__)
        
        # Initialize default portfolios if none exist
        self._initialize_default_portfolios()
        
        # Migrate existing portfolios to include new trading parameters
        self._migrate_existing_portfolios()

    def _load_settings_from_portfolio(self, portfolio: Portfolio) -> Optional[PortfolioSettings]:
        """Safely load settings from a portfolio, tolerating unknown/legacy keys.

        - Maps legacy keys (e.g., take_profit_pct -> stop_gain_pct)
        - Converts string risk_level to RiskLevel enum
        - Filters out any unknown keys before constructing dataclass
        """
        try:
            raw_settings = dict(portfolio.settings or {})

            # Map legacy key if present
            if 'stop_gain_pct' not in raw_settings and 'take_profit_pct' in raw_settings:
                raw_settings['stop_gain_pct'] = raw_settings['take_profit_pct']

            # Convert risk_level string to enum if needed
            if 'risk_level' in raw_settings and isinstance(raw_settings['risk_level'], str):
                try:
                    raw_settings['risk_level'] = RiskLevel(raw_settings['risk_level'])
                except Exception:
                    # Fallback to default by removing invalid value
                    raw_settings.pop('risk_level', None)

            # Keep only allowed keys
            allowed_fields = {f.name for f in fields(PortfolioSettings)}
            filtered = {k: v for k, v in raw_settings.items() if k in allowed_fields}

            settings = PortfolioSettings(**filtered)
            return settings
        except Exception as e:
            self.logger.error(f"Error loading portfolio settings: {e}")
            return None
    
    def _migrate_existing_portfolios(self):
        """Migrate existing portfolios to include new trading parameters."""
        try:
            portfolios = self.db.get_all_portfolios()
            
            for portfolio in portfolios:
                settings = (portfolio.settings or {}).copy()
                needs_update = False
                
                # Add missing trading parameters
                if 'cash_for_trading' not in settings:
                    settings['cash_for_trading'] = portfolio.initial_cash
                    needs_update = True
                
                if 'available_cash_for_trading' not in settings:
                    settings['available_cash_for_trading'] = portfolio.current_cash
                    needs_update = True
                
                if 'transaction_limit_pct' not in settings:
                    settings['transaction_limit_pct'] = 0.02  # 2% default
                    needs_update = True
                
                if 'safe_net' not in settings:
                    settings['safe_net'] = 1000.0  # $1000 default
                    needs_update = True
                
                if 'stop_gain_pct' not in settings and 'take_profit_pct' in settings:
                    settings['stop_gain_pct'] = settings['take_profit_pct']
                    needs_update = True

                # Remove legacy/unknown keys and normalize risk_level for storage
                allowed = {f.name for f in fields(PortfolioSettings)}
                # Keep 'risk_level' as string in DB
                if 'risk_level' in settings and isinstance(settings['risk_level'], RiskLevel):
                    settings['risk_level'] = settings['risk_level'].value

                # Remove legacy key explicitly
                if 'take_profit_pct' in settings:
                    settings.pop('take_profit_pct', None)
                    needs_update = True

                # Drop any unknown keys
                filtered = {k: v for k, v in settings.items() if (k in allowed or k == 'risk_level')}
                if filtered.keys() != settings.keys():
                    needs_update = True
                settings = filtered
                
                if needs_update:
                    # Update portfolio in database
                    with sqlite3.connect(self.db.db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE portfolios 
                            SET settings = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                        """, (json.dumps(settings), portfolio.id))
                        conn.commit()
                    
                    self.logger.info(f"Migrated portfolio {portfolio.id} with new trading parameters")
                    
        except Exception as e:
            self.logger.error(f"Error migrating portfolios: {e}")
    
    def _initialize_default_portfolios(self):
        """Initialize default portfolios if none exist."""
        try:
            portfolios = self.db.get_all_portfolios()
            
            if not portfolios:
                # Create User Portfolio
                user_settings = PortfolioSettings(
                    initial_cash=100000.0,
                    max_position_size=0.10,
                    max_positions=20,
                    cash_reserve_pct=0.10,
                    risk_level=RiskLevel.MODERATE,
                    rebalance_frequency="monthly",
                    # Trading cash management
                    cash_for_trading=100000.0,
                    available_cash_for_trading=100000.0,
                    transaction_limit_pct=0.02,  # 2% limit per transaction
                    safe_net=1000.0,  # Minimum cash to always keep available
                    # Risk management
                    stop_loss_pct=0.15,
                    stop_gain_pct=0.25
                )
                
                # Convert enum to string for JSON serialization
                settings_dict = user_settings.__dict__.copy()
                settings_dict['risk_level'] = user_settings.risk_level.value
                
                self.db.create_portfolio(
                    name="User Portfolio",
                    portfolio_type=PortfolioType.USER_MANAGED,
                    initial_cash=user_settings.initial_cash,
                    settings=settings_dict
                )
                
                # Create AI Portfolio
                ai_settings = PortfolioSettings(
                    initial_cash=100000.0,
                    max_position_size=0.08,  # Slightly more conservative
                    max_positions=15,
                    cash_reserve_pct=0.10,
                    risk_level=RiskLevel.CONSERVATIVE,
                    rebalance_frequency="monthly",
                    # Trading cash management
                    cash_for_trading=100000.0,
                    available_cash_for_trading=100000.0,
                    transaction_limit_pct=0.015,  # 1.5% limit per transaction (more conservative)
                    safe_net=2000.0,  # Higher safe net for AI
                    # Risk management
                    stop_loss_pct=0.12,
                    stop_gain_pct=0.20
                )
                
                # Convert enum to string for JSON serialization
                ai_settings_dict = ai_settings.__dict__.copy()
                ai_settings_dict['risk_level'] = ai_settings.risk_level.value
                
                self.db.create_portfolio(
                    name="AI Portfolio",
                    portfolio_type=PortfolioType.AI_MANAGED,
                    initial_cash=ai_settings.initial_cash,
                    settings=ai_settings_dict
                )
                
                self.logger.info("Initialized default portfolios")
                
        except Exception as e:
            self.logger.error(f"Error initializing default portfolios: {e}")
    
    def get_portfolio_summary(self, portfolio_id: int) -> Optional[PortfolioSummary]:
        """Get a comprehensive summary of a portfolio."""
        try:
            portfolio = self.db.get_portfolio(portfolio_id)
            if not portfolio:
                return None
            
            positions = self.db.get_portfolio_positions(portfolio_id)
            
            # Calculate totals
            positions_value = sum(pos.shares * pos.current_price for pos in positions)
            total_value = portfolio.current_cash + positions_value
            total_pnl = total_value - portfolio.initial_cash
            total_pnl_pct = (total_pnl / portfolio.initial_cash) * 100 if portfolio.initial_cash > 0 else 0
            
            # Find best and worst positions
            best_position = max(positions, key=lambda p: p.pnl_pct) if positions else None
            worst_position = min(positions, key=lambda p: p.pnl_pct) if positions else None
            
            return PortfolioSummary(
                portfolio_id=portfolio.id,
                name=portfolio.name,
                portfolio_type=portfolio.portfolio_type,
                total_value=total_value,
                cash=portfolio.current_cash,
                positions_value=positions_value,
                total_pnl=total_pnl,
                total_pnl_pct=total_pnl_pct,
                positions_count=len(positions),
                best_position=best_position,
                worst_position=worst_position
            )
            
        except Exception as e:
            self.logger.error(f"Error getting portfolio summary: {e}")
            raise
    
    def _get_last_traded_price(self, symbol: str) -> Optional[float]:
        """Get the last traded price for a symbol."""
        try:
            if not self.data_manager:
                self.logger.warning("Data manager not available for price fetching")
                return None
            
            # Try to get the latest collection data
            collections = self.data_manager.list_collections()
            if not collections:
                self.logger.warning("No collections available for price fetching")
                return None
            
            # Use the most recent collection
            latest_collection = max(collections, key=lambda x: x['collection_date'])
            collection_id = latest_collection['collection_id']
            
            # Get symbol data
            data = self.data_manager.get_symbol_data(collection_id, symbol)
            if data is None or data.empty:
                self.logger.warning(f"No data available for {symbol}")
                return None
            
            # Get the latest price
            if 'Close' in data.columns:
                current_price = data['Close'].iloc[-1]
            elif 'close' in data.columns:
                current_price = data['close'].iloc[-1]
            else:
                self.logger.warning(f"No price column found for {symbol}")
                return None
            
            self.logger.info(f"Fetched last traded price for {symbol}: ${current_price:.2f}")
            return float(current_price)
            
        except Exception as e:
            self.logger.error(f"Error fetching last traded price for {symbol}: {e}")
            return None

    def buy_stock(self, portfolio_id: int, symbol: str, shares: float, 
                  price: float = None, notes: str = None) -> bool:
        """Buy stock for a portfolio."""
        try:
            self.logger.info(f"Starting buy_stock for portfolio {portfolio_id}, symbol {symbol}, shares {shares}, price {price}")
            
            portfolio = self.db.get_portfolio(portfolio_id)
            if not portfolio:
                self.logger.error(f"Portfolio {portfolio_id} not found")
                return False
        
            self.logger.info(f"Found portfolio: {portfolio.name}, current cash: ${portfolio.current_cash}")
            
            # Load portfolio settings
            settings = self._load_settings_from_portfolio(portfolio)
            if not settings:
                return False
            self.logger.info(f"Portfolio settings loaded: available_cash_for_trading=${settings.available_cash_for_trading:.2f}, transaction_limit_pct={settings.transaction_limit_pct}")
            
            # If no price provided, fetch the last traded price
            if price is None:
                self.logger.info(f"No price provided, fetching last traded price for {symbol}")
                price = self._get_last_traded_price(symbol)
                if price is None:
                    self.logger.error(f"Could not fetch price for {symbol}")
                    return False
                self.logger.info(f"Using fetched price for {symbol}: ${price:.2f}")
            else:
                self.logger.info(f"Using provided price for {symbol}: ${price:.2f}")
            
            # Calculate total cost
            total_cost = shares * price
            self.logger.info(f"Total cost: ${total_cost:.2f}, available cash for trading: ${settings.available_cash_for_trading:.2f}")
            
            # Check if we have enough available cash for trading
            if total_cost > settings.available_cash_for_trading:
                self.logger.error(f"Insufficient available cash for trading. Need ${total_cost:.2f}, have ${settings.available_cash_for_trading:.2f}")
                return False
    
            # Check transaction limit (percentage of cash for trading)
            transaction_limit = settings.cash_for_trading * settings.transaction_limit_pct
            if total_cost > transaction_limit:
                self.logger.error(f"Transaction exceeds limit. Cost: ${total_cost:.2f}, Limit: ${transaction_limit:.2f} ({settings.transaction_limit_pct*100}% of ${settings.cash_for_trading:.2f})")
                return False
            
            # Check safe net (minimum cash to always keep available)
            remaining_cash = settings.available_cash_for_trading - total_cost
            if remaining_cash < settings.safe_net:
                self.logger.error(f"Transaction would violate safe net. Remaining cash: ${remaining_cash:.2f}, Safe net: ${settings.safe_net:.2f}")
                return False
            
            # Check position size limits
            portfolio_summary = self.get_portfolio_summary(portfolio_id)
            
            if portfolio_summary:
                position_value = shares * price
                self.logger.info(f"Position value: ${position_value:.2f}, total portfolio value: ${portfolio_summary.total_value:.2f}")
                
                if position_value > portfolio_summary.total_value * settings.max_position_size:
                    self.logger.error(f"Position size exceeds limit for {symbol}. Position: ${position_value:.2f}, Limit: ${portfolio_summary.total_value * settings.max_position_size:.2f}")
                    return False
                
                if portfolio_summary.positions_count >= settings.max_positions:
                    self.logger.error(f"Maximum positions reached for portfolio. Current: {portfolio_summary.positions_count}, Max: {settings.max_positions}")
                    return False
            else:
                self.logger.warning("Could not get portfolio summary, skipping position size checks")
            
            # Execute transaction
            self.logger.info(f"Executing transaction for {shares} shares of {symbol} at ${price:.2f}")
            transaction_id = self.db.add_transaction(
                portfolio_id=portfolio_id,
                symbol=symbol,
                transaction_type=TransactionType.BUY,
                shares=shares,
                price=price,
                notes=notes
            )
            
            # Update position
            self.db.update_position(portfolio_id, symbol, shares, price)
            
            # Update available cash for trading
            settings.available_cash_for_trading -= total_cost
            portfolio.settings = settings.__dict__.copy()
            portfolio.settings['risk_level'] = settings.risk_level.value
            
            # Update portfolio in database
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE portfolios 
                    SET current_cash = ?, settings = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (portfolio.current_cash - total_cost, json.dumps(portfolio.settings), portfolio_id))
                conn.commit()
            
            self.logger.info(f"Successfully bought {shares} shares of {symbol} at ${price:.2f}. Available cash for trading: ${settings.available_cash_for_trading:.2f}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error buying stock: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def sell_stock(self, portfolio_id: int, symbol: str, shares: float, 
                   price: float = None, notes: str = None) -> bool:
        """Sell stock from a portfolio."""
        try:
            self.logger.info(f"Starting sell_stock for portfolio {portfolio_id}, symbol {symbol}, shares {shares}, price {price}")
            
            portfolio = self.db.get_portfolio(portfolio_id)
            if not portfolio:
                self.logger.error(f"Portfolio {portfolio_id} not found")
                return False
            
            # Load portfolio settings
            settings = self._load_settings_from_portfolio(portfolio)
            if not settings:
                return False
            self.logger.info(f"Portfolio settings loaded: available_cash_for_trading=${settings.available_cash_for_trading:.2f}")
            
            # Check if we have enough shares
            positions = self.db.get_portfolio_positions(portfolio_id)
            position = next((p for p in positions if p.symbol == symbol), None)
            
            if not position or position.shares < shares:
                self.logger.error(f"Insufficient shares of {symbol} to sell")
                return False
            
            # If no price provided, fetch the last traded price
            if price is None:
                price = self._get_last_traded_price(symbol)
                if price is None:
                    self.logger.error(f"Could not fetch price for {symbol}")
                    return False
                self.logger.info(f"Using fetched price for {symbol}: ${price:.2f}")
            
            # Calculate total proceeds
            total_proceeds = shares * price
            self.logger.info(f"Total proceeds: ${total_proceeds:.2f}")
            
            # Execute transaction
            transaction_id = self.db.add_transaction(
                portfolio_id=portfolio_id,
                symbol=symbol,
                transaction_type=TransactionType.SELL,
                shares=shares,
                price=price,
                notes=notes
            )
            
            # Update position (negative shares for sell)
            self.db.update_position(portfolio_id, symbol, -shares, price)
            
            # Update available cash for trading
            settings.available_cash_for_trading += total_proceeds
            portfolio.settings = settings.__dict__.copy()
            portfolio.settings['risk_level'] = settings.risk_level.value
            
            # Update portfolio in database
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE portfolios 
                    SET current_cash = ?, settings = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (portfolio.current_cash + total_proceeds, json.dumps(portfolio.settings), portfolio_id))
                conn.commit()
            
            self.logger.info(f"Sold {shares} shares of {symbol} at ${price:.2f}. Available cash for trading: ${settings.available_cash_for_trading:.2f}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error selling stock: {e}")
            return False
    
    def update_portfolio_prices(self, portfolio_id: int, 
                              price_data: Dict[str, float]) -> None:
        """Update current prices for all positions in a portfolio."""
        try:
            positions = self.db.get_portfolio_positions(portfolio_id)
            
            for position in positions:
                if position.symbol in price_data:
                    new_price = price_data[position.symbol]
                    
                    # Update position with new price
                    self.db.update_position(portfolio_id, position.symbol, 0, new_price)
            
            self.logger.info(f"Updated prices for portfolio {portfolio_id}")
            
        except Exception as e:
            self.logger.error(f"Error updating portfolio prices: {e}")
            raise
    
    def record_daily_snapshot(self, portfolio_id: int, 
                             price_data: Dict[str, float]) -> None:
        """Record daily performance snapshot for a portfolio."""
        try:
            # Update prices first
            self.update_portfolio_prices(portfolio_id, price_data)
            
            # Get portfolio summary
            summary = self.get_portfolio_summary(portfolio_id)
            if not summary:
                return
            
            # Record daily performance
            today = date.today()
            self.db.record_daily_performance(
                portfolio_id=portfolio_id,
                date=today,
                total_value=summary.total_value,
                pnl=summary.total_pnl,
                return_pct=summary.total_pnl_pct,
                cash=summary.cash,
                positions_value=summary.positions_value
            )
            
            self.logger.info(f"Recorded daily snapshot for portfolio {portfolio_id}")
            
        except Exception as e:
            self.logger.error(f"Error recording daily snapshot: {e}")
            raise
    
    def manage_ai_portfolio(self, portfolio_id: int, 
                           collection_id: str = "ALL_20250803_160817") -> Dict:
        """Manage AI portfolio based on hybrid ranking results."""
        try:
            if not self.hybrid_ranking_engine:
                self.logger.error("Hybrid ranking engine not available")
                return {"success": False, "error": "Ranking engine not available"}
            
            # Get hybrid ranking results
            ranking_results = self.hybrid_ranking_engine.rank_collection_hybrid(
                collection_id=collection_id,
                max_stocks=50  # Limit for AI portfolio
            )
            
            if not ranking_results or not hasattr(ranking_results, 'dual_scores'):
                return {"success": False, "error": "No ranking results available"}
            
            portfolio = self.db.get_portfolio(portfolio_id)
            if not portfolio or portfolio.portfolio_type != PortfolioType.AI_MANAGED:
                return {"success": False, "error": "Invalid AI portfolio"}
            
            settings = self._load_settings_from_portfolio(portfolio)
            if not settings:
                return {"success": False, "error": "Invalid portfolio settings"}
            portfolio_summary = self.get_portfolio_summary(portfolio_id)
            
            decisions = []
            actions_taken = []
            
            # Process ranking results
            for stock in ranking_results.dual_scores:
                symbol = stock.symbol
                # Calculate combined score as average of OpenAI and local scores
                combined_score = (stock.openai_score + stock.local_score) / 2
                # Generate recommendation based on combined score
                if combined_score >= 75:
                    recommendation = "Strong Buy"
                elif combined_score >= 65:
                    recommendation = "Buy"
                elif combined_score >= 55:
                    recommendation = "Hold"
                elif combined_score >= 45:
                    recommendation = "Sell"
                else:
                    recommendation = "Strong Sell"
                
                # Get current price (simplified - in real implementation, get from data manager)
                current_price = 100.0  # Placeholder - should get real price
                
                # Decision logic
                decision = self._make_ai_decision(
                    symbol=symbol,
                    combined_score=combined_score,
                    recommendation=recommendation,
                    current_price=current_price,
                    portfolio_summary=portfolio_summary,
                    settings=settings
                )
                
                if decision['action'] != 'hold':
                    actions_taken.append(decision)
                    
                    # Execute decision
                    if decision['action'] == 'buy':
                        success = self.buy_stock(
                            portfolio_id=portfolio_id,
                            symbol=symbol,
                            shares=decision['shares'],
                            price=current_price,
                            notes=f"AI Decision: Score={combined_score}, Rec={recommendation}"
                        )
                        decision['executed'] = success
                    
                    elif decision['action'] == 'sell':
                        success = self.sell_stock(
                            portfolio_id=portfolio_id,
                            symbol=symbol,
                            shares=decision['shares'],
                            price=current_price,
                            notes=f"AI Decision: Score={combined_score}, Rec={recommendation}"
                        )
                        decision['executed'] = success
                
                # Record decision
                self.db.record_algorithm_decision(
                    portfolio_id=portfolio_id,
                    symbol=symbol,
                    decision=decision['action'],
                    confidence=combined_score / 100.0,
                    factors={
                        'combined_score': combined_score,
                        'recommendation': recommendation,
                        'reason': decision['reason']
                    }
                )
                
                decisions.append(decision)
            
            return {
                "success": True,
                "decisions": decisions,
                "actions_taken": actions_taken,
                "total_decisions": len(decisions)
            }
            
        except Exception as e:
            self.logger.error(f"Error managing AI portfolio: {e}")
            return {"success": False, "error": str(e)}
    
    def _make_ai_decision(self, symbol: str, combined_score: float, 
                          recommendation: str, current_price: float,
                          portfolio_summary: PortfolioSummary,
                          settings: PortfolioSettings) -> Dict:
        """Make AI decision for a stock."""
        decision = {
            'symbol': symbol,
            'action': 'hold',
            'shares': 0,
            'reason': '',
            'confidence': combined_score / 100.0
        }
        
        # Get current position
        positions = self.db.get_portfolio_positions(portfolio_summary.portfolio_id)
        current_position = next((p for p in positions if p.symbol == symbol), None)
        
        # Buy decision logic
        if recommendation in ['Strong Buy', 'Buy'] and combined_score >= 65:
            if not current_position:
                # Calculate position size
                max_position_value = portfolio_summary.total_value * settings.max_position_size
                shares = max_position_value / current_price
                
                if shares > 0 and portfolio_summary.cash >= (shares * current_price):
                    decision.update({
                        'action': 'buy',
                        'shares': shares,
                        'reason': f'AI Recommendation: {recommendation} (Score: {combined_score:.1f})'
                    })
        
        # Sell decision logic
        elif current_position:
            # Check stop loss
            if current_position.pnl_pct <= -settings.stop_loss_pct * 100:
                decision.update({
                    'action': 'sell',
                    'shares': current_position.shares,
                    'reason': f'Stop Loss triggered: {current_position.pnl_pct:.1f}%'
                })
            
            # Check take profit
            elif current_position.pnl_pct >= settings.stop_gain_pct * 100:
                decision.update({
                    'action': 'sell',
                    'shares': current_position.shares,
                    'reason': f'Take Profit triggered: {current_position.pnl_pct:.1f}%'
                })
            
            # Check if recommendation changed to Sell
            elif recommendation in ['Sell', 'Strong Sell'] and combined_score < 45:
                decision.update({
                    'action': 'sell',
                    'shares': current_position.shares,
                    'reason': f'AI Recommendation: {recommendation} (Score: {combined_score:.1f})'
                })
        
        return decision
    
    def get_portfolio_comparison(self) -> Dict:
        """Get comparison between user and AI portfolios."""
        try:
            portfolios = self.db.get_all_portfolios()
            
            comparison = {
                'user_portfolio': None,
                'ai_portfolio': None,
                'comparison': {}
            }
            
            for portfolio in portfolios:
                summary = self.get_portfolio_summary(portfolio.id)
                if summary:
                    if portfolio.portfolio_type == PortfolioType.USER_MANAGED:
                        comparison['user_portfolio'] = summary
                    elif portfolio.portfolio_type == PortfolioType.AI_MANAGED:
                        comparison['ai_portfolio'] = summary
            
            # Calculate comparison metrics
            if comparison['user_portfolio'] and comparison['ai_portfolio']:
                user = comparison['user_portfolio']
                ai = comparison['ai_portfolio']
                
                comparison['comparison'] = {
                    'user_total_return': user.total_pnl_pct,
                    'ai_total_return': ai.total_pnl_pct,
                    'performance_difference': user.total_pnl_pct - ai.total_pnl_pct,
                    'user_positions': user.positions_count,
                    'ai_positions': ai.positions_count,
                    'user_cash_utilization': ((user.total_value - user.cash) / user.total_value * 100) if user.total_value > 0 else 0,
                    'ai_cash_utilization': ((ai.total_value - ai.cash) / ai.total_value * 100) if ai.total_value > 0 else 0
                }
            
            return comparison
            
        except Exception as e:
            self.logger.error(f"Error getting portfolio comparison: {e}")
            raise 