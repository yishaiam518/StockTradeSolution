#!/usr/bin/env python3
"""
Debug script to test AI ranking imports
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all AI ranking imports"""
    try:
        print("Testing imports...")
        
        # Test basic imports
        from src.ai_ranking.ranking_engine import StockRankingEngine
        print("✓ StockRankingEngine imported successfully")
        
        from src.ai_ranking.scoring_models import MultiFactorScorer
        print("✓ MultiFactorScorer imported successfully")
        
        from src.ai_ranking.strategy_analyzer import StrategyAnalyzer
        print("✓ StrategyAnalyzer imported successfully")
        
        from src.ai_ranking.educational_ai import EducationalAI
        print("✓ EducationalAI imported successfully")
        
        from src.ai_ranking.openai_integration import OpenAIStockAnalyzer
        print("✓ OpenAIStockAnalyzer imported successfully")
        
        # Test integration
        from src.data_collection.integration import DataCollectionAIIntegration
        print("✓ DataCollectionAIIntegration imported successfully")
        
        print("\nAll imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ranking_engine():
    """Test ranking engine initialization"""
    try:
        print("\nTesting ranking engine initialization...")
        
        from src.ai_ranking.ranking_engine import StockRankingEngine
        from src.data_collection.data_manager import DataCollectionManager
        
        # Initialize components
        data_manager = DataCollectionManager()
        ranking_engine = StockRankingEngine(data_manager)
        
        print("✓ Ranking engine initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Ranking engine error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration():
    """Test integration layer"""
    try:
        print("\nTesting integration layer...")
        
        from src.data_collection.integration import DataCollectionAIIntegration
        from src.data_collection.data_manager import DataCollectionManager
        
        # Initialize components
        data_manager = DataCollectionManager()
        integration = DataCollectionAIIntegration(data_manager)
        
        print("✓ Integration layer initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Integration error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== AI Ranking Debug Test ===\n")
    
    # Test imports
    imports_ok = test_imports()
    
    if imports_ok:
        # Test ranking engine
        ranking_ok = test_ranking_engine()
        
        if ranking_ok:
            # Test integration
            integration_ok = test_integration()
            
            if integration_ok:
                print("\n🎉 All tests passed! AI ranking system is working correctly.")
            else:
                print("\n❌ Integration test failed.")
        else:
            print("\n❌ Ranking engine test failed.")
    else:
        print("\n❌ Import test failed.") 