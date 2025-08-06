"""
Data Collection Integration with AI Ranking

This module integrates the AI ranking system with the existing data collection
infrastructure to provide intelligent stock ranking within the data collection context.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from ..ai_ranking.ranking_engine import StockRankingEngine
from ..ai_ranking.strategy_analyzer import StrategyAnalyzer
from ..ai_ranking.educational_ai import EducationalAI

logger = logging.getLogger(__name__)

class DataCollectionAIIntegration:
    """
    Integration layer between data collection and AI ranking systems.
    
    Features:
    - Seamless integration with existing data collection
    - Real-time ranking updates
    - Educational content generation
    - Strategy analysis and recommendations
    """
    
    def __init__(self, data_collection_manager):
        self.data_collection_manager = data_collection_manager
        self.ranking_engine = StockRankingEngine(data_collection_manager)
        self.strategy_analyzer = StrategyAnalyzer()
        self.educational_ai = EducationalAI()
        self.logger = logging.getLogger(__name__)
        
    def get_collection_ranking(self, collection_id: str, max_stocks: int = 50) -> Dict:
        """
        Get AI-powered ranking for a specific collection.
        
        Args:
            collection_id: ID of the data collection
            max_stocks: Maximum number of stocks to rank
            
        Returns:
            Dictionary with ranking results and educational content
        """
        try:
            self.logger.info(f"Generating AI ranking for collection: {collection_id}")
            
            # Get ranking results
            ranking_result = self.ranking_engine.rank_collection(collection_id, max_stocks)
            self.logger.info(f"Ranking engine returned {len(ranking_result.ranked_stocks)} stocks")
            self.logger.info(f"Total stocks in result: {ranking_result.total_stocks}")
            self.logger.info(f"Max stocks requested: {max_stocks}")
            self.logger.info(f"Array size from ranking engine: {len(ranking_result.ranked_stocks)}")
            
            # Debug: Print first few stocks
            if ranking_result.ranked_stocks:
                self.logger.info(f"First 5 stocks: {[s.symbol for s in ranking_result.ranked_stocks[:5]]}")
                self.logger.info(f"Last 5 stocks: {[s.symbol for s in ranking_result.ranked_stocks[-5:]]}")
                self.logger.info(f"All stock symbols: {[s.symbol for s in ranking_result.ranked_stocks]}")
            
            # Generate educational content
            educational_content = self._generate_educational_content(ranking_result)
            
            # Create comprehensive response
            response = {
                'success': True,
                'collection_id': collection_id,
                'timestamp': ranking_result.timestamp,
                'total_stocks': ranking_result.total_stocks,
                'ranking_summary': ranking_result.summary,
                'top_stocks': [
                    {
                        'rank': score.rank,
                        'symbol': score.symbol,
                        'total_score': score.total_score,
                        'technical_score': score.technical_score,
                        'fundamental_score': score.fundamental_score,
                        'risk_score': score.risk_score,
                        'market_score': score.market_score,
                        'explanation': score.explanation,
                        'recommendations': score.recommendations
                    }
                    for score in ranking_result.ranked_stocks  # Return all ranked stocks
                ],
                'educational_content': educational_content,
                'market_analysis': self._generate_market_analysis(ranking_result),
                'learning_recommendations': self._generate_learning_recommendations(ranking_result)
            }
            
            self.logger.info(f"Final response top_stocks array size: {len(response['top_stocks'])}")
            self.logger.info(f"Response total_stocks field: {response['total_stocks']}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error getting collection ranking: {e}")
            return {
                'success': False,
                'error': str(e),
                'collection_id': collection_id,
                'message': 'Unable to generate ranking at this time'
            }
    
    def get_stock_analysis(self, collection_id: str, symbol: str) -> Dict:
        """
        Get detailed AI analysis for a specific stock.
        
        Args:
            collection_id: ID of the data collection
            symbol: Stock symbol to analyze
            
        Returns:
            Dictionary with detailed stock analysis
        """
        try:
            # Get stock score and ranking
            stock_score = self.ranking_engine.get_stock_analysis(collection_id, symbol)
            
            if not stock_score:
                return {
                    'success': False,
                    'error': f'Unable to analyze {symbol}',
                    'symbol': symbol
                }
            
            # Get stock data for strategy analysis
            stock_data = self._get_stock_data_for_analysis(collection_id, symbol)
            
            # Generate strategy insight
            strategy_insight = self.strategy_analyzer.analyze_stock_strategy(
                symbol, stock_data, {
                    'technical_score': stock_score.technical_score,
                    'fundamental_score': stock_score.fundamental_score,
                    'risk_score': stock_score.risk_score,
                    'market_score': stock_score.market_score
                }
            )
            
            # Generate educational content
            educational_content = self.educational_ai.generate_strategy_explanation(
                strategy_insight.strategy_name, stock_data
            )
            
            response = {
                'success': True,
                'symbol': symbol,
                'collection_id': collection_id,
                'analysis': {
                    'rank': stock_score.rank,
                    'total_score': stock_score.total_score,
                    'technical_score': stock_score.technical_score,
                    'fundamental_score': stock_score.fundamental_score,
                    'risk_score': stock_score.risk_score,
                    'market_score': stock_score.market_score,
                    'explanation': stock_score.explanation,
                    'recommendations': stock_score.recommendations
                },
                'strategy_insight': {
                    'strategy_name': strategy_insight.strategy_name,
                    'description': strategy_insight.description,
                    'current_conditions': strategy_insight.current_conditions,
                    'recommendation': strategy_insight.recommendation,
                    'risk_level': strategy_insight.risk_level,
                    'time_horizon': strategy_insight.time_horizon,
                    'key_indicators': strategy_insight.key_indicators
                },
                'educational_content': educational_content,
                'learning_recommendations': self._generate_stock_learning_recommendations(stock_score)
            }
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error getting stock analysis for {symbol}: {e}")
            return {
                'success': False,
                'error': str(e),
                'symbol': symbol,
                'message': 'Unable to analyze stock at this time'
            }
    
    def get_ranking_performance(self, collection_id: str) -> Dict:
        """
        Get ranking performance metrics and insights.
        
        Args:
            collection_id: ID of the data collection
            
        Returns:
            Dictionary with performance metrics
        """
        try:
            performance = self.ranking_engine.get_ranking_performance(collection_id)
            
            return {
                'success': True,
                'collection_id': collection_id,
                'performance_metrics': performance,
                'insights': self._generate_performance_insights(performance)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting ranking performance: {e}")
            return {
                'success': False,
                'error': str(e),
                'collection_id': collection_id,
                'message': 'Unable to get performance metrics'
            }
    
    def export_ranking_report(self, collection_id: str, format: str = 'json') -> Dict:
        """
        Export ranking report in specified format.
        
        Args:
            collection_id: ID of the data collection
            format: Export format ('json' or 'csv')
            
        Returns:
            Dictionary with export data
        """
        try:
            report_data = self.ranking_engine.export_ranking_report(collection_id, format)
            
            return {
                'success': True,
                'collection_id': collection_id,
                'format': format,
                'data': report_data,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error exporting ranking report: {e}")
            return {
                'success': False,
                'error': str(e),
                'collection_id': collection_id,
                'message': 'Unable to export report'
            }
    
    def _generate_educational_content(self, ranking_result) -> Dict:
        """Generate educational content based on ranking results."""
        try:
            # Analyze top performers
            top_stocks = ranking_result.ranked_stocks[:5]
            
            # Generate insights
            insights = []
            for stock in top_stocks:
                if stock.total_score >= 70:
                    insights.append(f"{stock.symbol} shows strong technical indicators and low risk")
                elif stock.total_score >= 50:
                    insights.append(f"{stock.symbol} has mixed signals but potential for improvement")
            
            # Generate learning recommendations
            learning_recommendations = [
                "Focus on stocks with strong technical indicators",
                "Use proper risk management for all positions",
                "Monitor key support and resistance levels",
                "Consider sector rotation opportunities"
            ]
            
            return {
                'insights': insights,
                'learning_recommendations': learning_recommendations,
                'key_concepts': [
                    'Technical Analysis',
                    'Risk Management',
                    'Portfolio Diversification',
                    'Market Timing'
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error generating educational content: {e}")
            return {
                'insights': ['Educational content generation in progress'],
                'learning_recommendations': ['Focus on risk management'],
                'key_concepts': ['Learning', 'Practice', 'Analysis']
            }
    
    def _generate_market_analysis(self, ranking_result) -> Dict:
        """Generate market analysis based on ranking results."""
        try:
            # Analyze market conditions from ranking data
            scores = [stock.total_score for stock in ranking_result.ranked_stocks]
            technical_scores = [stock.technical_score for stock in ranking_result.ranked_stocks]
            risk_scores = [stock.risk_score for stock in ranking_result.ranked_stocks]
            
            # Determine market regime
            avg_technical = sum(technical_scores) / len(technical_scores) if technical_scores else 50
            avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 50
            
            if avg_technical >= 60 and avg_risk >= 60:
                market_regime = "Favorable"
                market_insight = "Strong technical indicators across the market"
            elif avg_technical < 40 or avg_risk < 40:
                market_regime = "Challenging"
                market_insight = "Market conditions require careful risk management"
            else:
                market_regime = "Mixed"
                market_insight = "Mixed market conditions with selective opportunities"
            
            return {
                'market_regime': market_regime,
                'market_insight': market_insight,
                'average_technical_score': round(avg_technical, 2),
                'average_risk_score': round(avg_risk, 2),
                'recommendations': [
                    "Focus on stocks with strong technical indicators",
                    "Use proper position sizing for risk management",
                    "Monitor market conditions for changes",
                    "Consider defensive positions if needed"
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error generating market analysis: {e}")
            return {
                'market_regime': 'Unknown',
                'market_insight': 'Market analysis unavailable',
                'recommendations': ['Use standard risk management practices']
            }
    
    def _generate_learning_recommendations(self, ranking_result) -> List[str]:
        """Generate learning recommendations based on ranking results."""
        try:
            recommendations = []
            
            # Analyze ranking patterns
            high_scoring_stocks = [s for s in ranking_result.ranked_stocks if s.total_score >= 70]
            low_risk_stocks = [s for s in ranking_result.ranked_stocks if s.risk_score >= 70]
            
            if len(high_scoring_stocks) > len(ranking_result.ranked_stocks) * 0.3:
                recommendations.append("Market conditions are favorable for active trading")
            else:
                recommendations.append("Focus on selective opportunities with strong fundamentals")
            
            if len(low_risk_stocks) > len(ranking_result.ranked_stocks) * 0.4:
                recommendations.append("Low volatility environment - good for trend strategies")
            else:
                recommendations.append("Higher volatility - use strict risk management")
            
            recommendations.extend([
                "Study technical analysis fundamentals",
                "Practice with paper trading",
                "Learn about risk management",
                "Monitor market conditions regularly"
            ])
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating learning recommendations: {e}")
            return ["Focus on risk management", "Continue learning and practicing"]
    
    def _generate_stock_learning_recommendations(self, stock_score) -> List[str]:
        """Generate learning recommendations for a specific stock."""
        try:
            recommendations = []
            
            if stock_score.total_score >= 70:
                recommendations.extend([
                    "This stock shows strong technical indicators",
                    "Consider learning about trend following strategies",
                    "Study momentum indicators and their applications"
                ])
            elif stock_score.total_score >= 50:
                recommendations.extend([
                    "This stock has mixed signals",
                    "Learn about confirmation techniques",
                    "Study risk management for uncertain conditions"
                ])
            else:
                recommendations.extend([
                    "This stock shows bearish signals",
                    "Learn about defensive trading strategies",
                    "Study risk management for challenging conditions"
                ])
            
            if stock_score.risk_score < 50:
                recommendations.append("Focus on risk management due to high volatility")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating stock learning recommendations: {e}")
            return ["Focus on risk management", "Continue learning trading fundamentals"]
    
    def _get_stock_data_for_analysis(self, collection_id: str, symbol: str) -> Dict:
        """Get stock data for strategy analysis."""
        try:
            if self.data_collection_manager:
                # Get recent data for analysis
                end_date = datetime.now()
                start_date = end_date.replace(day=end_date.day - 30)  # Last 30 days
                
                data = self.data_collection_manager.get_stock_data_with_indicators(
                    symbol,
                    start_date.strftime("%Y-%m-%d"),
                    end_date.strftime("%Y-%m-%d")
                )
                
                if data is not None and not data.empty:
                    return data.to_dict('records') if len(data) > 0 else {}
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Error getting stock data for analysis: {e}")
            return {}
    
    def _generate_performance_insights(self, performance: Dict) -> List[str]:
        """Generate insights from performance metrics."""
        try:
            insights = []
            
            # Add insights based on performance metrics
            if performance.get('correlation_with_actual_returns', 0) > 0.6:
                insights.append("Ranking system shows good correlation with actual performance")
            elif performance.get('correlation_with_actual_returns', 0) < 0.3:
                insights.append("Ranking system needs improvement in prediction accuracy")
            
            if performance.get('ranking_accuracy', 0) > 0.7:
                insights.append("High accuracy in identifying top performers")
            else:
                insights.append("Focus on improving ranking accuracy")
            
            insights.extend([
                "Continue monitoring ranking performance",
                "Consider adjusting scoring weights based on results",
                "Validate rankings against actual market performance"
            ])
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating performance insights: {e}")
            return ["Performance analysis in progress", "Continue monitoring results"] 