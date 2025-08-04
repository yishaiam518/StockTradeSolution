#!/usr/bin/env python3
"""
Simple test to check what get_collection_details returns.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data_collection.data_manager import DataCollectionManager

def test_get_collection_details():
    """Test what get_collection_details returns."""
    data_manager = DataCollectionManager()
    
    # Get all collections
    collections = data_manager.list_collections()
    print(f"Found {len(collections)} collections")
    
    if collections:
        collection_id = collections[0]['collection_id']
        print(f"Testing collection: {collection_id}")
        
        # Get collection details
        details = data_manager.get_collection_details(collection_id)
        print(f"Collection details: {details}")
        
        if details:
            print(f"last_run: {details.get('last_run')}")
            print(f"next_run: {details.get('next_run')}")
            print(f"auto_update: {details.get('auto_update')}")
            print(f"update_interval: {details.get('update_interval')}")
        else:
            print("No details found")

if __name__ == "__main__":
    test_get_collection_details() 