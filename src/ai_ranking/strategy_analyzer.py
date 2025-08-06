"""
Strategy Analyzer for Educational Content

This module provides educational analysis and explanations of trading strategies,
market conditions, and investment recommendations.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class StrategyInsight:
    """Educational insight about a trading strategy"""
    strategy_name: str
    description: str
    current_conditions: str
    recommendation: str
    risk_level: str
    time_horizon: str
    key_indicators: List[str]

@dataclass
class MarketAnalysis:
    """Market condition analysis"""
    market_regime: str
    volatility_level: str
    trend_direction: str
    sector_performance: Dict[str, str]
    recommendations: List[str]

class StrategyAnalyzer:
    """
    Analyzes trading strategies and provides educational insights.
    
    Features:
    - Strategy explanation and education
    - Market condition analysis
    - Risk assessment and recommendations
    - Educational content generation
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Define available strategies
        self.strategies = {
            'macd_momentum': {
                'name': 'MACD Momentum Strategy',
                'description': 'Uses MACD crossovers to identify momentum shifts',
                'indicators': ['MACD', 'EMA_12', 'EMA_26'],
                'risk_level': 'Medium',
                'time_horizon': 'Short to Medium term'
            },
            'rsi_mean_reversion': {
                'name': 'RSI Mean Reversion Strategy',
                'description': 'Trades oversold/overbought conditions using RSI',
                'indicators': ['RSI', 'Bollinger_Bands'],
                'risk_level': 'Medium to High',
                'time_horizon': 'Short term'
            },
            'trend_following': {
                'name': 'Trend Following Strategy',
                'description': 'Follows established price trends using moving averages',
                'indicators': ['EMA_20', 'EMA_50', 'ATR'],
                'risk_level': 'Low to Medium',
                'time_horizon': 'Medium to Long term'
            },
            'volatility_breakout': {
                'name': 'Volatility Breakout Strategy',
                'description': 'Trades breakouts from low volatility periods',
                'indicators': ['ATR', 'Bollinger_Bands', 'Volume'],
                'risk_level': 'High',
                'time_horizon': 'Short term'
            }
        }
    
    def analyze_stock_strategy(self, symbol: str, data: Dict, score: Dict) -> StrategyInsight:
        """
        Analyze the best strategy for a specific stock based on its characteristics.
        
        Args:
            symbol: Stock symbol
            data: Stock data and indicators
            score: Stock scoring results
            
        Returns:
            StrategyInsight with recommended strategy
        """
        try:
            # Determine best strategy based on stock characteristics
            technical_score = score.get('technical_score', 50)
            risk_score = score.get('risk_score', 50)
            
            # Strategy selection logic
            if technical_score >= 70 and risk_score >= 60:
                strategy_key = 'trend_following'
                recommendation = "Strong trend following opportunity"
            elif technical_score >= 60 and risk_score < 50:
                strategy_key = 'rsi_mean_reversion'
                recommendation = "Good mean reversion opportunity"
            elif technical_score < 50 and risk_score >= 70:
                strategy_key = 'volatility_breakout'
                recommendation = "Potential breakout opportunity"
            else:
                strategy_key = 'macd_momentum'
                recommendation = "Standard momentum strategy"
            
            strategy = self.strategies[strategy_key]
            
            # Generate current conditions analysis
            conditions = self._analyze_current_conditions(data, score)
            
            return StrategyInsight(
                strategy_name=strategy['name'],
                description=strategy['description'],
                current_conditions=conditions,
                recommendation=recommendation,
                risk_level=strategy['risk_level'],
                time_horizon=strategy['time_horizon'],
                key_indicators=strategy['indicators']
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing strategy for {symbol}: {e}")
            return self._create_default_insight()
    
    def _analyze_current_conditions(self, data: Dict, score: Dict) -> str:
        """Analyze current market conditions for the stock."""
        try:
            conditions = []
            
            technical_score = score.get('technical_score', 50)
            risk_score = score.get('risk_score', 50)
            
            # Technical condition analysis
            if technical_score >= 70:
                conditions.append("Strong technical indicators showing bullish momentum")
            elif technical_score >= 50:
                conditions.append("Mixed technical signals with moderate momentum")
            else:
                conditions.append("Technical indicators showing bearish pressure")
            
            # Risk condition analysis
            if risk_score >= 70:
                conditions.append("Low volatility environment suitable for trend strategies")
            elif risk_score >= 50:
                conditions.append("Moderate volatility requiring careful position sizing")
            else:
                conditions.append("High volatility requiring strict risk management")
            
            # Market context
            if technical_score >= 60 and risk_score >= 60:
                conditions.append("Favorable market conditions for active trading")
            elif technical_score < 40 or risk_score < 40:
                conditions.append("Challenging market conditions - consider defensive positions")
            else:
                conditions.append("Neutral market conditions - standard strategies apply")
            
            return ". ".join(conditions)
            
        except Exception as e:
            self.logger.error(f"Error analyzing current conditions: {e}")
            return "Market conditions analysis unavailable"
    
    def get_educational_content(self, topic: str) -> Dict:
        """Get educational content about trading topics."""
        educational_content = {
            'technical_analysis': {
                'title': 'Understanding Technical Analysis',
                'content': [
                    'Technical analysis uses historical price data to predict future movements',
                    'Key indicators include moving averages, RSI, MACD, and Bollinger Bands',
                    'Trend analysis helps identify market direction and momentum',
                    'Support and resistance levels guide entry and exit points'
                ],
                'key_concepts': ['Trend Analysis', 'Momentum Indicators', 'Volatility Measures', 'Support/Resistance']
            },
            'risk_management': {
                'title': 'Risk Management Fundamentals',
                'content': [
                    'Always use stop-loss orders to limit potential losses',
                    'Position sizing should be based on account size and risk tolerance',
                    'Diversification reduces portfolio risk across multiple assets',
                    'Risk-reward ratios should be favorable before entering trades'
                ],
                'key_concepts': ['Stop Losses', 'Position Sizing', 'Diversification', 'Risk-Reward Ratio']
            },
            'strategy_selection': {
                'title': 'Choosing the Right Trading Strategy',
                'content': [
                    'Match strategy to your risk tolerance and time horizon',
                    'Trend following works well in trending markets',
                    'Mean reversion strategies excel in sideways markets',
                    'Volatility strategies require active management'
                ],
                'key_concepts': ['Risk Tolerance', 'Time Horizon', 'Market Conditions', 'Strategy Fit']
            }
        }
        
        return educational_content.get(topic, {
            'title': 'Trading Education',
            'content': ['Educational content for this topic is being developed'],
            'key_concepts': ['Learning', 'Practice', 'Analysis', 'Improvement']
        })
    
    def analyze_market_conditions(self, collection_data: Dict) -> MarketAnalysis:
        """
        Analyze overall market conditions based on collection data.
        
        Args:
            collection_data: Data from the entire collection
            
        Returns:
            MarketAnalysis with market insights
        """
        try:
            # This is a simplified analysis
            # In a real implementation, you would analyze:
            # - Market breadth
            # - Sector rotation
            # - Volatility patterns
            # - Economic indicators
            
            market_regime = "Mixed"  # Placeholder
            volatility_level = "Moderate"  # Placeholder
            trend_direction = "Sideways"  # Placeholder
            
            sector_performance = {
                'Technology': 'Strong',
                'Healthcare': 'Moderate',
                'Financial': 'Weak',
                'Consumer': 'Mixed'
            }
            
            recommendations = [
                "Focus on stocks with strong technical indicators",
                "Use proper position sizing for risk management",
                "Monitor key support and resistance levels",
                "Consider sector rotation opportunities"
            ]
            
            return MarketAnalysis(
                market_regime=market_regime,
                volatility_level=volatility_level,
                trend_direction=trend_direction,
                sector_performance=sector_performance,
                recommendations=recommendations
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing market conditions: {e}")
            return self._create_default_market_analysis()
    
    def generate_learning_recommendations(self, user_profile: Dict) -> List[str]:
        """
        Generate personalized learning recommendations based on user profile.
        
        Args:
            user_profile: User's experience level and preferences
            
        Returns:
            List of learning recommendations
        """
        experience_level = user_profile.get('experience_level', 'beginner')
        
        recommendations = {
            'beginner': [
                "Start with basic technical indicators (MA, RSI)",
                "Practice paper trading before using real money",
                "Learn about risk management fundamentals",
                "Focus on one strategy at a time"
            ],
            'intermediate': [
                "Explore advanced indicators and combinations",
                "Study market structure and patterns",
                "Develop your own trading system",
                "Learn about portfolio management"
            ],
            'advanced': [
                "Optimize strategies using backtesting",
                "Study market microstructure",
                "Develop quantitative models",
                "Focus on risk-adjusted returns"
            ]
        }
        
        return recommendations.get(experience_level, recommendations['beginner'])
    
    def _create_default_insight(self) -> StrategyInsight:
        """Create default strategy insight when analysis fails."""
        return StrategyInsight(
            strategy_name="MACD Momentum Strategy",
            description="Standard momentum-based trading strategy",
            current_conditions="Market conditions analysis unavailable",
            recommendation="Use standard risk management practices",
            risk_level="Medium",
            time_horizon="Medium term",
            key_indicators=["MACD", "EMA_12", "EMA_26"]
        )
    
    def _create_default_market_analysis(self) -> MarketAnalysis:
        """Create default market analysis when analysis fails."""
        return MarketAnalysis(
            market_regime="Unknown",
            volatility_level="Unknown",
            trend_direction="Unknown",
            sector_performance={},
            recommendations=["Gather more market data for accurate analysis"]
        ) 