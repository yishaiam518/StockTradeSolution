#!/usr/bin/env python3
"""
Test script to check scheduler persistence
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data_collection.scheduler import DataCollectionScheduler
from src.data_collection.data_manager import DataCollectionManager

def test_scheduler_persistence():
    """Test scheduler persistence."""
    print("🔍 Testing Scheduler Persistence")
    print("=" * 50)
    
    # Initialize data manager
    data_manager = DataCollectionManager()
    
    # Initialize scheduler
    scheduler = DataCollectionScheduler(data_manager)
    
    # Get the collection scheduler
    collection_id = "ALL_20250803_160817"
    collection_scheduler = scheduler.get_or_create_scheduler(collection_id)
    
    print(f"📊 Collection: {collection_id}")
    print(f"🔄 Scheduler instance ID: {id(collection_scheduler)}")
    
    # Check initial status
    initial_status = collection_scheduler.get_status()
    print(f"📈 Initial AI ranking last update: {initial_status.get('ai_ranking_last_update', 'Never')}")
    
    # Trigger AI ranking
    print("\n🚀 Triggering AI ranking...")
    collection_scheduler._trigger_ai_ranking_recalculation()
    
    # Check updated status
    updated_status = collection_scheduler.get_status()
    print(f"📈 Updated AI ranking last update: {updated_status.get('ai_ranking_last_update', 'Never')}")
    
    # Get the same scheduler instance again
    same_scheduler = scheduler.get_or_create_scheduler(collection_id)
    print(f"🔄 Same scheduler instance ID: {id(same_scheduler)}")
    
    # Check if the AI ranking information persists
    persisted_status = same_scheduler.get_status()
    print(f"📈 Persisted AI ranking last update: {persisted_status.get('ai_ranking_last_update', 'Never')}")
    
    # Check if the scheduler is in the collection_schedulers dict
    print(f"📊 Scheduler in collection_schedulers: {collection_id in scheduler.collection_schedulers}")
    print(f"📊 Collection schedulers keys: {list(scheduler.collection_schedulers.keys())}")

if __name__ == "__main__":
    test_scheduler_persistence() 