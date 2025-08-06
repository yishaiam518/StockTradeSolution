#!/usr/bin/env python3
"""
Test script to check dashboard scheduler instance
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.web_dashboard.dashboard_app import DashboardApp

def test_dashboard_scheduler():
    """Test dashboard scheduler instance."""
    print("🔍 Testing Dashboard Scheduler")
    print("=" * 50)
    
    # Initialize dashboard
    dashboard = DashboardApp()
    
    # Check if dashboard has data_scheduler
    print(f"📊 Dashboard has data_scheduler: {hasattr(dashboard, 'data_scheduler')}")
    
    if hasattr(dashboard, 'data_scheduler'):
        print(f"📊 Data scheduler type: {type(dashboard.data_scheduler)}")
        
        # Get collection status
        collection_id = "ALL_20250803_160817"
        status = dashboard.data_scheduler.get_collection_status(collection_id)
        
        print(f"📈 Status keys: {list(status.keys()) if status else 'None'}")
        print(f"📈 AI ranking last update: {status.get('ai_ranking_last_update', 'Never') if status else 'None'}")
        print(f"📈 AI ranking integrated: {status.get('ai_ranking_integrated', 'Not set') if status else 'None'}")
    else:
        print("❌ Dashboard does not have data_scheduler")

if __name__ == "__main__":
    test_dashboard_scheduler() 