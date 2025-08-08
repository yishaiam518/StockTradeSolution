#!/usr/bin/env python3
"""Test script to migrate existing portfolios to include new trading parameters."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.portfolio_management.portfolio_manager import PortfolioManager
from src.data_collection.data_manager import DataCollectionManager as DataManager
from src.ai_ranking.hybrid_ranking_engine import HybridRankingEngine

def main():
    print("Starting portfolio migration...")
    
    # Initialize components
    data_manager = DataManager()
    hybrid_ranking_engine = HybridRankingEngine(data_manager)
    portfolio_manager = PortfolioManager(data_manager, hybrid_ranking_engine)
    
    # Trigger migration
    portfolio_manager._migrate_existing_portfolios()
    
    print("Portfolio migration completed!")
    
    # Check the results
    portfolios = portfolio_manager.db.get_all_portfolios()
    for portfolio in portfolios:
        print(f"\nPortfolio {portfolio.id}: {portfolio.name}")
        print(f"Settings: {portfolio.settings}")

if __name__ == "__main__":
    main() 