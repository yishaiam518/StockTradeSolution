#!/usr/bin/env python3
"""
Test script to manually trigger AI ranking recalculation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data_collection.scheduler import DataCollectionScheduler
from src.data_collection.data_manager import DataCollectionManager

def test_ai_ranking_trigger():
    """Test manual AI ranking trigger."""
    print("🤖 Testing AI Ranking Trigger")
    print("=" * 50)
    
    # Initialize data manager
    data_manager = DataCollectionManager()
    
    # Initialize scheduler
    scheduler = DataCollectionScheduler(data_manager)
    
    # Get the collection scheduler
    collection_id = "ALL_20250803_160817"
    collection_scheduler = scheduler.get_or_create_scheduler(collection_id)
    
    print(f"📊 Collection: {collection_id}")
    print(f"🔄 Scheduler running: {collection_scheduler.is_running}")
    
    # Check current status
    current_status = collection_scheduler.get_status()
    print(f"📈 Current AI ranking last update: {current_status.get('ai_ranking_last_update', 'Never')}")
    
    # Manually trigger AI ranking recalculation
    print("\n🚀 Manually triggering AI ranking recalculation...")
    try:
        collection_scheduler._trigger_ai_ranking_recalculation()
        print("✅ AI ranking recalculation triggered successfully!")
        
        # Check updated status
        updated_status = collection_scheduler.get_status()
        print(f"📈 Updated AI ranking last update: {updated_status.get('ai_ranking_last_update', 'Never')}")
        
        if updated_status.get('ai_ranking_metadata'):
            print("📊 AI Ranking Metadata:")
            metadata = updated_status['ai_ranking_metadata']
            print(f"   - Total stocks ranked: {metadata.get('total_stocks', 'Unknown')}")
            print(f"   - Top stocks: {metadata.get('top_stocks', [])}")
        
    except Exception as e:
        print(f"❌ Error triggering AI ranking: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ai_ranking_trigger() 