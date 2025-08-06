"""
AI Stock Ranking Engine

This module provides the main ranking engine that orchestrates the scoring
and ranking process for stocks within a data collection.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import logging
from datetime import datetime, timedelta
import json

from .scoring_models import MultiFactorScorer, StockScore, ScoringWeights

logger = logging.getLogger(__name__)

@dataclass
class RankingResult:
    """Complete ranking result for a collection"""
    collection_id: str
    timestamp: str
    total_stocks: int
    ranked_stocks: List[StockScore]
    summary: Dict
    metadata: Dict

class StockRankingEngine:
    """
    Main ranking engine that orchestrates the scoring and ranking process.
    
    Features:
    - Multi-factor scoring for each stock
    - Intelligent ranking from best to worst
    - Collection-specific analysis
    - Real-time updates with scheduler
    - Educational explanations and recommendations
    """
    
    def __init__(self, data_collection_manager=None):
        self.scorer = MultiFactorScorer()
        self.data_collection_manager = data_collection_manager
        self.logger = logging.getLogger(__name__)
        
    def rank_collection(self, collection_id: str, max_stocks: int = 100) -> RankingResult:
        """
        Rank all stocks in a collection from best to worst investment opportunities.
        
        Args:
            collection_id: ID of the data collection to rank
            max_stocks: Maximum number of stocks to rank (for performance)
            
        Returns:
            RankingResult with complete ranking analysis
        """
        try:
            self.logger.info(f"=== STARTING RANKING ANALYSIS ===")
            self.logger.info(f"Collection ID: {collection_id}")
            self.logger.info(f"Max stocks requested: {max_stocks}")
            
            # Get collection details
            collection_details = self._get_collection_details(collection_id)
            if not collection_details:
                raise ValueError(f"Collection {collection_id} not found")
            self.logger.info(f"Collection details: {collection_details}")
            
            # Get symbols from collection
            symbols = self._get_collection_symbols(collection_id)
            if not symbols:
                raise ValueError(f"No symbols found in collection {collection_id}")
            
            self.logger.info(f"Total symbols in collection: {len(symbols)}")
            self.logger.info(f"First 10 symbols: {symbols[:10]}")
            self.logger.info(f"Last 10 symbols: {symbols[-10:]}")
            self.logger.info(f"Max stocks requested: {max_stocks}")
            
            # Limit symbols for performance
            symbols = symbols[:max_stocks]
            self.logger.info(f"After limiting: {len(symbols)} symbols to process")
            self.logger.info(f"Symbols to process: {symbols}")
            self.logger.info(f"Array size after limiting: {len(symbols)}")
            
            # Score each stock
            stock_scores = []
            successful_scores = 0
            failed_scores = 0
            
            self.logger.info(f"=== STARTING SCORING PROCESS ===")
            self.logger.info(f"Processing {len(symbols)} symbols...")
            
            for i, symbol in enumerate(symbols):
                self.logger.info(f"Processing symbol {i+1}/{len(symbols)}: {symbol}")
                try:
                    score = self._score_stock_in_collection(collection_id, symbol)
                    if score:
                        stock_scores.append(score)
                        successful_scores += 1
                        self.logger.info(f"✓ Successfully scored {symbol}: {score.total_score}")
                    else:
                        failed_scores += 1
                        self.logger.warning(f"✗ No score returned for {symbol}")
                except Exception as e:
                    self.logger.error(f"✗ Error scoring {symbol}: {e}")
                    failed_scores += 1
                    continue
            
            self.logger.info(f"=== SCORING COMPLETE ===")
            self.logger.info(f"Successful: {successful_scores}")
            self.logger.info(f"Failed: {failed_scores}")
            self.logger.info(f"Total processed: {len(symbols)}")
            
            # Sort by total score (best to worst)
            stock_scores.sort(key=lambda x: x.total_score, reverse=True)
            
            # Assign ranks
            for i, score in enumerate(stock_scores):
                score.rank = i + 1
            
            # Generate summary statistics
            summary = self._generate_summary(stock_scores)
            
            # Create ranking result
            result = RankingResult(
                collection_id=collection_id,
                timestamp=datetime.now().isoformat(),
                total_stocks=len(stock_scores),
                ranked_stocks=stock_scores,
                summary=summary,
                metadata={
                    'collection_details': collection_details,
                    'analysis_parameters': {
                        'max_stocks': max_stocks,
                        'scoring_weights': asdict(self.scorer.weights)
                    }
                }
            )
            
            self.logger.info(f"Ranking complete: {len(stock_scores)} stocks ranked")
            self.logger.info(f"Final result array size: {len(result.ranked_stocks)}")
            self.logger.info(f"Total stocks in result: {result.total_stocks}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error ranking collection {collection_id}: {e}")
            raise
    
    def _get_collection_details(self, collection_id: str) -> Optional[Dict]:
        """Get collection details from data manager."""
        if self.data_collection_manager:
            return self.data_collection_manager.get_collection_details(collection_id)
        return None
    
    def _get_collection_symbols(self, collection_id: str) -> List[str]:
        """Get symbols from collection."""
        if self.data_collection_manager:
            return self.data_collection_manager.get_collection_symbols(collection_id)
        return []
    
    def _score_stock_in_collection(self, collection_id: str, symbol: str) -> Optional[StockScore]:
        """Score a single stock within a collection context."""
        try:
            self.logger.info(f"  Getting data for {symbol}...")
            
            # Get stock data with indicators
            if self.data_collection_manager:
                # First try to get data with indicators
                self.logger.info(f"  Attempting to get indicators for {symbol}")
                data = self.data_collection_manager.get_symbol_indicators(collection_id, symbol)
                
                if data is not None and not data.empty:
                    self.logger.info(f"  ✓ Got indicators data for {symbol}: {len(data)} rows, columns: {list(data.columns)}")
                    self.logger.info(f"  Data sample for {symbol}: {data.head(2).to_dict()}")
                else:
                    self.logger.info(f"  ✗ No indicators data for {symbol}, trying basic data")
                    # If no indicators available, get basic data
                    data = self.data_collection_manager.get_symbol_data(collection_id, symbol)
                    
                    if data is not None and not data.empty:
                        self.logger.info(f"  ✓ Got basic data for {symbol}: {len(data)} rows, columns: {list(data.columns)}")
                        self.logger.info(f"  Data sample for {symbol}: {data.head(2).to_dict()}")
                    else:
                        self.logger.warning(f"  ✗ No data available for {symbol}")
                        return None
                
                if data is not None and not data.empty:
                    self.logger.info(f"  Scoring {symbol} with data...")
                    score = self.scorer.score_stock(symbol, data)
                    self.logger.info(f"  ✓ Score calculated for {symbol}: {score.total_score if score else 'None'}")
                    return score
                else:
                    self.logger.warning(f"  ✗ No data available for {symbol}")
                    return None
            else:
                self.logger.error("  ✗ No data collection manager available")
                return None
                
        except Exception as e:
            self.logger.error(f"  ✗ Error scoring {symbol}: {e}")
            return None
    
    def _generate_summary(self, stock_scores: List[StockScore]) -> Dict:
        """Generate summary statistics for the ranking."""
        if not stock_scores:
            return {}
        
        try:
            # Calculate summary statistics
            total_scores = [score.total_score for score in stock_scores]
            technical_scores = [score.technical_score for score in stock_scores]
            risk_scores = [score.risk_score for score in stock_scores]
            
            summary = {
                'total_stocks': len(stock_scores),
                'score_statistics': {
                    'mean_total_score': np.mean(total_scores),
                    'std_total_score': np.std(total_scores),
                    'min_total_score': np.min(total_scores),
                    'max_total_score': np.max(total_scores),
                    'mean_technical_score': np.mean(technical_scores),
                    'mean_risk_score': np.mean(risk_scores)
                },
                'top_performers': [
                    {
                        'symbol': score.symbol,
                        'rank': score.rank,
                        'total_score': score.total_score,
                        'explanation': score.explanation
                    }
                    for score in stock_scores[:10]  # Top 10
                ],
                'risk_categories': {
                    'low_risk': len([s for s in stock_scores if s.risk_score >= 70]),
                    'medium_risk': len([s for s in stock_scores if 50 <= s.risk_score < 70]),
                    'high_risk': len([s for s in stock_scores if s.risk_score < 50])
                },
                'recommendation_summary': {
                    'strong_buy': len([s for s in stock_scores if s.total_score >= 70]),
                    'hold': len([s for s in stock_scores if 50 <= s.total_score < 70]),
                    'avoid': len([s for s in stock_scores if s.total_score < 50])
                }
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating summary: {e}")
            return {}
    
    def get_top_stocks(self, collection_id: str, top_n: int = 10) -> List[StockScore]:
        """Get top N stocks from a collection."""
        try:
            result = self.rank_collection(collection_id)
            return result.ranked_stocks[:top_n]
        except Exception as e:
            self.logger.error(f"Error getting top stocks: {e}")
            return []
    
    def get_stock_analysis(self, collection_id: str, symbol: str) -> Optional[StockScore]:
        """Get detailed analysis for a specific stock."""
        try:
            score = self._score_stock_in_collection(collection_id, symbol)
            if score:
                # Get ranking context
                result = self.rank_collection(collection_id)
                for ranked_score in result.ranked_stocks:
                    if ranked_score.symbol == symbol:
                        score.rank = ranked_score.rank
                        break
            return score
        except Exception as e:
            self.logger.error(f"Error getting stock analysis: {e}")
            return None
    
    def export_ranking_report(self, collection_id: str, format: str = 'json') -> str:
        """Export ranking report in specified format."""
        try:
            result = self.rank_collection(collection_id)
            
            if format.lower() == 'json':
                return self._export_json(result)
            elif format.lower() == 'csv':
                return self._export_csv(result)
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            self.logger.error(f"Error exporting ranking report: {e}")
            raise
    
    def _export_json(self, result: RankingResult) -> str:
        """Export ranking result as JSON."""
        export_data = {
            'collection_id': result.collection_id,
            'timestamp': result.timestamp,
            'total_stocks': result.total_stocks,
            'summary': result.summary,
            'ranked_stocks': [
                {
                    'symbol': score.symbol,
                    'rank': score.rank,
                    'total_score': score.total_score,
                    'technical_score': score.technical_score,
                    'fundamental_score': score.fundamental_score,
                    'risk_score': score.risk_score,
                    'market_score': score.market_score,
                    'explanation': score.explanation,
                    'recommendations': score.recommendations
                }
                for score in result.ranked_stocks
            ]
        }
        
        return json.dumps(export_data, indent=2)
    
    def _export_csv(self, result: RankingResult) -> str:
        """Export ranking result as CSV."""
        import io
        
        output = io.StringIO()
        
        # Write header
        output.write("Rank,Symbol,Total_Score,Technical_Score,Fundamental_Score,Risk_Score,Market_Score,Explanation\n")
        
        # Write data
        for score in result.ranked_stocks:
            output.write(f"{score.rank},{score.symbol},{score.total_score:.2f},{score.technical_score:.2f},{score.fundamental_score:.2f},{score.risk_score:.2f},{score.market_score:.2f},\"{score.explanation}\"\n")
        
        return output.getvalue()
    
    def update_ranking_weights(self, weights: ScoringWeights):
        """Update the scoring weights for the ranking engine."""
        self.scorer.weights = weights
        self.logger.info("Updated ranking weights")
    
    def get_ranking_performance(self, collection_id: str, days_back: int = 30) -> Dict:
        """
        Analyze ranking performance over time.
        
        This would compare how well the rankings predicted actual performance.
        """
        # This is a placeholder for future implementation
        # In a real system, you would:
        # 1. Get historical rankings
        # 2. Compare with actual price performance
        # 3. Calculate correlation and accuracy metrics
        
        return {
            'collection_id': collection_id,
            'analysis_period_days': days_back,
            'performance_metrics': {
                'correlation_with_actual_returns': 0.0,  # Placeholder
                'ranking_accuracy': 0.0,  # Placeholder
                'top_performers_accuracy': 0.0  # Placeholder
            },
            'note': 'Performance analysis not yet implemented'
        } 