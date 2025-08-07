#!/usr/bin/env python3
"""
Test Hybrid Data Retrieval

This script tests what data the hybrid ranking engine
is actually retrieving for scoring.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data_collection.data_manager import DataCollectionManager
from src.ai_ranking.hybrid_ranking_engine import HybridRankingEngine
import pandas as pd

def test_data_retrieval():
    """Test what data the hybrid ranking engine retrieves."""
    print("🔍 Testing Hybrid Data Retrieval...")
    
    # Initialize data manager
    data_manager = DataCollectionManager()
    collection_id = "ALL_20250803_160817"
    symbol = "AAPL"
    
    print(f"Testing data retrieval for {symbol} in collection {collection_id}")
    
    # Test get_symbol_indicators
    print("\n1. Testing get_symbol_indicators...")
    indicators_data = data_manager.get_symbol_indicators(collection_id, symbol)
    
    if indicators_data is not None and not indicators_data.empty:
        print(f"   ✅ Got indicators data: {len(indicators_data)} rows")
        print(f"   Columns: {list(indicators_data.columns)}")
        
        # Show latest data
        latest = indicators_data.iloc[-1]
        print(f"   Latest data:")
        print(f"     Close: {latest.get('Close', 'N/A')}")
        print(f"     RSI: {latest.get('rsi', 'N/A')}")
        print(f"     MACD: {latest.get('macd', 'N/A')}")
        print(f"     MACD Signal: {latest.get('macd_signal', 'N/A')}")
        print(f"     SMA 20: {latest.get('sma_20', 'N/A')}")
        print(f"     SMA 50: {latest.get('sma_50', 'N/A')}")
        
        # Test the scoring algorithm
        print("\n2. Testing scoring algorithm...")
        try:
            # Create a simple hybrid engine for testing
            class SimpleHybridEngine:
                def __init__(self, data_manager):
                    self.data_manager = data_manager
                    self.logger = None
                
                def _calculate_local_score(self, stock_data) -> float:
                    """Calculate score using local algorithms."""
                    try:
                        if stock_data.empty:
                            return 50.0
                        
                        latest = stock_data.iloc[-1]
                        
                        # More sophisticated technical indicators analysis
                        rsi = latest.get('rsi', 50)
                        # RSI scoring: 100 for optimal (40-60), 80 for good (30-70), 60 for neutral, 40 for poor
                        if 40 <= rsi <= 60:
                            rsi_score = 100
                        elif 30 <= rsi <= 70:
                            rsi_score = 80
                        elif 20 <= rsi <= 80:
                            rsi_score = 60
                        else:
                            rsi_score = 40
                        
                        # MACD analysis with more granular scoring
                        macd = latest.get('macd', 0)
                        macd_signal = latest.get('macd_signal', 0)
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
                        
                        # Moving average analysis with more granular scoring
                        close = latest.get('Close', 0)
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
                        
                        # Enhanced volatility calculation
                        try:
                            if 'Close' in stock_data.columns and len(stock_data) > 1:
                                returns = stock_data['Close'].pct_change().dropna()
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
                            print(f"   Warning: Error calculating volatility: {vol_error}")
                            risk_score = 60.0
                        
                        # Enhanced weighted average with more weight on technical indicators
                        technical_score = (rsi_score * 0.4 + macd_score * 0.4 + ma_score * 0.2)
                        local_score = (technical_score * 0.7 + risk_score * 0.3)
                        
                        print(f"   Scoring breakdown:")
                        print(f"     RSI: {rsi} -> {rsi_score}")
                        print(f"     MACD: {macd} vs {macd_signal} (histogram: {macd_histogram}) -> {macd_score}")
                        print(f"     MA: Close {close} vs SMA20 {sma_20} vs SMA50 {sma_50} -> {ma_score}")
                        print(f"     Risk: {risk_score}")
                        print(f"     Technical score: {technical_score}")
                        print(f"     Final local score: {local_score}")
                        
                        return min(max(local_score, 0), 100)
                        
                    except Exception as e:
                        print(f"   Error calculating local score: {e}")
                        return 50.0
            
            # Test the scoring
            engine = SimpleHybridEngine(data_manager)
            score = engine._calculate_local_score(indicators_data)
            print(f"   Final score: {score}")
            
        except Exception as e:
            print(f"   Error testing scoring: {e}")
            
    else:
        print("   ❌ No indicators data retrieved")

def main():
    """Run the hybrid data retrieval test."""
    print("🚀 Hybrid Data Retrieval Test")
    print("=" * 60)
    
    test_data_retrieval()
    
    print("\n" + "=" * 60)
    print("✅ Hybrid Data Retrieval Test Completed!")

if __name__ == "__main__":
    main() 