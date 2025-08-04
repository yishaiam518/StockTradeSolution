#!/usr/bin/env python3
"""
Start the StockTradeSolution Web Dashboard
"""

import sys
import os
# import webbrowser
# import time
# from threading import Timer

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# def open_browser():
#     """Open the dashboard in the browser"""
#     webbrowser.open('http://localhost:8080')

def main():
    """Start the dashboard"""
    try:
        from src.web_dashboard.dashboard_app import DashboardApp
        
        print("🚀 Starting StockTradeSolution Dashboard...")
        print("=" * 50)
        print("📊 Dashboard Features:")
        print("   - Strategy + Profile Selection")
        print("   - Backtesting with Multiple Strategies")
        print("   - Historic Backtesting")
        print("   - Real-time Trading Signals")
        print("   - Performance Analytics")
        print("   - Portfolio Management")
        print("=" * 50)
        
        # Open browser after 2 seconds
        # Timer(2.0, open_browser).start()
        
        # print("🌐 Opening dashboard in browser...")
        print("🔗 URL: http://localhost:8080")
        print("⏹️  Press Ctrl+C to stop the dashboard")
        print("=" * 50)
        
        # Create and start the dashboard app
        dashboard_app = DashboardApp()
        dashboard_app.start()
        
    except ImportError as e:
        print(f"❌ Error importing dashboard: {e}")
        print("💡 Make sure all dependencies are installed:")
        print("   pip install flask pandas numpy plotly")
        return 1
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 