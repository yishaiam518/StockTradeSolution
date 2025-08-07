#!/usr/bin/env python3
"""
OpenAI Integration for Enhanced AI Stock Analysis

This module provides OpenAI/GPT integration for:
1. Dynamic stock explanations
2. Comparative analysis between our system and AI
3. Enhanced market insights
4. Professional-grade investment recommendations
"""

import logging
import os
from typing import Dict, List, Optional, Tuple
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None

class OpenAIStockAnalyzer:
    """
    OpenAI-powered stock analysis for enhanced explanations and insights.
    
    Features:
    - Dynamic explanations based on stock characteristics
    - Comparative analysis between technical and AI insights
    - Market sentiment integration
    - Professional investment recommendations
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = None
        self.api_key = os.getenv('OPENAI_API_KEY')
        
        if not self.api_key:
            self.logger.warning("OpenAI API key not found in environment variables")
            return
            
        if not OPENAI_AVAILABLE:
            self.logger.warning("OpenAI package not installed")
            return
            
        try:
            self.client = openai.OpenAI(api_key=self.api_key)
            self.logger.info("OpenAI client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI client: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if OpenAI integration is available."""
        return self.client is not None and self.api_key is not None
    
    def generate_stock_explanation(self, symbol: str, scores: Dict[str, float],
                                   technical_data: Optional[Dict] = None,
                                   market_context: Optional[Dict] = None) -> str:
        """
        Generate AI-powered stock explanation.
        """
        try:
            if not self.client:
                return "OpenAI analysis not available"
            
            # Build prompt for explanation
            prompt = self._build_explanation_prompt(symbol, scores, technical_data, market_context)
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert stock analyst. Provide clear, concise explanations."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"Error generating stock explanation: {e}")
            return f"Analysis explanation failed: {str(e)}"
    
    def analyze_stock_comprehensive(self, symbol: str, technical_data: Optional[Dict] = None,
                                   market_context: Optional[Dict] = None) -> Dict:
        """
        Perform comprehensive stock analysis using OpenAI.
        
        Args:
            symbol: Stock symbol
            technical_data: Technical indicators data
            market_context: Market context information
            
        Returns:
            Dictionary with comprehensive analysis including score
        """
        try:
            if not self.client:
                self.logger.warning("OpenAI client not available")
                return {'score': 50.0, 'analysis': 'OpenAI not available'}
            
            # Prepare prompt for comprehensive analysis
            prompt = self._build_comprehensive_analysis_prompt(symbol, technical_data, market_context)
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert stock analyst. Provide comprehensive analysis with numerical scores (0-100) and detailed insights."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            analysis_text = response.choices[0].message.content
            
            # Extract score from response
            score = self._extract_score_from_analysis(analysis_text)
            
            return {
                'score': score,
                'analysis': analysis_text,
                'technical_insights': self._extract_technical_insights(analysis_text),
                'recommendation': self._extract_recommendation(analysis_text)
            }
            
        except Exception as e:
            self.logger.error(f"Error in comprehensive stock analysis: {e}")
            return {'score': 50.0, 'analysis': f'Analysis failed: {str(e)}'}
    
    def _build_comprehensive_analysis_prompt(self, symbol: str, technical_data: Dict, market_context: Dict) -> str:
        """Build comprehensive analysis prompt for OpenAI."""
        prompt = f"""
        Analyze {symbol} comprehensively and provide a numerical score (0-100) based on:
        
        Technical Data:
        - Current Price: ${technical_data.get('current_price', 0):.2f}
        - RSI: {technical_data.get('rsi', 50):.1f}
        - MACD: {technical_data.get('macd', 0):.3f}
        - MACD Signal: {technical_data.get('macd_signal', 0):.3f}
        - SMA 20: ${technical_data.get('sma_20', 0):.2f}
        - SMA 50: ${technical_data.get('sma_50', 0):.2f}
        - Volume: {technical_data.get('volume', 0):,.0f}
        
        Market Context:
        - Market Regime: {market_context.get('market_regime', 'unknown')}
        - Volatility: {market_context.get('volatility_level', 'unknown')}
        
        Provide:
        1. A numerical score (0-100) where 0=poor, 50=neutral, 100=excellent
        2. Brief technical analysis
        3. Investment recommendation (Buy/Hold/Sell)
        4. Key risks and opportunities
        
        Format your response with clear sections and include the score prominently.
        """
        return prompt
    
    def _extract_score_from_analysis(self, analysis_text: str) -> float:
        """Extract numerical score from OpenAI analysis text."""
        try:
            # Look for score patterns in the text
            import re
            
            # Pattern 1: "score: 75" or "score is 75"
            score_pattern1 = r'score[:\s]+(\d+(?:\.\d+)?)'
            match1 = re.search(score_pattern1, analysis_text.lower())
            if match1:
                return float(match1.group(1))
            
            # Pattern 2: "75/100" or "75 out of 100"
            score_pattern2 = r'(\d+(?:\.\d+)?)\s*/\s*100'
            match2 = re.search(score_pattern2, analysis_text)
            if match2:
                return float(match2.group(1))
            
            # Pattern 3: Look for numbers followed by "score" or "rating"
            score_pattern3 = r'(\d+(?:\.\d+)?)\s*(?:score|rating)'
            match3 = re.search(score_pattern3, analysis_text.lower())
            if match3:
                return float(match3.group(1))
            
            # Default score if no pattern found
            return 50.0
            
        except Exception as e:
            self.logger.error(f"Error extracting score from analysis: {e}")
            return 50.0
    
    def _extract_technical_insights(self, analysis_text: str) -> List[str]:
        """Extract technical insights from analysis text."""
        try:
            insights = []
            
            # Look for technical indicators mentioned
            if 'rsi' in analysis_text.lower():
                insights.append("RSI analysis included")
            if 'macd' in analysis_text.lower():
                insights.append("MACD analysis included")
            if 'moving average' in analysis_text.lower():
                insights.append("Moving average analysis included")
            if 'volume' in analysis_text.lower():
                insights.append("Volume analysis included")
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error extracting technical insights: {e}")
            return []
    
    def _extract_recommendation(self, analysis_text: str) -> str:
        """Extract investment recommendation from analysis text."""
        try:
            analysis_lower = analysis_text.lower()
            
            if 'buy' in analysis_lower and 'sell' not in analysis_lower:
                return "Buy"
            elif 'sell' in analysis_lower:
                return "Sell"
            elif 'hold' in analysis_lower:
                return "Hold"
            else:
                return "Neutral"
                
        except Exception as e:
            self.logger.error(f"Error extracting recommendation: {e}")
            return "Neutral"
        """
        Generate AI-powered stock explanation.
        
        Args:
            symbol: Stock symbol
            scores: Dictionary of scores (technical, fundamental, risk, market, total)
            technical_data: Optional technical indicators data
            market_context: Optional market context data
            
        Returns:
            AI-generated explanation string
        """
        if not self.is_available():
            return self._fallback_explanation(symbol, scores)
        
        try:
            # Prepare context for AI
            context = self._prepare_ai_context(symbol, scores, technical_data, market_context)
            
            # Generate AI explanation
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a professional stock analyst providing concise, 
                        actionable investment advice. Focus on the key factors that drive the 
                        recommendation and provide specific insights about the stock's current 
                        position and potential outlook."""
                    },
                    {
                        "role": "user",
                        "content": f"Analyze this stock: {context}"
                    }
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            explanation = response.choices[0].message.content.strip()
            self.logger.info(f"Generated AI explanation for {symbol}")
            return explanation
            
        except Exception as e:
            self.logger.error(f"Error generating AI explanation for {symbol}: {e}")
            return self._fallback_explanation(symbol, scores)
    
    def _prepare_ai_context(self, symbol: str, scores: Dict[str, float],
                           technical_data: Optional[Dict] = None,
                           market_context: Optional[Dict] = None) -> str:
        """Prepare context for AI analysis."""
        
        # Determine recommendation based on total score
        total_score = scores.get('total', 0)
        if total_score >= 70:
            recommendation = "Strong Buy"
        elif total_score >= 60:
            recommendation = "Buy"
        elif total_score >= 50:
            recommendation = "Hold"
        else:
            recommendation = "Sell"
        
        context = f"""
