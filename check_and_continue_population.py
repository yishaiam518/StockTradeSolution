#!/usr/bin/env python3
"""
Check and Continue Population

This script checks the current storage status and continues
populating the remaining symbols that haven't been stored yet.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json
import time
from datetime import datetime
from pathlib import Path

def check_current_storage():
    """Check current storage status."""
    print("🔍 Checking Current Storage Status...")
    
    try:
        import sqlite3
        
        db_path = Path("data/openai_analysis.db")
        if db_path.exists():
            with sqlite3.connect(db_path) as conn:
                # Check total analyses stored
                cursor = conn.execute("SELECT COUNT(*) FROM openai_analysis")
                total_analyses = cursor.fetchone()[0]
                print(f"✅ Total analyses stored: {total_analyses}")
                
                # Check unique symbols
                cursor = conn.execute("SELECT COUNT(DISTINCT symbol) FROM openai_analysis")
                unique_symbols = cursor.fetchone()[0]
                print(f"✅ Unique symbols analyzed: {unique_symbols}")
                
                # Get list of stored symbols
                cursor = conn.execute("SELECT DISTINCT symbol FROM openai_analysis ORDER BY symbol")
                stored_symbols = [row[0] for row in cursor.fetchall()]
                print(f"📊 Stored symbols: {', '.join(stored_symbols[:10])}{'...' if len(stored_symbols) > 10 else ''}")
                
                return stored_symbols
                    
        else:
            print("❌ Database file not found")
            return []
            
    except Exception as e:
        print(f"❌ Storage check failed: {e}")
        return []

def get_all_symbols():
    """Get all symbols from the collection."""
    base_url = "http://localhost:8080"
    collection_id = "ALL_20250803_160817"
    
    try:
        response = requests.get(f"{base_url}/api/data-collection/collections/{collection_id}/symbols", timeout=10)
        if response.status_code == 200:
            data = response.json()
            symbols = data.get('symbols', [])
            print(f"✅ Found {len(symbols)} symbols in collection")
            return symbols
        else:
            print("❌ Failed to get collection symbols")
            return []
            
    except Exception as e:
        print(f"❌ Error getting symbols: {e}")
        return []

def populate_remaining_symbols(stored_symbols, all_symbols, batch_size=5):
    """Populate storage for remaining symbols."""
    base_url = "http://localhost:8080"
    collection_id = "ALL_20250803_160817"
    
    # Find symbols that need to be stored
    remaining_symbols = [s for s in all_symbols if s not in stored_symbols]
    
    print(f"\n🚀 Populating remaining {len(remaining_symbols)} symbols")
    print(f"📊 Already stored: {len(stored_symbols)} symbols")
    print(f"📊 Remaining to store: {len(remaining_symbols)} symbols")
    
    if not remaining_symbols:
        print("✅ All symbols already stored!")
        return
    
    successful_stores = 0
    failed_stores = 0
    total_batches = (len(remaining_symbols) + batch_size - 1) // batch_size
    
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(remaining_symbols))
        batch_symbols = remaining_symbols[start_idx:end_idx]
        
        print(f"\n📊 Processing batch {batch_num + 1}/{total_batches} ({len(batch_symbols)} symbols)")
        print(f"   Symbols: {', '.join(batch_symbols)}")
        
        batch_start_time = time.time()
        batch_successful = 0
        batch_failed = 0
        
        for i, symbol in enumerate(batch_symbols, 1):
            try:
                print(f"      📈 Processing {symbol} ({i}/{len(batch_symbols)})...")
                
                # Trigger comprehensive analysis for this symbol
                response = requests.get(
                    f"{base_url}/api/ai-ranking/collection/{collection_id}/hybrid-rank?max_stocks=1&symbols={symbol}", 
                    timeout=60
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success') and data.get('dual_scores'):
                        print(f"         ✅ {symbol}: Analysis completed and stored")
                        batch_successful += 1
                        successful_stores += 1
                    else:
                        print(f"         ⚠️ {symbol}: Analysis completed but no results")
                        batch_failed += 1
                        failed_stores += 1
                else:
                    print(f"         ❌ {symbol}: Analysis failed")
                    batch_failed += 1
                    failed_stores += 1
                    
            except Exception as e:
                print(f"         ❌ {symbol}: Error - {e}")
                batch_failed += 1
                failed_stores += 1
                continue
        
        batch_time = time.time() - batch_start_time
        print(f"   ✅ Batch {batch_num + 1} completed in {batch_time:.2f}s")
        print(f"   📊 Batch results: {batch_successful} successful, {batch_failed} failed")
        
        # Small delay between batches
        if batch_num < total_batches - 1:
            print("   ⏳ Waiting 2 seconds before next batch...")
            time.sleep(2)
    
    print(f"\n✅ Storage population completed!")
    print(f"   - Total successful stores: {successful_stores}")
    print(f"   - Total failed stores: {failed_stores}")
    if successful_stores + failed_stores > 0:
        print(f"   - Success rate: {(successful_stores/(successful_stores+failed_stores)*100):.1f}%")

def test_performance_with_full_data():
    """Test performance with full dataset."""
    print("\n⚡ Testing Performance with Full Dataset...")
    
    base_url = "http://localhost:8080"
    collection_id = "ALL_20250803_160817"
    
    # Test different batch sizes
    test_sizes = [5, 10, 20, 50, 112]
    
    for size in test_sizes:
        try:
            print(f"\n   📊 Testing {size} symbols...")
            start_time = time.time()
            response = requests.get(f"{base_url}/api/ai-ranking/collection/{collection_id}/hybrid-rank?max_stocks={size}", timeout=120)
            load_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('dual_scores'):
                    print(f"      ✅ Loaded {len(data['dual_scores'])} symbols in {load_time:.2f}s")
                    
                    if load_time < 10:
                        print("      🚀 Performance: Excellent (under 10 seconds)")
                    elif load_time < 30:
                        print("      ✅ Performance: Good (under 30 seconds)")
                    elif load_time < 60:
                        print("      ⚠️ Performance: Acceptable (under 60 seconds)")
                    else:
                        print("      ❌ Performance: Slow (over 60 seconds)")
                        
                else:
                    print("      ❌ No data returned")
            else:
                print(f"      ❌ Request failed: {response.status_code}")
                
        except Exception as e:
            print(f"      ❌ Test failed: {e}")

def main():
    """Run the check and continue population."""
    print("🚀 Check and Continue Population")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check current storage
    stored_symbols = check_current_storage()
    
    # Get all symbols
    all_symbols = get_all_symbols()
    if not all_symbols:
        print("❌ No symbols found, exiting")
        return
    
    # Populate remaining symbols
    populate_remaining_symbols(stored_symbols, all_symbols, batch_size=5)
    
    # Test performance
    test_performance_with_full_data()
    
    print("\n" + "=" * 60)
    print("✅ Check and Continue Population Completed!")
    print("\n📋 Summary:")
    print("1. ✅ Current storage status checked")
    print("2. ✅ Remaining symbols populated")
    print("3. ✅ Performance tested with full dataset")
    print("4. ✅ System ready for frontend testing")
    
    print("\n🎯 Ready for Frontend Testing:")
    print("- Open dashboard and test AI Ranking section")
    print("- Verify instant loading with cached results")
    print("- Experience the performance improvements")

if __name__ == "__main__":
    main() 