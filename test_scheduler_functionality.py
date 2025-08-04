#!/usr/bin/env python3
"""
Automated test script to verify scheduler functionality.
Tests the data collection scheduler with 1min intervals and verifies updates.
"""

import requests
import time
import json
from datetime import datetime, timedelta
import sys

class SchedulerTest:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def test_api_connection(self):
        """Test if the dashboard is running and accessible."""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                self.log("✅ Dashboard is accessible")
                return True
            else:
                self.log(f"❌ Dashboard returned status {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Cannot connect to dashboard: {e}")
            return False
    
    def get_collections(self):
        """Get list of available collections."""
        try:
            response = self.session.get(f"{self.base_url}/api/data-collection/collections")
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    collections = data.get('collections', [])
                    self.log(f"✅ Found {len(collections)} collections")
                    return collections
                else:
                    self.log(f"❌ API returned error: {data.get('message', 'Unknown error')}")
                    return []
            else:
                self.log(f"❌ Failed to get collections: {response.status_code}")
                return []
        except Exception as e:
            self.log(f"❌ Error getting collections: {e}")
            return []
    
    def start_scheduler(self, collection_id, interval="1min"):
        """Start the scheduler for a collection."""
        try:
            # First, set the interval
            interval_response = self.session.post(
                f"{self.base_url}/api/data-collection/collections/{collection_id}/auto-update",
                json={"interval": interval}
            )
            
            # Then start the scheduler
            response = self.session.post(
                f"{self.base_url}/api/data-collection/collections/{collection_id}/scheduler/start"
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log(f"✅ Started scheduler for {collection_id} with {interval} interval")
                    return data
                else:
                    self.log(f"❌ Failed to start scheduler: {data.get('message', 'Unknown error')}")
                    return None
            else:
                self.log(f"❌ Failed to start scheduler: {response.status_code}")
                return None
        except Exception as e:
            self.log(f"❌ Error starting scheduler: {e}")
            return None
    
    def stop_scheduler(self, collection_id):
        """Stop the scheduler for a collection."""
        try:
            response = self.session.post(
                f"{self.base_url}/api/data-collection/collections/{collection_id}/scheduler/stop"
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log(f"✅ Stopped scheduler for {collection_id}")
                    return True
                else:
                    self.log(f"❌ Failed to stop scheduler: {data.get('message', 'Unknown error')}")
                    return False
            else:
                self.log(f"❌ Failed to stop scheduler: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error stopping scheduler: {e}")
            return False
    
    def get_scheduler_status(self, collection_id):
        """Get the current scheduler status for a collection."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/data-collection/collections/{collection_id}/scheduler/status"
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"🔍 Status response: {json.dumps(data, indent=2)}")
                if data.get('success'):
                    return data
                else:
                    self.log(f"❌ Failed to get status: {data.get('message', 'Unknown error')}")
                    return None
            else:
                self.log(f"❌ Failed to get status: {response.status_code}")
                return None
        except Exception as e:
            self.log(f"❌ Error getting status: {e}")
            return None
    
    def verify_times(self, collection_id, expected_interval_minutes=1):
        """Verify that Last and Next times are correct."""
        status = self.get_scheduler_status(collection_id)
        if not status:
            return False
        
        now = datetime.now()
        
        # Check auto_update is True
        if not status.get('auto_update'):
            self.log("❌ auto_update should be True")
            return False
        
        # Check last_run is recent (within last 2 minutes)
        last_run_str = status.get('last_run')
        if last_run_str:
            try:
                last_run = datetime.fromisoformat(last_run_str.replace('Z', '+00:00'))
                time_diff = abs((now - last_run).total_seconds())
                if time_diff > 120:  # 2 minutes
                    self.log(f"❌ last_run is too old: {last_run_str} (diff: {time_diff:.0f}s)")
                    return False
                else:
                    self.log(f"✅ last_run is recent: {last_run_str}")
            except Exception as e:
                self.log(f"❌ Error parsing last_run: {e}")
                return False
        else:
            self.log("❌ last_run is missing")
            return False
        
        # Check next_run is in the future and approximately correct
        next_run_str = status.get('next_run')
        if next_run_str:
            try:
                next_run = datetime.fromisoformat(next_run_str.replace('Z', '+00:00'))
                time_diff = (next_run - now).total_seconds()
                
                # Special handling for 24h interval (runs at 18:00)
                if expected_interval_minutes == 1440:  # 24h
                    if next_run.hour == 18 and next_run.minute == 0:
                        self.log(f"✅ next_run is correct for 24h: {next_run_str} (set to 18:00)")
                        return True
                    else:
                        self.log(f"❌ next_run is not set to 18:00 for 24h: {next_run_str}")
                        return False
                
                # Should be approximately the interval time (with some tolerance)
                expected_seconds = expected_interval_minutes * 60
                tolerance = 30  # 30 seconds tolerance
                
                if abs(time_diff - expected_seconds) > tolerance:
                    self.log(f"❌ next_run is not approximately {expected_interval_minutes}min in future: {next_run_str} (diff: {time_diff:.0f}s)")
                    return False
                else:
                    self.log(f"✅ next_run is correct: {next_run_str} (diff: {time_diff:.0f}s)")
                    return True
            except Exception as e:
                self.log(f"❌ Error parsing next_run: {e}")
                return False
        else:
            self.log("❌ next_run is missing")
            return False
    
    def wait_for_update(self, collection_id, wait_minutes=2):
        """Wait for an update and verify the times change."""
        self.log(f"⏳ Waiting {wait_minutes} minutes for scheduler update...")
        
        # Get initial status
        initial_status = self.get_scheduler_status(collection_id)
        if not initial_status:
            return False
        
        initial_last_run = initial_status.get('last_run')
        initial_next_run = initial_status.get('next_run')
        
        self.log(f"Initial last_run: {initial_last_run}")
        self.log(f"Initial next_run: {initial_next_run}")
        
        # Wait for the specified time
        wait_seconds = wait_minutes * 60
        for i in range(wait_seconds):
            if i % 30 == 0:  # Log every 30 seconds
                self.log(f"⏳ Still waiting... ({i}/{wait_seconds}s)")
            time.sleep(1)
        
        # Get updated status
        updated_status = self.get_scheduler_status(collection_id)
        if not updated_status:
            return False
        
        updated_last_run = updated_status.get('last_run')
        updated_next_run = updated_status.get('next_run')
        
        self.log(f"Updated last_run: {updated_last_run}")
        self.log(f"Updated next_run: {updated_next_run}")
        
        # Check if times have changed
        if updated_last_run != initial_last_run:
            self.log("✅ last_run has been updated")
        else:
            self.log("❌ last_run has not been updated")
            return False
        
        if updated_next_run != initial_next_run:
            self.log("✅ next_run has been updated")
        else:
            self.log("❌ next_run has not been updated")
            return False
        
        return True
    
    def test_interval(self, collection_id, interval, expected_minutes):
        """Test a specific interval."""
        self.log(f"\n🧪 Testing {interval} interval...")
        
        # Start scheduler
        start_result = self.start_scheduler(collection_id, interval)
        if not start_result:
            return False
        
        # Wait a moment for the system to update
        time.sleep(2)
        
        # Verify times are correct
        if not self.verify_times(collection_id, expected_minutes):
            return False
        
        # Stop scheduler
        if not self.stop_scheduler(collection_id):
            return False
        
        self.log(f"✅ {interval} interval test passed")
        return True
    
    def run_full_test(self):
        """Run the complete test suite."""
        self.log("🚀 Starting Scheduler Functionality Test")
        self.log("=" * 50)
        
        # Test 1: Check if dashboard is accessible
        if not self.test_api_connection():
            self.log("❌ Cannot proceed - dashboard not accessible")
            return False
        
        # Test 2: Get collections
        collections = self.get_collections()
        if not collections:
            self.log("❌ Cannot proceed - no collections available")
            return False
        
        # Use the first collection for testing
        test_collection = collections[0]
        collection_id = test_collection['collection_id']
        self.log(f"📊 Using collection: {collection_id}")
        
        # Test 3: Test 1min interval with background scheduler verification
        self.log(f"\n🧪 Testing 1min interval with background scheduler verification...")
        
        # Start scheduler
        start_result = self.start_scheduler(collection_id, "1min")
        if not start_result:
            self.log("❌ Failed to start scheduler")
            return False
        
        # Wait a moment for the system to update
        time.sleep(2)
        
        # Check what's actually in the database
        self.check_database_contents(collection_id)
        
        # Verify initial times are correct
        if not self.verify_times(collection_id, 1):
            self.log("❌ Initial times verification failed")
            self.stop_scheduler(collection_id)
            return False
        
        # Wait for the background scheduler to actually run (2 minutes)
        self.log("⏳ Waiting for background scheduler to run and update times...")
        if not self.wait_for_update(collection_id, 2):
            self.log("❌ Background scheduler update test failed")
            self.stop_scheduler(collection_id)
            return False
        
        # Stop scheduler
        if not self.stop_scheduler(collection_id):
            self.log("❌ Failed to stop scheduler")
            return False
        
        self.log("✅ 1min interval test with background scheduler passed")
        
        # Test 4: Test other intervals briefly
        intervals_to_test = [
            ("5min", 5),
            ("10min", 10),
            ("30min", 30),
            ("1h", 60),
            ("24h", 1440)
        ]
        
        for interval, expected_minutes in intervals_to_test:
            if not self.test_interval(collection_id, interval, expected_minutes):
                self.log(f"❌ {interval} interval test failed")
                return False
        
        self.log("\n🎉 All tests passed!")
        self.log("✅ Scheduler functionality is working correctly")
        self.log("📝 Note: Background scheduler updates are not yet implemented")
        return True

    def check_database_contents(self, collection_id):
        """Check what's actually stored in the database for a collection."""
        try:
            response = self.session.get(f"{self.base_url}/api/data-collection/collections")
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    collections = data.get('collections', [])
                    for collection in collections:
                        if collection['collection_id'] == collection_id:
                            self.log(f"🔍 Database contents for {collection_id}:")
                            self.log(f"   auto_update: {collection.get('auto_update')}")
                            self.log(f"   update_interval: {collection.get('update_interval')}")
                            self.log(f"   last_run: {collection.get('last_run')}")
                            self.log(f"   next_run: {collection.get('next_run')}")
                            return collection
            return None
        except Exception as e:
            self.log(f"❌ Error checking database contents: {e}")
            return None

def main():
    """Main test runner."""
    test = SchedulerTest()
    
    try:
        success = test.run_full_test()
        if success:
            print("\n🎉 SCHEDULER TEST PASSED")
            sys.exit(0)
        else:
            print("\n❌ SCHEDULER TEST FAILED")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 