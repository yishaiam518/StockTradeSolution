#!/usr/bin/env python3
"""
Test script to check scheduler status
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data_collection.scheduler import DataCollectionScheduler
from src.data_collection.data_manager import DataCollectionManager

def test_scheduler_status():
    """Test scheduler status."""
    print("🔍 Testing Scheduler Status")
    print("=" * 50)
    
    # Initialize data manager
    data_manager = DataCollectionManager()
    
    # Initialize scheduler
    scheduler = DataCollectionScheduler(data_manager)
    
    # Get the collection scheduler
    collection_id = "ALL_20250803_160817"
    collection_scheduler = scheduler.get_or_create_scheduler(collection_id)
    
    print(f"📊 Collection: {collection_id}")
    
    # Check current status
    current_status = collection_scheduler.get_status()
    print(f"📈 Current status keys: {list(current_status.keys())}")
    print(f"📈 AI ranking last update: {current_status.get('ai_ranking_last_update', 'Never')}")
    print(f"📈 AI ranking integrated: {current_status.get('ai_ranking_integrated', 'Not set')}")
    
    # Check the DataCollectionScheduler get_collection_status method
    scheduler_status = scheduler.get_collection_status(collection_id)
    print(f"📈 Scheduler status keys: {list(scheduler_status.keys()) if scheduler_status else 'None'}")
    print(f"📈 Scheduler AI ranking last update: {scheduler_status.get('ai_ranking_last_update', 'Never') if scheduler_status else 'None'}")

if __name__ == "__main__":
    test_scheduler_status() 