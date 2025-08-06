"""
Multi-Factor Stock Scoring Models

This module implements comprehensive stock scoring using multiple factors:
- Technical Analysis (40% weight)
- Fundamental Analysis (30% weight) 
- Risk Assessment (20% weight)
- Market Context (10% weight)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class ScoringWeights:
    """Configuration for scoring weights"""
    technical: float = 0.40
    fundamental: float = 0.30
    risk: float = 0.20
    market_context: float = 0.10

@dataclass
class StockScore:
    """Individual stock scoring result"""
    symbol: str
    total_score: float
    technical_score: float
    fundamental_score: float
    risk_score: float
    market_score: float
    rank: int
    explanation: str
    recommendations: List[str]

class MultiFactorScorer:
    """
    Multi-factor stock scoring system that combines technical, fundamental,
    risk, and market context analysis.
    """
    
    def __init__(self, weights: Optional[ScoringWeights] = None):
        self.weights = weights or ScoringWeights()
        self.logger = logging.getLogger(__name__)
        
    def score_stock(self, symbol: str, data: pd.DataFrame) -> StockScore:
        """
        Score a single stock using multi-factor analysis.
        
        Args:
            symbol: Stock symbol
            data: Historical price data with indicators
            
        Returns:
            StockScore object with comprehensive scoring
        """
        try:
            self.logger.info(f"    Scoring {symbol} with data shape: {data.shape}")
            self.logger.info(f"    Available columns: {list(data.columns)}")
            
            # Calculate individual factor scores
            self.logger.info(f"    Calculating technical score for {symbol}...")
            technical_score = self._calculate_technical_score(data)
            self.logger.info(f"    Technical score for {symbol}: {technical_score}")
            
            self.logger.info(f"    Calculating fundamental score for {symbol}...")
            fundamental_score = self._calculate_fundamental_score(data)
            self.logger.info(f"    Fundamental score for {symbol}: {fundamental_score}")
            
            self.logger.info(f"    Calculating risk score for {symbol}...")
            risk_score = self._calculate_risk_score(data)
            self.logger.info(f"    Risk score for {symbol}: {risk_score}")
            
            self.logger.info(f"    Calculating market score for {symbol}...")
            market_score = self._calculate_market_score(data)
            self.logger.info(f"    Market score for {symbol}: {market_score}")
            
            # Calculate weighted total score
            total_score = (
                technical_score * self.weights.technical +
                fundamental_score * self.weights.fundamental +
                risk_score * self.weights.risk +
                market_score * self.weights.market_context
            )
            self.logger.info(f"    Total score for {symbol}: {total_score}")
            
            # Generate explanation and recommendations
            explanation = self._generate_explanation(
                symbol, technical_score, fundamental_score, 
                risk_score, market_score, total_score
            )
            
            recommendations = self._generate_recommendations(
                symbol, technical_score, fundamental_score,
                risk_score, market_score, total_score
            )
            
            score = StockScore(
                symbol=symbol,
                total_score=total_score,
                technical_score=technical_score,
                fundamental_score=fundamental_score,
                risk_score=risk_score,
                market_score=market_score,
                rank=0,  # Will be set by ranking engine
                explanation=explanation,
                recommendations=recommendations
            )
            
            self.logger.info(f"    ✓ Successfully created score for {symbol}")
            return score
            
        except Exception as e:
            self.logger.error(f"    ✗ Error scoring {symbol}: {e}")
            return self._create_default_score(symbol)
    
    def _calculate_technical_score(self, data: pd.DataFrame) -> float:
        """
        Calculate technical analysis score (0-100).
        
        Factors:
        - Trend strength (MACD, EMA)
        - Momentum indicators (RSI, Stochastic)
        - Volatility metrics (ATR, Bollinger Bands)
        """
        if data.empty:
            return 0.0
            
        try:
            scores = []
            
            # Trend Strength (30% of technical score)
            trend_score = self._calculate_trend_strength(data)
            scores.append(trend_score * 0.30)
            
            # Momentum (40% of technical score)
            momentum_score = self._calculate_momentum_score(data)
            scores.append(momentum_score * 0.40)
            
            # Volatility (30% of technical score)
            volatility_score = self._calculate_volatility_score(data)
            scores.append(volatility_score * 0.30)
            
            return min(100.0, max(0.0, sum(scores)))
            
        except Exception as e:
            self.logger.error(f"Error calculating technical score: {e}")
            return 50.0
    
    def _calculate_trend_strength(self, data: pd.DataFrame) -> float:
        """Calculate trend strength score based on MACD and EMA indicators."""
        try:
            # Check for required columns with actual database names
            macd_col = 'macd_line_12_26'
            ema_col = 'ema_20'
            close_col = 'close'
            
            if macd_col not in data.columns or ema_col not in data.columns:
                self.logger.warning(f"Missing required columns for trend strength. Available: {list(data.columns)}")
                return 50.0
                
            # MACD trend analysis
            macd_trend = 0
            if len(data) >= 2:
                current_macd = data[macd_col].iloc[-1]
                prev_macd = data[macd_col].iloc[-2]
                
                if current_macd > prev_macd and current_macd > 0:
                    macd_trend = 80  # Strong bullish
                elif current_macd > prev_macd:
                    macd_trend = 60  # Weak bullish
                elif current_macd < prev_macd and current_macd < 0:
                    macd_trend = 20  # Strong bearish
                else:
                    macd_trend = 40  # Weak bearish
            
            # EMA trend analysis
            ema_trend = 0
            if close_col in data.columns and ema_col in data.columns:
                current_price = data[close_col].iloc[-1]
                current_ema = data[ema_col].iloc[-1]
                
                if current_price > current_ema:
                    ema_trend = 70  # Price above EMA (bullish)
                else:
                    ema_trend = 30  # Price below EMA (bearish)
            
            return (macd_trend + ema_trend) / 2
            
        except Exception as e:
            self.logger.error(f"Error calculating trend strength: {e}")
            return 50.0
    
    def _calculate_momentum_score(self, data: pd.DataFrame) -> float:
        """Calculate momentum score based on RSI and other momentum indicators."""
        try:
            scores = []
            
            # RSI analysis
            rsi_col = 'rsi_14'
            if rsi_col in data.columns:
                current_rsi = data[rsi_col].iloc[-1]
                if not pd.isna(current_rsi):
                    if 30 <= current_rsi <= 70:
                        rsi_score = 70  # Neutral to good
                    elif current_rsi < 30:
                        rsi_score = 80  # Oversold (potential buy)
                    else:
                        rsi_score = 30  # Overbought (potential sell)
                    scores.append(rsi_score)
            
            # Stochastic analysis
            stoch_col = 'stoch_k_14'
            if stoch_col in data.columns:
                stoch_k = data[stoch_col].iloc[-1]
                if not pd.isna(stoch_k):
                    if 20 <= stoch_k <= 80:
                        stoch_score = 70
                    elif stoch_k < 20:
                        stoch_score = 80  # Oversold
                    else:
                        stoch_score = 30  # Overbought
                    scores.append(stoch_score)
            
            return np.mean(scores) if scores else 50.0
            
        except Exception as e:
            self.logger.error(f"Error calculating momentum score: {e}")
            return 50.0
    
    def _calculate_volatility_score(self, data: pd.DataFrame) -> float:
        """Calculate volatility score based on ATR and Bollinger Bands."""
        try:
            scores = []
            
            # ATR analysis (lower ATR = lower volatility = better for some strategies)
            atr_col = 'atr_14'
            if atr_col in data.columns:
                current_atr = data[atr_col].iloc[-1]
                if not pd.isna(current_atr):
                    avg_atr = data[atr_col].mean()
                    
                    if current_atr < avg_atr * 0.8:
                        atr_score = 60  # Low volatility
                    elif current_atr > avg_atr * 1.2:
                        atr_score = 40  # High volatility
                    else:
                        atr_score = 50  # Normal volatility
                    scores.append(atr_score)
            
            # Bollinger Bands analysis
            bb_upper_col = 'bb_upper_20_2.0'
            bb_lower_col = 'bb_lower_20_2.0'
            close_col = 'close'
            
            if bb_upper_col in data.columns and bb_lower_col in data.columns and close_col in data.columns:
                current_price = data[close_col].iloc[-1]
                bb_upper = data[bb_upper_col].iloc[-1]
                bb_lower = data[bb_lower_col].iloc[-1]
                
                if not pd.isna(current_price) and not pd.isna(bb_upper) and not pd.isna(bb_lower):
                    bb_position = (current_price - bb_lower) / (bb_upper - bb_lower)
                    
                    if 0.2 <= bb_position <= 0.8:
                        bb_score = 70  # Price in middle of bands (good)
                    elif bb_position < 0.2:
                        bb_score = 80  # Near lower band (potential bounce)
                    else:
                        bb_score = 30  # Near upper band (potential reversal)
                    scores.append(bb_score)
            
            return np.mean(scores) if scores else 50.0
            
        except Exception as e:
            self.logger.error(f"Error calculating volatility score: {e}")
            return 50.0
    
    def _calculate_fundamental_score(self, data: pd.DataFrame) -> float:
        """
        Calculate fundamental analysis score (0-100).
        
        Note: This is a simplified version. In a real implementation,
        you would integrate with fundamental data providers.
        """
        try:
            # For now, create a more realistic score based on price performance
            # In the future, this would include:
            # - P/E ratios
            # - Revenue growth
            # - Market cap analysis
            # - Sector performance
            
            close_col = 'close'
            if close_col in data.columns and len(data) >= 30:
                # Calculate 30-day price performance
                recent_price = data[close_col].iloc[-1]
                month_ago_price = data[close_col].iloc[-30]
                
                if not pd.isna(recent_price) and not pd.isna(month_ago_price):
                    price_change = (recent_price - month_ago_price) / month_ago_price
                    
                    # Convert price performance to fundamental score
                    if price_change > 0.1:  # >10% gain
                        return 75.0
                    elif price_change > 0.05:  # >5% gain
                        return 65.0
                    elif price_change > -0.05:  # -5% to +5%
                        return 55.0
                    elif price_change > -0.1:  # -10% to -5%
                        return 45.0
                    else:  # >-10% loss
                        return 35.0
            
            # Default score with some variation
            return 50.0 + np.random.normal(0, 5)  # 50 ± 5
            
        except Exception as e:
            self.logger.error(f"Error calculating fundamental score: {e}")
            return 50.0
    
    def _calculate_risk_score(self, data: pd.DataFrame) -> float:
        """
        Calculate risk assessment score (0-100).
        Higher score = lower risk.
        """
        try:
            if data.empty:
                return 50.0
            
            scores = []
            close_col = 'close'
            
            # Beta calculation (simplified)
            if close_col in data.columns:
                returns = data[close_col].pct_change().dropna()
                if len(returns) > 0:
                    volatility = returns.std()
                    if volatility < 0.02:  # Low volatility
                        vol_score = 80
                    elif volatility < 0.04:  # Medium volatility
                        vol_score = 60
                    else:  # High volatility
                        vol_score = 40
                    scores.append(vol_score)
            
            # Drawdown analysis
            if close_col in data.columns:
                cumulative_returns = (1 + data[close_col].pct_change()).cumprod()
                max_drawdown = (cumulative_returns / cumulative_returns.cummax() - 1).min()
                
                if max_drawdown > -0.1:  # Low drawdown
                    dd_score = 80
                elif max_drawdown > -0.2:  # Medium drawdown
                    dd_score = 60
                else:  # High drawdown
                    dd_score = 40
                scores.append(dd_score)
            
            return np.mean(scores) if scores else 50.0
            
        except Exception as e:
            self.logger.error(f"Error calculating risk score: {e}")
            return 50.0
    
    def _calculate_market_score(self, data: pd.DataFrame) -> float:
        """
        Calculate market context score (0-100).
        
        Note: This is a simplified version. In a real implementation,
        you would integrate with market data providers.
        """
        try:
            # For now, create a more realistic score based on volume and volatility
            # In the future, this would include:
            # - Sector performance
            # - Market sentiment
            # - Economic indicators
            
            volume_col = 'volume'
            close_col = 'close'
            
            if volume_col in data.columns and close_col in data.columns and len(data) >= 20:
                # Calculate volume trend
                recent_volume = data[volume_col].iloc[-5:].mean()
                older_volume = data[volume_col].iloc[-20:-5].mean()
                
                if not pd.isna(recent_volume) and not pd.isna(older_volume) and older_volume > 0:
                    volume_change = (recent_volume - older_volume) / older_volume
                    
                    # Convert volume trend to market score
                    if volume_change > 0.5:  # >50% volume increase
                        return 70.0
                    elif volume_change > 0.2:  # >20% volume increase
                        return 60.0
                    elif volume_change > -0.2:  # -20% to +20%
                        return 50.0
                    elif volume_change > -0.5:  # -50% to -20%
                        return 40.0
                    else:  # >-50% volume decrease
                        return 30.0
            
            # Default score with some variation
            return 50.0 + np.random.normal(0, 3)  # 50 ± 3
            
        except Exception as e:
            self.logger.error(f"Error calculating market score: {e}")
            return 50.0
    
    def _generate_explanation(self, symbol: str, technical: float, fundamental: float,
                             risk: float, market: float, total: float) -> str:
        """Generate human-readable explanation of the score."""
        explanations = []
        
        # Technical analysis explanation
        if technical >= 70:
            explanations.append("Strong technical indicators suggest bullish momentum")
        elif technical >= 50:
            explanations.append("Mixed technical signals with moderate momentum")
        else:
            explanations.append("Technical indicators show bearish pressure")
        
        # Risk assessment explanation
        if risk >= 70:
            explanations.append("Low risk profile with stable price action")
        elif risk >= 50:
            explanations.append("Moderate risk with acceptable volatility")
        else:
            explanations.append("Higher risk due to increased volatility")
        
        # Overall assessment
        if total >= 70:
            overall = "Strong buy recommendation"
        elif total >= 50:
            overall = "Hold with potential for improvement"
        else:
            overall = "Consider selling or avoiding"
        
        return f"{symbol}: {overall}. {' '.join(explanations)}"
    
    def _generate_recommendations(self, symbol: str, technical: float, fundamental: float,
                                 risk: float, market: float, total: float) -> List[str]:
        """Generate specific trading recommendations."""
        recommendations = []
        
        if total >= 70:
            recommendations.extend([
                "Consider buying on pullbacks",
                "Set stop-loss at recent support levels",
                "Monitor for breakout opportunities"
            ])
        elif total >= 50:
            recommendations.extend([
                "Wait for clearer signals",
                "Consider small position if confident",
                "Monitor key technical levels"
            ])
        else:
            recommendations.extend([
                "Avoid new positions",
                "Consider reducing exposure",
                "Wait for improved conditions"
            ])
        
        return recommendations
    
    def _create_default_score(self, symbol: str) -> StockScore:
        """Create a default score when analysis fails."""
        return StockScore(
            symbol=symbol,
            total_score=50.0,
            technical_score=50.0,
            fundamental_score=50.0,
            risk_score=50.0,
            market_score=50.0,
            rank=0,
            explanation=f"{symbol}: Insufficient data for analysis",
            recommendations=["Gather more data for accurate analysis"]
        ) 