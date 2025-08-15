#!/usr/bin/env python3
"""
Launcher script for Trading Monitor Agent

This script starts the intelligent monitoring system that:
- Monitors logs in real-time
- Detects and auto-fixes common issues
- Provides system health status
- Generates end-of-day reports
"""

import sys
import os
import signal
import time

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
    if 'monitor' in globals():
        monitor.stop_monitoring()
    sys.exit(0)

def main():
    """Launch the trading monitor agent."""
    print("🚀 Launching Trading Monitor Agent...")
    print("=" * 50)
    print("📊 Intelligent monitoring system for StockTradeSolution")
    print("🔧 Auto-fix enabled for known issues")
    print("📝 Real-time monitoring + End-of-day reporting")
    print("⏹️  Press Ctrl+C to stop")
    print("=" * 50)
    
    try:
        # Import and start the monitor
        from trading_monitor_agent import TradingMonitorAgent
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start the monitor
        global monitor
        monitor = TradingMonitorAgent()
        
        print("✅ Trading Monitor Agent is now running!")
        print("📊 Monitoring: Portfolio, Transactions, Scheduler, AI Ranking")
        print("🔧 Auto-fix: Active for known issues")
        print("📝 Logging: All issues tracked in database")
        print("=" * 50)
        
        # Keep the main thread alive
        while True:
            time.sleep(60)
            
            # Print status every minute
            status = monitor.get_system_status()
            print(f"📊 Status: {status['issues_detected']} issues, {status['auto_fixes_applied']} auto-fixes")
            
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Trading Monitor Agent...")
        if 'monitor' in globals():
            monitor.stop_monitoring()
            
            # Generate final report
            print("📋 Generating final report...")
            report = monitor.generate_end_of_day_report()
            
            print("\n📊 Final Status Report:")
            print(f"   Date: {report['date']}")
            print(f"   Overall Health: {report['summary']['overall_health']}")
            print(f"   Total Issues: {report['summary']['total_issues']}")
            print(f"   Auto-fixes Applied: {report['summary']['auto_fixes_applied']}")
            print(f"   Manual Reviews Required: {report['summary']['manual_reviews_required']}")
            
            # Export issues
            filename = monitor.export_issues_to_file()
            if filename:
                print(f"📄 Issues exported to: {filename}")
            
            print("✅ Trading Monitor Agent shutdown complete")
            
    except Exception as e:
        print(f"❌ Error in Trading Monitor Agent: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