Stock: {symbol}
Recommendation: {recommendation}
Scores:
- Technical: {scores.get('technical', 0):.1f}/100
- Fundamental: {scores.get('fundamental', 0):.1f}/100  
- Risk: {scores.get('risk', 0):.1f}/100
- Market: {scores.get('market', 0):.1f}/100
- Total: {total_score:.1f}/100

Please provide a concise, professional explanation of this recommendation focusing on the key factors that support this assessment.
"""
        
        if technical_data:
            context += f"\nTechnical Indicators: {technical_data}"
        
        if market_context:
            context += f"\nMarket Context: {market_context}"
        
        return context
    
    def _fallback_explanation(self, symbol: str, scores: Dict[str, float]) -> str:
        """Fallback explanation when AI is not available."""
        total_score = scores.get('total', 0)
        
        if total_score >= 70:
            return f"Strong buy recommendation for {symbol} based on excellent technical and fundamental indicators."
        elif total_score >= 60:
            return f"Buy recommendation for {symbol} with positive momentum and solid fundamentals."
        elif total_score >= 50:
            return f"Hold recommendation for {symbol} with mixed signals and moderate potential."
        else:
            return f"Consider selling {symbol} due to poor technical indicators and elevated risk."
    
    def compare_systems(self, symbol: str, our_scores: Dict[str, float], 
                       market_data: Optional[Dict] = None) -> Dict[str, str]:
        """
        Compare our scoring system with AI analysis.
        
        Args:
            symbol: Stock symbol
            our_scores: Our system's scores
            market_data: Optional market data for context
            
        Returns:
            Dictionary with comparison analysis
        """
        if not self.is_available():
            return {"status": "OpenAI not available", "comparison": "Fallback analysis used"}
        
        try:
            context = f"""
