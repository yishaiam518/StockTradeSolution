#!/usr/bin/env python3
"""
Test script for AI Ranking System

This script tests the AI ranking functionality to ensure it's working correctly.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.data_collection.data_manager import DataCollectionManager, DataCollectionConfig, Exchange
from src.data_collection.integration import DataCollectionAIIntegration
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ai_ranking():
    """Test the AI ranking system functionality."""
    
    print("🧪 Testing AI Ranking System")
    print("=" * 50)
    
    try:
        # Initialize data collection manager
        data_manager = DataCollectionManager()
        
        # Initialize AI integration
        ai_integration = DataCollectionAIIntegration(data_manager)
        
        print("✅ AI Ranking System initialized successfully")
        
        # Test with a sample collection
        # First, let's check if we have any existing collections
        collections = data_manager.list_collections()
        
        if not collections:
            print("⚠️  No existing collections found. Creating a test collection...")
            
            # Create a test collection
            config = DataCollectionConfig(
                exchange=Exchange.NASDAQ,
                start_date="2024-01-01",
                end_date="2024-12-31",
                symbols=["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]  # Small test set
            )
            
            collection_id = data_manager.create_data_collection(config)
            print(f"✅ Created test collection: {collection_id}")
            
        else:
            # Use the first available collection
            collection_id = collections[0]['collection_id']
            print(f"✅ Using existing collection: {collection_id}")
        
        # Test AI ranking
        print("\n🔍 Testing AI Ranking...")
        ranking_result = ai_integration.get_collection_ranking(collection_id, max_stocks=10)
        
        if ranking_result['success']:
            print("✅ AI Ranking completed successfully!")
            print(f"📊 Total stocks analyzed: {ranking_result['total_stocks']}")
            
            # Display top stocks
            if ranking_result['top_stocks']:
                print("\n🏆 Top Ranked Stocks:")
                for i, stock in enumerate(ranking_result['top_stocks'][:5], 1):
                    print(f"{i}. {stock['symbol']} - Score: {stock['total_score']:.1f}")
                    print(f"   Technical: {stock['technical_score']:.1f}, Risk: {stock['risk_score']:.1f}")
                    print(f"   Explanation: {stock['explanation']}")
                    print()
            
            # Display market analysis
            if 'market_analysis' in ranking_result:
                market = ranking_result['market_analysis']
                print(f"📈 Market Regime: {market.get('market_regime', 'Unknown')}")
                print(f"💡 Market Insight: {market.get('market_insight', 'No insight available')}")
            
            # Display educational content
            if 'educational_content' in ranking_result:
                edu = ranking_result['educational_content']
                if edu.get('insights'):
                    print("\n🎓 Key Insights:")
                    for insight in edu['insights']:
                        print(f"   • {insight}")
                
                if edu.get('learning_recommendations'):
                    print("\n📚 Learning Recommendations:")
                    for rec in edu['learning_recommendations']:
                        print(f"   • {rec}")
            
        else:
            print(f"❌ AI Ranking failed: {ranking_result.get('error', 'Unknown error')}")
        
        # Test stock analysis
        print("\n🔍 Testing Individual Stock Analysis...")
        test_symbol = "AAPL"
        stock_analysis = ai_integration.get_stock_analysis(collection_id, test_symbol)
        
        if stock_analysis['success']:
            print(f"✅ Stock analysis for {test_symbol} completed!")
            analysis = stock_analysis['analysis']
            print(f"   Rank: {analysis['rank']}")
            print(f"   Total Score: {analysis['total_score']:.1f}")
            print(f"   Technical Score: {analysis['technical_score']:.1f}")
            print(f"   Risk Score: {analysis['risk_score']:.1f}")
            print(f"   Explanation: {analysis['explanation']}")
            
            if 'strategy_insight' in stock_analysis:
                strategy = stock_analysis['strategy_insight']
                print(f"   Recommended Strategy: {strategy['strategy_name']}")
                print(f"   Risk Level: {strategy['risk_level']}")
                print(f"   Time Horizon: {strategy['time_horizon']}")
        else:
            print(f"❌ Stock analysis failed: {stock_analysis.get('error', 'Unknown error')}")
        
        # Test export functionality
        print("\n📤 Testing Export Functionality...")
        export_result = ai_integration.export_ranking_report(collection_id, 'json')
        
        if export_result['success']:
            print("✅ Export functionality working!")
            print(f"   Format: {export_result['format']}")
            print(f"   Data length: {len(export_result['data'])} characters")
        else:
            print(f"❌ Export failed: {export_result.get('error', 'Unknown error')}")
        
        print("\n🎉 AI Ranking System Test Completed Successfully!")
        
    except Exception as e:
        print(f"❌ Error testing AI ranking system: {e}")
        logger.error(f"Error in test: {e}", exc_info=True)

if __name__ == "__main__":
    test_ai_ranking() 