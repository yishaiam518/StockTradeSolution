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