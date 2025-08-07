#!/usr/bin/env python3
"""
Hybrid AI Ranking Engine

This module implements a hybrid approach that:
1. Runs both OpenAI and local algorithms
2. Compares results and provides dual scoring
3. Uses comparison data to improve local algorithms
4. Provides insights on algorithm performance
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import time
import json
from dataclasses import dataclass

from .scoring_models import MultiFactorScorer
from .openai_integration import OpenAIStockAnalyzer
from .openai_storage import OpenAIAnalysisStorage

logger = logging.getLogger(__name__)

@dataclass
class DualScore:
    """Represents dual scoring results from OpenAI and local algorithms."""
    symbol: str
    openai_score: float
    local_score: float
    score_difference: float
    confidence_level: str
    explanation: str
    recommendations: List[str]

@dataclass
class HybridRankingResult:
    """Represents hybrid ranking results with dual scoring."""
    dual_scores: List[DualScore]
    total_stocks: int
    timestamp: datetime
    algorithm_performance: Dict
    improvement_insights: List[str]

class HybridRankingEngine:
    """
    Hybrid ranking engine that compares OpenAI vs local algorithms.
    """
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.local_scorer = MultiFactorScorer()
        self.openai_analyzer = OpenAIStockAnalyzer()
        self.openai_storage = OpenAIAnalysisStorage()
        self.logger = logging.getLogger(__name__)
        
        # Performance tracking
        self.algorithm_comparisons = []
        self.improvement_suggestions = []
        
    def rank_collection_hybrid(self, collection_id: str, max_stocks: int = 50) -> HybridRankingResult:
        """
        Rank stocks using both OpenAI and local algorithms with incremental updates.
        
        Args:
            collection_id: ID of the data collection
            max_stocks: Maximum number of stocks to rank
            
        Returns:
            HybridRankingResult with dual scoring and insights
        """
        try:
            self.logger.info(f"Starting incremental hybrid ranking for collection: {collection_id}")
            start_time = time.time()
            
            # Get collection symbols
            symbols = self.data_manager.get_collection_symbols(collection_id)
            if not symbols:
                self.logger.warning(f"No symbols found for collection {collection_id}")
                return self._create_empty_hybrid_result()
            
            # Limit symbols for performance (allow up to max_stocks)
            symbols = symbols[:max_stocks]
            self.logger.info(f"Processing {len(symbols)} symbols for hybrid ranking")
            
            # Get technical data for all symbols to check for changes
            technical_data_dict = {}
            market_context = self._get_market_context()
            
            for symbol in symbols:
                stock_data = self.data_manager.get_symbol_indicators(collection_id, symbol)
                if stock_data is not None and not stock_data.empty:
                    technical_data_dict[symbol] = self._prepare_technical_data_for_openai(stock_data)
            
            # Determine which symbols need fresh analysis
            symbols_needing_analysis = self.openai_storage.get_symbols_needing_analysis(
                collection_id, symbols, technical_data_dict, market_context
            )
            
            self.logger.info(f"Found {len(symbols_needing_analysis)} symbols needing fresh analysis")
            
            # Process stocks with parallel processing for better performance
            dual_scores = []
            batch_size = 5  # Smaller batch size for parallel processing
            
            # Use threading for parallel processing
            import threading
            import queue
            
            # Create a queue for results
            result_queue = queue.Queue()
            
            def process_batch(batch_symbols, batch_id):
                """Process a batch of symbols in parallel."""
                try:
                    batch_scores = self._process_hybrid_batch_incremental(collection_id, batch_symbols, symbols_needing_analysis)
                    result_queue.put((batch_id, batch_scores))
                    self.logger.info(f"Completed batch {batch_id} with {len(batch_scores)} symbols")
                except Exception as e:
                    self.logger.error(f"Error in batch {batch_id}: {e}")
                    result_queue.put((batch_id, []))
            
            # Start parallel processing
            threads = []
            for i in range(0, len(symbols), batch_size):
                batch = symbols[i:i + batch_size]
                batch_id = i // batch_size + 1
                
                thread = threading.Thread(target=process_batch, args=(batch, batch_id))
                thread.start()
                threads.append(thread)
                
                # Small delay to prevent overwhelming the system
                time.sleep(0.1)
            
            # Wait for all threads to complete with increased timeout
            timeout = 900  # 15 minutes timeout for comprehensive analysis with 112 symbols
            start_time = time.time()
            
            for thread in threads:
                thread.join(timeout=timeout)
                if thread.is_alive():
                    self.logger.warning("Thread timeout reached")
                    break
            
            # Collect results
            batch_results = {}
            while not result_queue.empty():
                batch_id, batch_scores = result_queue.get_nowait()
                batch_results[batch_id] = batch_scores
            
            # Combine results in order
            for batch_id in sorted(batch_results.keys()):
                dual_scores.extend(batch_results[batch_id])
            
            # Sort by combined score (average of OpenAI and local)
            dual_scores.sort(key=lambda x: (x.openai_score + x.local_score) / 2, reverse=True)
            
            # Generate algorithm performance insights
            algorithm_performance = self._analyze_algorithm_performance(dual_scores)
            improvement_insights = self._generate_improvement_insights(dual_scores)
            
            result = HybridRankingResult(
                dual_scores=dual_scores,
                total_stocks=len(dual_scores),
                timestamp=datetime.now(),
                algorithm_performance=algorithm_performance,
                improvement_insights=improvement_insights
            )
            
            elapsed_time = time.time() - start_time
            self.logger.info(f"Hybrid ranking completed in {elapsed_time:.2f}s")
            self.logger.info(f"Ranked {len(dual_scores)} stocks with dual scoring")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in hybrid ranking: {e}")
            return self._create_empty_hybrid_result()
    
    def _process_hybrid_batch(self, collection_id: str, symbols: List[str]) -> List[DualScore]:
        """Process a batch of stocks with dual scoring."""
        scores = []
        
        for symbol in symbols:
            try:
                # Get stock data
                stock_data = self.data_manager.get_symbol_indicators(collection_id, symbol)
                
                if stock_data is None or stock_data.empty:
                    self.logger.warning(f"No data available for {symbol}, skipping")
                    continue
                
                # Calculate local score with timeout protection
                try:
                    local_score = self._calculate_local_score(stock_data)
                except Exception as local_error:
                    self.logger.warning(f"Error calculating local score for {symbol}: {local_error}")
                    local_score = 50.0
                
                # Calculate OpenAI score with timeout protection
                try:
                    openai_score = self._calculate_openai_score(symbol, stock_data)
                except Exception as openai_error:
                    self.logger.warning(f"Error calculating OpenAI score for {symbol}: {openai_error}")
                    openai_score = 50.0
                
                # Calculate score difference
                score_difference = abs(openai_score - local_score)
                
                # Determine confidence level
                confidence_level = self._determine_confidence_level(score_difference)
                
                # Generate explanation
                explanation = self._generate_hybrid_explanation(symbol, openai_score, local_score, stock_data)
                
                # Generate recommendations
                recommendations = self._generate_hybrid_recommendations(openai_score, local_score, score_difference)
                
                # Store comparison for algorithm improvement
                self._store_algorithm_comparison(symbol, openai_score, local_score, stock_data)
                
                dual_score = DualScore(
                    symbol=symbol,
                    openai_score=openai_score,
                    local_score=local_score,
                    score_difference=score_difference,
                    confidence_level=confidence_level,
                    explanation=explanation,
                    recommendations=recommendations
                )
                
                scores.append(dual_score)
                
            except Exception as e:
                self.logger.error(f"Error processing {symbol} in hybrid mode: {e}")
                continue
        
        return scores
    
    def _process_hybrid_batch_incremental(self, collection_id: str, symbols: List[str], 
                                        symbols_needing_analysis: List[str]) -> List[DualScore]:
        """Process a batch of symbols with incremental hybrid scoring."""
        dual_scores = []
        
        for symbol in symbols:
            try:
                # Get stock data
                stock_data = self.data_manager.get_symbol_indicators(collection_id, symbol)
                
                if stock_data is None or stock_data.empty:
                    self.logger.warning(f"No data available for {symbol}")
                    continue
                
                # Calculate local score
                try:
                    local_score = self._calculate_local_score(stock_data)
                except Exception as local_error:
                    self.logger.warning(f"Error calculating local score for {symbol}: {local_error}")
                    local_score = 50.0
                
                # Check if we need fresh OpenAI analysis
                if symbol in symbols_needing_analysis:
                    self.logger.info(f"Performing fresh OpenAI analysis for {symbol}")
                    
                    # Calculate OpenAI score with comprehensive analysis
                    try:
                        openai_score = self._calculate_openai_score(symbol, stock_data)
                    except Exception as openai_error:
                        self.logger.warning(f"Error calculating OpenAI score for {symbol}: {openai_error}")
                        openai_score = 50.0
                    
                    # Store the analysis result
                    technical_data = self._prepare_technical_data_for_openai(stock_data)
                    market_context = self._get_market_context()
                    
                    analysis_data = {
                        'score': openai_score,
                        'analysis': f'Comprehensive analysis for {symbol}',
                        'technical_insights': 'Technical analysis completed',
                        'recommendation': self._get_recommendation_from_score(openai_score),
                        'confidence_level': self._determine_confidence_level(abs(openai_score - local_score))
                    }
                    
                    self.openai_storage.store_analysis_result(
                        symbol, collection_id, analysis_data, technical_data, market_context
                    )
                    
                else:
                    # Use cached OpenAI analysis
                    cached_analysis = self.openai_storage.get_latest_analysis(symbol, collection_id)
                    if cached_analysis:
                        self.logger.info(f"Using cached OpenAI analysis for {symbol}")
                        openai_score = cached_analysis['score']
                    else:
                        self.logger.warning(f"No cached analysis for {symbol}, performing fresh analysis")
                        try:
                            openai_score = self._calculate_openai_score(symbol, stock_data)
                        except Exception as openai_error:
                            self.logger.warning(f"Error calculating OpenAI score for {symbol}: {openai_error}")
                            openai_score = 50.0
                
                # Calculate score difference
                score_difference = abs(openai_score - local_score)
                
                # Determine confidence level
                confidence_level = self._determine_confidence_level(score_difference)
                
                # Generate explanation
                explanation = self._generate_hybrid_explanation(symbol, openai_score, local_score, stock_data)
                
                # Generate recommendations
                recommendations = self._generate_hybrid_recommendations(openai_score, local_score, score_difference)
                
                # Store comparison for algorithm improvement
                self._store_algorithm_comparison(symbol, openai_score, local_score, stock_data)
                
                # Create dual score
                dual_score = DualScore(
                    symbol=symbol,
                    openai_score=openai_score,
                    local_score=local_score,
                    score_difference=score_difference,
                    confidence_level=confidence_level,
                    explanation=explanation,
                    recommendations=recommendations
                )
                
                dual_scores.append(dual_score)
                
            except Exception as e:
                self.logger.error(f"Error processing {symbol} in incremental hybrid batch: {e}")
                continue
        
        return dual_scores
    
    def _get_recommendation_from_score(self, score: float) -> str:
        """Get recommendation based on score."""
        if score >= 75:
            return "Strong Buy"
        elif score >= 65:
            return "Buy"
        elif score >= 55:
            return "Hold"
        elif score >= 45:
            return "Sell"
        else:
            return "Strong Sell"
    
    def _calculate_local_score(self, stock_data) -> float:
        """Calculate score using local algorithms."""
        try:
            if stock_data.empty:
                return 50.0
            
            latest = stock_data.iloc[-1]
            
            # More sophisticated technical indicators analysis with correct column names
            rsi = latest.get('rsi_14', latest.get('rsi', 50))
            # RSI scoring: 100 for optimal (40-60), 80 for good (30-70), 60 for neutral, 40 for poor
            if 40 <= rsi <= 60:
                rsi_score = 100
            elif 30 <= rsi <= 70:
                rsi_score = 80
            elif 20 <= rsi <= 80:
                rsi_score = 60
            else:
                rsi_score = 40
            
            # MACD analysis with more granular scoring and correct column names
            macd = latest.get('macd_line_12_26', latest.get('macd', 0))
            macd_signal = latest.get('macd_signal_12_26_9', latest.get('macd_signal', 0))
            macd_histogram = macd - macd_signal
            
            if macd_histogram > 0 and macd > 0:
                macd_score = 100  # Strong bullish
            elif macd_histogram > 0:
                macd_score = 80   # Bullish
            elif macd_histogram < 0 and macd < 0:
                macd_score = 20   # Strong bearish
            elif macd_histogram < 0:
                macd_score = 40   # Bearish
            else:
                macd_score = 60   # Neutral
            
            # Moving average analysis with more granular scoring and correct column names
            close = latest.get('close', latest.get('Close', 0))
            sma_20 = latest.get('sma_20', close)
            sma_50 = latest.get('sma_50', close)
            
            if close > sma_20 > sma_50:
                ma_score = 100  # Strong uptrend
            elif close > sma_20:
                ma_score = 80   # Uptrend
            elif close > sma_50:
                ma_score = 60   # Neutral
            elif close < sma_20 < sma_50:
                ma_score = 20   # Strong downtrend
            else:
                ma_score = 40   # Downtrend
            
            # Enhanced volatility calculation with correct column names
            try:
                close_col = 'close' if 'close' in stock_data.columns else 'Close'
                if close_col in stock_data.columns and len(stock_data) > 1:
                    returns = stock_data[close_col].pct_change().dropna()
                    if len(returns) > 0:
                        volatility = returns.std() * (252 ** 0.5) * 100
                        # More sophisticated risk scoring
                        if volatility < 15:
                            risk_score = 90  # Low volatility
                        elif volatility < 25:
                            risk_score = 70  # Moderate volatility
                        elif volatility < 35:
                            risk_score = 50  # High volatility
                        else:
                            risk_score = 30  # Very high volatility
                    else:
                        risk_score = 60.0
                else:
                    risk_score = 60.0
            except Exception as vol_error:
                self.logger.warning(f"Error calculating volatility, using default risk score: {vol_error}")
                risk_score = 60.0
            
            # Enhanced weighted average with more weight on technical indicators
            technical_score = (rsi_score * 0.4 + macd_score * 0.4 + ma_score * 0.2)
            local_score = (technical_score * 0.7 + risk_score * 0.3)
            
            return min(max(local_score, 0), 100)
            
        except Exception as e:
            self.logger.error(f"Error calculating local score: {e}")
            return 50.0
    
    def _calculate_openai_score(self, symbol: str, stock_data) -> float:
        """Calculate score using OpenAI analysis."""
        try:
            # Prepare data for OpenAI
            technical_data = self._prepare_technical_data_for_openai(stock_data)
            
            # Get OpenAI analysis
            openai_analysis = self.openai_analyzer.analyze_stock_comprehensive(
                symbol=symbol,
                technical_data=technical_data,
                market_context=self._get_market_context()
            )
            
            # Extract score from OpenAI response
            if openai_analysis and 'score' in openai_analysis:
                return float(openai_analysis['score'])
            else:
                # Fallback to simplified OpenAI scoring
                return self._calculate_simplified_openai_score(symbol, stock_data)
                
        except Exception as e:
            self.logger.error(f"Error calculating OpenAI score for {symbol}: {e}")
            return 50.0
    
    def _calculate_simplified_openai_score(self, symbol: str, stock_data) -> float:
        """Calculate simplified OpenAI score when full analysis fails."""
        try:
            # Use a more sophisticated approach that mimics OpenAI thinking
            latest = stock_data.iloc[-1]
            
            # Price momentum with more granular scoring and correct column names
            close = latest.get('close', latest.get('Close', 0))
            sma_20 = latest.get('sma_20', close)
            sma_50 = latest.get('sma_50', close)
            
            if close > sma_20 > sma_50:
                price_momentum = 100  # Strong uptrend
            elif close > sma_20:
                price_momentum = 80   # Uptrend
            elif close > sma_50:
                price_momentum = 60   # Neutral
            else:
                price_momentum = 40   # Downtrend
            
            # Technical strength with RSI analysis and correct column names
            rsi = latest.get('rsi_14', latest.get('rsi', 50))
            if 40 <= rsi <= 60:
                technical_strength = 100  # Optimal
            elif 30 <= rsi <= 70:
                technical_strength = 80   # Good
            elif 20 <= rsi <= 80:
                technical_strength = 60   # Neutral
            else:
                technical_strength = 40   # Poor
            
            # MACD analysis with correct column names
            macd = latest.get('macd_line_12_26', latest.get('macd', 0))
            macd_signal = latest.get('macd_signal_12_26_9', latest.get('macd_signal', 0))
            macd_histogram = macd - macd_signal
            
            if macd_histogram > 0 and macd > 0:
                macd_strength = 100  # Strong bullish
            elif macd_histogram > 0:
                macd_strength = 80   # Bullish
            elif macd_histogram < 0 and macd < 0:
                macd_strength = 20   # Strong bearish
            else:
                macd_strength = 40   # Bearish/neutral
            
            # Market sentiment (enhanced)
            sentiment_score = 70  # Moderate positive sentiment
            
            # Weighted average with more emphasis on technical indicators
            openai_score = (price_momentum * 0.3 + 
                          technical_strength * 0.3 + 
                          macd_strength * 0.2 + 
                          sentiment_score * 0.2)
            
            return min(max(openai_score, 0), 100)
            
        except Exception as e:
            self.logger.error(f"Error calculating simplified OpenAI score: {e}")
            return 50.0
    
    def _determine_confidence_level(self, score_difference: float) -> str:
        """Determine confidence level based on score difference."""
        if score_difference <= 5:
            return "High Confidence"
        elif score_difference <= 15:
            return "Medium Confidence"
        elif score_difference <= 25:
            return "Low Confidence"
        else:
            return "Divergent Analysis"
    
    def _generate_hybrid_explanation(self, symbol: str, openai_score: float, 
                                   local_score: float, stock_data) -> str:
        """Generate explanation comparing both approaches."""
        try:
            score_diff = abs(openai_score - local_score)
            
            if score_diff <= 5:
                return f"Both AI and local algorithms agree on {symbol} with scores of {openai_score:.1f} and {local_score:.1f} respectively. High confidence in analysis."
            elif score_diff <= 15:
                return f"Moderate agreement between AI ({openai_score:.1f}) and local ({local_score:.1f}) analysis for {symbol}. Consider both perspectives."
            else:
                return f"Divergent analysis for {symbol}: AI suggests {openai_score:.1f} while local algorithm indicates {local_score:.1f}. Further investigation recommended."
                
        except Exception as e:
            self.logger.error(f"Error generating hybrid explanation: {e}")
            return f"Analysis completed for {symbol} with dual scoring approach."
    
    def _generate_hybrid_recommendations(self, openai_score: float, local_score: float, 
                                       score_difference: float) -> List[str]:
        """Generate recommendations based on dual scoring."""
        recommendations = []
        
        avg_score = (openai_score + local_score) / 2
        
        if avg_score >= 70:
            recommendations.append("Strong Buy - Both algorithms agree on positive outlook")
        elif avg_score >= 60:
            recommendations.append("Buy - Good potential with moderate agreement")
        elif avg_score >= 50:
            recommendations.append("Hold - Mixed signals, monitor closely")
        else:
            recommendations.append("Consider selling - Both algorithms indicate poor performance")
        
        if score_difference <= 5:
            recommendations.append("High algorithm agreement - confident recommendation")
        elif score_difference <= 15:
            recommendations.append("Moderate algorithm agreement - consider both perspectives")
        else:
            recommendations.append("Algorithm divergence - requires additional analysis")
        
        return recommendations
    
    def _analyze_algorithm_performance(self, dual_scores: List[DualScore]) -> Dict:
        """Analyze performance differences between algorithms."""
        if not dual_scores:
            return {}
        
        try:
            differences = [score.score_difference for score in dual_scores]
            openai_scores = [score.openai_score for score in dual_scores]
            local_scores = [score.local_score for score in dual_scores]
            
            avg_difference = sum(differences) / len(differences)
            avg_openai = sum(openai_scores) / len(openai_scores)
            avg_local = sum(local_scores) / len(local_scores)
            
            # Calculate correlation
            correlation = self._calculate_correlation(openai_scores, local_scores)
            
            return {
                'average_score_difference': round(avg_difference, 2),
                'average_openai_score': round(avg_openai, 2),
                'average_local_score': round(avg_local, 2),
                'algorithm_correlation': round(correlation, 3),
                'high_confidence_count': len([s for s in dual_scores if s.confidence_level == "High Confidence"]),
                'divergent_analysis_count': len([s for s in dual_scores if s.confidence_level == "Divergent Analysis"])
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing algorithm performance: {e}")
            return {}
    
    def _calculate_correlation(self, scores1: List[float], scores2: List[float]) -> float:
        """Calculate correlation between two score lists."""
        try:
            if len(scores1) != len(scores2) or len(scores1) < 2:
                return 0.0
            
            n = len(scores1)
            sum1, sum2, sum1_sq, sum2_sq, sum_prod = 0, 0, 0, 0, 0
            
            for i in range(n):
                sum1 += scores1[i]
                sum2 += scores2[i]
                sum1_sq += scores1[i] ** 2
                sum2_sq += scores2[i] ** 2
                sum_prod += scores1[i] * scores2[i]
            
            numerator = n * sum_prod - sum1 * sum2
            denominator = ((n * sum1_sq - sum1 ** 2) * (n * sum2_sq - sum2 ** 2)) ** 0.5
            
            if denominator == 0:
                return 0.0
            
            return numerator / denominator
            
        except Exception as e:
            self.logger.error(f"Error calculating correlation: {e}")
            return 0.0
    
    def _generate_improvement_insights(self, dual_scores: List[DualScore]) -> List[str]:
        """Generate insights for algorithm improvement."""
        insights = []
        
        try:
            # Analyze patterns in divergent cases
            divergent_cases = [s for s in dual_scores if s.confidence_level == "Divergent Analysis"]
            
            if divergent_cases:
                insights.append(f"Found {len(divergent_cases)} cases with significant algorithm divergence")
                insights.append("Consider reviewing technical indicator weights for these stocks")
            
            # Analyze high-confidence cases
            high_confidence = [s for s in dual_scores if s.confidence_level == "High Confidence"]
            
            if high_confidence:
                insights.append(f"Algorithm agreement in {len(high_confidence)} cases - validate these patterns")
            
            # Performance insights
            avg_diff = sum(s.score_difference for s in dual_scores) / len(dual_scores)
            if avg_diff > 20:
                insights.append("High average divergence suggests need for algorithm refinement")
            elif avg_diff < 10:
                insights.append("Good algorithm alignment - consider expanding analysis scope")
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating improvement insights: {e}")
            return ["Analysis insights generation failed"]
    
    def _store_algorithm_comparison(self, symbol: str, openai_score: float, 
                                  local_score: float, stock_data):
        """Store comparison data for algorithm improvement."""
        try:
            comparison = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'openai_score': openai_score,
                'local_score': local_score,
                'difference': abs(openai_score - local_score),
                'technical_data': self._extract_technical_features(stock_data)
            }
            
            self.algorithm_comparisons.append(comparison)
            
            # Keep only recent comparisons (last 1000)
            if len(self.algorithm_comparisons) > 1000:
                self.algorithm_comparisons = self.algorithm_comparisons[-1000:]
                
        except Exception as e:
            self.logger.error(f"Error storing algorithm comparison: {e}")
    
    def _extract_technical_features(self, stock_data) -> Dict:
        """Extract technical features for algorithm improvement."""
        try:
            if stock_data.empty:
                return {}
            
            latest = stock_data.iloc[-1]
            
            return {
                'rsi': latest.get('rsi', 50),
                'macd': latest.get('macd', 0),
                'macd_signal': latest.get('macd_signal', 0),
                'sma_20': latest.get('sma_20', 0),
                'sma_50': latest.get('sma_50', 0),
                'close': latest.get('Close', 0)
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting technical features: {e}")
            return {}
    
    def _prepare_technical_data_for_openai(self, stock_data) -> Dict:
        """Prepare technical data for OpenAI analysis."""
        try:
            if stock_data.empty:
                return {}
            
            latest = stock_data.iloc[-1]
            
            return {
                'current_price': latest.get('close', latest.get('Close', 0)),
                'rsi': latest.get('rsi_14', latest.get('rsi', 50)),
                'macd': latest.get('macd_line_12_26', latest.get('macd', 0)),
                'macd_signal': latest.get('macd_signal_12_26_9', latest.get('macd_signal', 0)),
                'sma_20': latest.get('sma_20', 0),
                'sma_50': latest.get('sma_50', 0),
                'volume': latest.get('volume', latest.get('Volume', 0))
            }
            
        except Exception as e:
            self.logger.error(f"Error preparing technical data for OpenAI: {e}")
            return {}
    
    def _get_market_context(self) -> Dict:
        """Get current market context for OpenAI analysis."""
        try:
            # This could be enhanced with real market data
            return {
                'market_regime': 'bullish',  # Placeholder
                'volatility_level': 'moderate',
                'sector_performance': 'mixed'
            }
        except Exception as e:
            self.logger.error(f"Error getting market context: {e}")
            return {}
    
    def _create_empty_hybrid_result(self) -> HybridRankingResult:
        """Create an empty hybrid ranking result."""
        return HybridRankingResult(
            dual_scores=[],
            total_stocks=0,
            timestamp=datetime.now(),
            algorithm_performance={},
            improvement_insights=["No data available for hybrid analysis"]
        )
    
    def export_algorithm_improvement_data(self, filename: str = None) -> str:
        """Export algorithm comparison data for improvement analysis."""
        try:
            if not filename:
                filename = f"algorithm_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'total_comparisons': len(self.algorithm_comparisons),
                'comparisons': self.algorithm_comparisons,
                'performance_summary': self._analyze_algorithm_performance(
                    [DualScore(s['symbol'], s['openai_score'], s['local_score'], 
                              s['difference'], '', '', []) for s in self.algorithm_comparisons]
                )
            }
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            self.logger.info(f"Exported algorithm improvement data to {filename}")
            return filename
            
        except Exception as e:
            self.logger.error(f"Error exporting algorithm improvement data: {e}")
            return ""
    
    def get_cached_hybrid_ranking(self, collection_id: str) -> Optional[Dict]:
        """Get cached hybrid ranking data for a collection."""
        try:
            import os
            import json
            from pathlib import Path
            
            cache_dir = Path("data/cache")
            cache_dir.mkdir(exist_ok=True)
            cache_file = cache_dir / f"hybrid_ranking_cache_{collection_id}.json"
            
            if cache_file.exists():
                # Check if cache is recent (less than 1 hour old)
                cache_age = datetime.now().timestamp() - cache_file.stat().st_mtime
                if cache_age < 3600:  # 1 hour
                    with open(cache_file, 'r') as f:
                        cached_data = json.load(f)
                        self.logger.info(f"Returning cached hybrid ranking for {collection_id}")
                        return cached_data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting cached hybrid ranking: {e}")
            return None
    
    def store_hybrid_ranking_cache(self, collection_id: str, ranking_data: Dict):
        """Store hybrid ranking data in cache."""
        try:
            import os
            import json
            from pathlib import Path
            
            cache_dir = Path("data/cache")
            cache_dir.mkdir(exist_ok=True)
            cache_file = cache_dir / f"hybrid_ranking_cache_{collection_id}.json"
            
            with open(cache_file, 'w') as f:
                json.dump(ranking_data, f, indent=2)
            
            self.logger.info(f"Stored hybrid ranking cache for {collection_id}")
            
        except Exception as e:
            self.logger.error(f"Error storing hybrid ranking cache: {e}") 