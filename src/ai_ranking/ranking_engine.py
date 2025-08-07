#!/usr/bin/env python3
"""
Lightweight Stock Ranking Engine

This module provides a fast, efficient stock ranking system that:
- Processes stocks in small batches
- Uses cached data when available
- Provides immediate results
- Handles timeouts gracefully
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
import time
from dataclasses import dataclass

from .scoring_models import MultiFactorScorer

logger = logging.getLogger(__name__)

@dataclass
class StockScore:
    """Represents a stock's ranking score."""
    symbol: str
    total_score: float
    technical_score: float
    fundamental_score: float
    risk_score: float
    market_score: float
    rank: int
    explanation: str
    recommendations: List[str]

@dataclass
class RankingResult:
    """Represents the result of a ranking operation."""
    ranked_stocks: List[StockScore]
    total_stocks: int
    timestamp: datetime
    summary: Dict

class LightweightStockRankingEngine:
    """
    Lightweight stock ranking engine optimized for speed and reliability.
    """
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.scorer = MultiFactorScorer()
        self.logger = logging.getLogger(__name__)
        
    def rank_collection(self, collection_id: str, max_stocks: int = 50) -> RankingResult:
        """
        Rank stocks in a collection with performance optimizations.
        
        Args:
            collection_id: ID of the data collection
            max_stocks: Maximum number of stocks to rank
            
        Returns:
            RankingResult with ranked stocks
        """
        try:
            self.logger.info(f"Starting lightweight ranking for collection: {collection_id}")
            start_time = time.time()
            
            # Get collection symbols (limit for performance)
            symbols = self.data_manager.get_collection_symbols(collection_id)
            if not symbols:
                self.logger.warning(f"No symbols found for collection {collection_id}")
                return self._create_empty_result()
            
            # Limit symbols for performance
            symbols = symbols[:min(max_stocks, 50)]
            self.logger.info(f"Processing {len(symbols)} symbols for ranking")
            
            # Process stocks in small batches
            ranked_stocks = []
            batch_size = 10
            
            for i in range(0, len(symbols), batch_size):
                batch = symbols[i:i + batch_size]
                self.logger.info(f"Processing batch {i//batch_size + 1}: {batch}")
                
                batch_scores = self._process_stock_batch(collection_id, batch)
                ranked_stocks.extend(batch_scores)
                
                # Check for timeout
                if time.time() - start_time > 30:  # 30 second timeout
                    self.logger.warning("Ranking timeout reached, returning partial results")
                    break
            
            # Sort by total score
            ranked_stocks.sort(key=lambda x: x.total_score, reverse=True)
            
            # Assign ranks
            for i, stock in enumerate(ranked_stocks):
                stock.rank = i + 1
            
            # Create summary
            summary = self._create_ranking_summary(ranked_stocks)
            
            result = RankingResult(
                ranked_stocks=ranked_stocks,
                total_stocks=len(ranked_stocks),
                timestamp=datetime.now(),
                summary=summary
            )
            
            elapsed_time = time.time() - start_time
            self.logger.info(f"Lightweight ranking completed in {elapsed_time:.2f}s")
            self.logger.info(f"Ranked {len(ranked_stocks)} stocks")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in lightweight ranking: {e}")
            return self._create_empty_result()
    
    def _process_stock_batch(self, collection_id: str, symbols: List[str]) -> List[StockScore]:
        """Process a batch of stocks for ranking."""
        scores = []
        
        for symbol in symbols:
            try:
                # Get stock data with indicators
                stock_data = self.data_manager.get_symbol_indicators(collection_id, symbol)
                
                if stock_data is None or stock_data.empty:
                    continue
                
                # Calculate scores using the scorer
                technical_score = self._calculate_technical_score(stock_data)
                fundamental_score = self._calculate_fundamental_score(stock_data)
                risk_score = self._calculate_risk_score(stock_data)
                market_score = self._calculate_market_score(stock_data)
                
                # Calculate total score
                total_score = (technical_score * 0.4 + 
                             fundamental_score * 0.3 + 
                             risk_score * 0.2 + 
                             market_score * 0.1)
                
                # Generate explanation
                explanation = self.scorer._generate_enhanced_template_explanation(
                    symbol, {
                        'technical': technical_score,
                        'fundamental': fundamental_score,
                        'risk': risk_score,
                        'market': market_score,
                        'total': total_score
                    }
                )
                
                # Create recommendations
                recommendations = self._generate_recommendations(total_score, technical_score, risk_score)
                
                score = StockScore(
                    symbol=symbol,
                    total_score=total_score,
                    technical_score=technical_score,
                    fundamental_score=fundamental_score,
                    risk_score=risk_score,
                    market_score=market_score,
                    rank=0,  # Will be set later
                    explanation=explanation,
                    recommendations=recommendations
                )
                
                scores.append(score)
                
            except Exception as e:
                self.logger.error(f"Error processing {symbol}: {e}")
                continue
        
        return scores
    
    def _calculate_technical_score(self, stock_data) -> float:
        """Calculate technical score based on indicators."""
        try:
            if stock_data.empty:
                return 50.0
            
            latest = stock_data.iloc[-1]
            
            # RSI analysis
            rsi = latest.get('rsi', 50)
            rsi_score = 100 if 30 <= rsi <= 70 else 50
            
            # MACD analysis
            macd = latest.get('macd', 0)
            macd_signal = latest.get('macd_signal', 0)
            macd_score = 100 if macd > macd_signal else 50
            
            # Moving average analysis
            close = latest.get('Close', 0)
            sma_20 = latest.get('sma_20', close)
            sma_50 = latest.get('sma_50', close)
            
            ma_score = 100 if close > sma_20 > sma_50 else 50
            
            # Average technical indicators
            technical_score = (rsi_score + macd_score + ma_score) / 3
            return min(max(technical_score, 0), 100)
            
        except Exception as e:
            self.logger.error(f"Error calculating technical score: {e}")
            return 50.0
    
    def _calculate_fundamental_score(self, stock_data) -> float:
        """Calculate fundamental score (simplified)."""
        try:
            # For now, use a simplified fundamental score
            # In a real implementation, this would use financial data
            return 60.0  # Default moderate score
        except Exception as e:
            self.logger.error(f"Error calculating fundamental score: {e}")
            return 50.0
    
    def _calculate_risk_score(self, stock_data) -> float:
        """Calculate risk score based on volatility."""
        try:
            if stock_data.empty:
                return 50.0
            
            # Try different column name variations
            close_cols = ['Close', 'close', 'CLOSE']
            close_col = None
            
            for col in close_cols:
                if col in stock_data.columns:
                    close_col = col
                    break
            
            if close_col is None:
                self.logger.warning("No close column found, using default risk score")
                return 50.0
            
            # Calculate volatility
            try:
                returns = stock_data[close_col].pct_change().dropna()
                if len(returns) > 0:
                    volatility = returns.std() * (252 ** 0.5) * 100
                    
                    # Lower volatility = higher score (less risk)
                    risk_score = max(0, 100 - volatility * 2)
                    return min(risk_score, 100)
                else:
                    return 50.0
            except Exception as vol_error:
                self.logger.warning(f"Error calculating volatility: {vol_error}")
                return 50.0
            
        except Exception as e:
            self.logger.error(f"Error calculating risk score: {e}")
            return 50.0
    
    def _calculate_market_score(self, stock_data) -> float:
        """Calculate market score (simplified)."""
        try:
            # For now, use a simplified market score
            return 70.0  # Default positive market score
        except Exception as e:
            self.logger.error(f"Error calculating market score: {e}")
            return 50.0
    
    def _generate_recommendations(self, total_score: float, technical_score: float, risk_score: float) -> List[str]:
        """Generate trading recommendations."""
        recommendations = []
        
        if total_score >= 70:
            recommendations.append("Strong Buy - Excellent overall score")
        elif total_score >= 60:
            recommendations.append("Buy - Good potential with moderate risk")
        elif total_score >= 50:
            recommendations.append("Hold - Monitor for improvement")
        else:
            recommendations.append("Consider selling - Poor performance indicators")
        
        if technical_score >= 70:
            recommendations.append("Strong technical momentum")
        elif technical_score < 30:
            recommendations.append("Weak technical indicators")
        
        if risk_score < 30:
            recommendations.append("High volatility - consider position sizing")
        
        return recommendations
    
    def _create_ranking_summary(self, ranked_stocks: List[StockScore]) -> Dict:
        """Create summary statistics for the ranking."""
        if not ranked_stocks:
            return {
                'recommendation_summary': {'strong_buy': 0, 'hold': 0, 'avoid': 0},
                'score_distribution': {'high': 0, 'medium': 0, 'low': 0}
            }
        
        strong_buy = sum(1 for stock in ranked_stocks if stock.total_score >= 70)
        hold = sum(1 for stock in ranked_stocks if 50 <= stock.total_score < 70)
        avoid = sum(1 for stock in ranked_stocks if stock.total_score < 50)
        
        high_scores = sum(1 for stock in ranked_stocks if stock.total_score >= 70)
        medium_scores = sum(1 for stock in ranked_stocks if 50 <= stock.total_score < 70)
        low_scores = sum(1 for stock in ranked_stocks if stock.total_score < 50)
        
        return {
            'recommendation_summary': {
                'strong_buy': strong_buy,
                'hold': hold,
                'avoid': avoid
            },
            'score_distribution': {
                'high': high_scores,
                'medium': medium_scores,
                'low': low_scores
            }
        }
    
    def _create_empty_result(self) -> RankingResult:
        """Create an empty ranking result."""
        return RankingResult(
            ranked_stocks=[],
            total_stocks=0,
            timestamp=datetime.now(),
            summary={
                'recommendation_summary': {'strong_buy': 0, 'hold': 0, 'avoid': 0},
                'score_distribution': {'high': 0, 'medium': 0, 'low': 0}
            }
        )

# Keep the original class for backward compatibility
class StockRankingEngine(LightweightStockRankingEngine):
    """Backward compatibility wrapper."""
    pass 