Compare our technical analysis system with AI insights for {symbol}:

Our System Scores:
- Technical: {our_scores.get('technical', 0):.1f}/100
- Fundamental: {our_scores.get('fundamental', 0):.1f}/100
- Risk: {our_scores.get('risk', 0):.1f}/100
- Total: {our_scores.get('total', 0):.1f}/100

Market Context: {market_data if market_data else 'Not available'}

Please provide:
1. Brief comparison of our analysis vs AI insights
2. Key factors that support or challenge our assessment
3. Any additional considerations for this stock
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial analyst comparing different analysis methods."
                    },
                    {
                        "role": "user",
                        "content": context
                    }
                ],
                max_tokens=300,
                temperature=0.5
            )
            
            comparison = response.choices[0].message.content.strip()
            return {
                "status": "AI comparison completed",
                "comparison": comparison,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in system comparison for {symbol}: {e}")
            return {"status": "Comparison failed", "error": str(e)}
    
    def get_market_insights(self, symbols: List[str], market_data: Optional[Dict] = None) -> Dict[str, str]:
        """
        Get AI-powered market insights for multiple symbols.
        
        Args:
            symbols: List of stock symbols
            market_data: Optional market context data
            
        Returns:
            Dictionary with market insights
        """
        if not self.is_available():
            return {"status": "OpenAI not available", "insights": "Market insights unavailable"}
        
        try:
            context = f"""
Provide brief market insights for these stocks: {', '.join(symbols)}

Market Context: {market_data if market_data else 'General market conditions'}

Focus on:
1. Overall market sentiment
2. Key themes affecting these stocks
3. Risk factors to watch
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a market analyst providing concise market insights."
                    },
                    {
                        "role": "user",
                        "content": context
                    }
                ],
                max_tokens=250,
                temperature=0.6
            )
            
            insights = response.choices[0].message.content.strip()
            return {
                "status": "Insights generated",
                "insights": insights,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating market insights: {e}")
            return {"status": "Insights generation failed", "error": str(e)} 