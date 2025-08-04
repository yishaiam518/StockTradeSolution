#!/usr/bin/env python3
"""
Test to directly call enable_auto_update and see if it works.
"""

import sys
import os
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data_collection.data_manager import DataCollectionManager

def test_enable_auto_update():
    """Test enable_auto_update directly."""
    data_manager = DataCollectionManager()
    
    # Get all collections
    collections = data_manager.list_collections()
    print(f"Found {len(collections)} collections")
    
    if collections:
        collection_id = collections[0]['collection_id']
        print(f"Testing collection: {collection_id}")
        
        # Check current state
        details_before = data_manager.get_collection_details(collection_id)
        print(f"Before - auto_update: {details_before.get('auto_update')}")
        print(f"Before - last_run: {details_before.get('last_run')}")
        print(f"Before - next_run: {details_before.get('next_run')}")
        
        # Call enable_auto_update
        now = datetime.now()
        next_run = now + timedelta(minutes=1)
        
        print(f"Calling enable_auto_update with:")
        print(f"  collection_id: {collection_id}")
        print(f"  enable: True")
        print(f"  interval: 1min")
        print(f"  last_run: {now.isoformat()}")
        print(f"  next_run: {next_run.isoformat()}")
        
        success = data_manager.enable_auto_update(
            collection_id,
            True,
            "1min",
            now.isoformat(),
            next_run.isoformat()
        )
        
        print(f"enable_auto_update returned: {success}")
        
        # Check state after
        details_after = data_manager.get_collection_details(collection_id)
        print(f"After - auto_update: {details_after.get('auto_update')}")
        print(f"After - last_run: {details_after.get('last_run')}")
        print(f"After - next_run: {details_after.get('next_run')}")

if __name__ == "__main__":
    test_enable_auto_update() 