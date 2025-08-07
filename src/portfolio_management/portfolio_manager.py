"""
Portfolio Manager

Main portfolio management class that coordinates allocation, rebalancing,
and risk management operations.
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

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
    stop_loss_pct: float = 0.15  # 15%
    take_profit_pct: float = 0.25  # 25%
    cash_reserve_pct: float = 0.10  # 10%
    risk_level: RiskLevel = RiskLevel.MODERATE
    rebalance_frequency: str = "monthly"  # daily, weekly, monthly

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
                    stop_loss_pct=0.15,
                    take_profit_pct=0.25,
                    risk_level=RiskLevel.MODERATE
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
                    stop_loss_pct=0.12,
                    take_profit_pct=0.20,
                    risk_level=RiskLevel.CONSERVATIVE
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
            portfolio = self.db.get_portfolio(portfolio_id)
            if not portfolio:
                self.logger.error(f"Portfolio {portfolio_id} not found")
                return False
            
            # If no price provided, fetch the last traded price
            if price is None:
                price = self._get_last_traded_price(symbol)
                if price is None:
                    self.logger.error(f"Could not fetch price for {symbol}")
                    return False
                self.logger.info(f"Using fetched price for {symbol}: ${price:.2f}")
            
            # Check if we have enough cash
            total_cost = shares * price
            if total_cost > portfolio.current_cash:
                self.logger.error(f"Insufficient cash for {symbol} purchase")
                return False
            
            # Check position size limits
            settings = PortfolioSettings(**portfolio.settings)
            portfolio_summary = self.get_portfolio_summary(portfolio_id)
            
            if portfolio_summary:
                position_value = shares * price
                if position_value > portfolio_summary.total_value * settings.max_position_size:
                    self.logger.error(f"Position size exceeds limit for {symbol}")
                    return False
                
                if portfolio_summary.positions_count >= settings.max_positions:
                    self.logger.error(f"Maximum positions reached for portfolio")
                    return False
            
            # Execute transaction
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
            
            self.logger.info(f"Bought {shares} shares of {symbol} at ${price:.2f}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error buying stock: {e}")
            return False
    
    def sell_stock(self, portfolio_id: int, symbol: str, shares: float, 
                   price: float = None, notes: str = None) -> bool:
        """Sell stock from a portfolio."""
        try:
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
            
            self.logger.info(f"Sold {shares} shares of {symbol} at ${price:.2f}")
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
            
            settings = PortfolioSettings(**portfolio.settings)
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
            elif current_position.pnl_pct >= settings.take_profit_pct * 100:
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
                    'user_cash_utilization': ((user.total_value - user.cash) / user.total_value) * 100,
                    'ai_cash_utilization': ((ai.total_value - ai.cash) / ai.total_value) * 100
                }
            
            return comparison
            
        except Exception as e:
            self.logger.error(f"Error getting portfolio comparison: {e}")
            raise 