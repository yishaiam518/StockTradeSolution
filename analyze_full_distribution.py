#!/usr/bin/env python3
"""
Analyze Full Distribution

This script analyzes the scoring distribution across all 112 symbols
to understand the local algorithm performance and OpenAI issues.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json
import pandas as pd
from datetime import datetime
import numpy as np

def analyze_full_distribution():
    """Analyze the full distribution of all 112 symbols."""
    base_url = "http://localhost:8080"
    collection_id = "ALL_20250803_160817"
    
    print("🔍 Analyzing Full Distribution (112 symbols)...")
    
    try:
        # Get all 112 symbols
        response = requests.get(f"{base_url}/api/ai-ranking/collection/{collection_id}/hybrid-rank?max_stocks=112", timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('dual_scores'):
                dual_scores = data['dual_scores']
                
                print(f"✅ Retrieved {len(dual_scores)} symbols")
                
                # Convert to DataFrame for analysis
                df = pd.DataFrame(dual_scores)
                
                # Basic statistics
                print(f"\n📊 Basic Statistics:")
                print(f"   Total symbols: {len(df)}")
                print(f"   Local scores - Mean: {df['local_score'].mean():.1f}, Std: {df['local_score'].std():.1f}")
                print(f"   OpenAI scores - Mean: {df['openai_score'].mean():.1f}, Std: {df['openai_score'].std():.1f}")
                print(f"   Combined scores - Mean: {df['combined_score'].mean():.1f}, Std: {df['combined_score'].std():.1f}")
                
                # Score ranges
                print(f"\n📊 Score Ranges:")
                print(f"   Local scores: {df['local_score'].min():.1f} - {df['local_score'].max():.1f}")
                print(f"   OpenAI scores: {df['openai_score'].min():.1f} - {df['openai_score'].max():.1f}")
                print(f"   Combined scores: {df['combined_score'].min():.1f} - {df['combined_score'].max():.1f}")
                
                # Recommendation distribution
                print(f"\n📊 Recommendation Distribution:")
                
                # Current thresholds
                strong_buy_count = len(df[df['combined_score'] >= 75])
                buy_count = len(df[(df['combined_score'] >= 65) & (df['combined_score'] < 75)])
                hold_count = len(df[(df['combined_score'] >= 55) & (df['combined_score'] < 65)])
                sell_count = len(df[(df['combined_score'] >= 45) & (df['combined_score'] < 55)])
                strong_sell_count = len(df[df['combined_score'] < 45])
                
                print(f"   Strong Buy (≥75): {strong_buy_count} ({strong_buy_count/len(df)*100:.1f}%)")
                print(f"   Buy (65-74): {buy_count} ({buy_count/len(df)*100:.1f}%)")
                print(f"   Hold (55-64): {hold_count} ({hold_count/len(df)*100:.1f}%)")
                print(f"   Sell (45-54): {sell_count} ({sell_count/len(df)*100:.1f}%)")
                print(f"   Strong Sell (<45): {strong_sell_count} ({strong_sell_count/len(df)*100:.1f}%)")
                
                # Alternative thresholds for comparison
                print(f"\n📊 Alternative Threshold Analysis:")
                
                # Lower thresholds
                buy_count_60 = len(df[df['combined_score'] >= 60])
                buy_count_55 = len(df[df['combined_score'] >= 55])
                buy_count_50 = len(df[df['combined_score'] >= 50])
                
                print(f"   BUY recommendations with threshold 60: {buy_count_60} ({buy_count_60/len(df)*100:.1f}%)")
                print(f"   BUY recommendations with threshold 55: {buy_count_55} ({buy_count_55/len(df)*100:.1f}%)")
                print(f"   BUY recommendations with threshold 50: {buy_count_50} ({buy_count_50/len(df)*100:.1f}%)")
                
                # Top performers
                print(f"\n🏆 Top 10 Local Scores:")
                top_local = df.nlargest(10, 'local_score')[['symbol', 'local_score', 'openai_score', 'combined_score']]
                for _, row in top_local.iterrows():
                    print(f"   {row['symbol']}: Local={row['local_score']:.1f}, OpenAI={row['openai_score']:.1f}, Combined={row['combined_score']:.1f}")
                
                print(f"\n🏆 Top 10 Combined Scores:")
                top_combined = df.nlargest(10, 'combined_score')[['symbol', 'local_score', 'openai_score', 'combined_score']]
                for _, row in top_combined.iterrows():
                    print(f"   {row['symbol']}: Local={row['local_score']:.1f}, OpenAI={row['openai_score']:.1f}, Combined={row['combined_score']:.1f}")
                
                # Bottom performers
                print(f"\n📉 Bottom 10 Combined Scores:")
                bottom_combined = df.nsmallest(10, 'combined_score')[['symbol', 'local_score', 'openai_score', 'combined_score']]
                for _, row in bottom_combined.iterrows():
                    print(f"   {row['symbol']}: Local={row['local_score']:.1f}, OpenAI={row['openai_score']:.1f}, Combined={row['combined_score']:.1f}")
                
                # OpenAI analysis
                print(f"\n🤖 OpenAI Analysis:")
                unique_openai = df['openai_score'].unique()
                print(f"   Unique OpenAI scores: {sorted(unique_openai)}")
                print(f"   OpenAI score distribution:")
                for score in sorted(unique_openai):
                    count = len(df[df['openai_score'] == score])
                    print(f"     {score}: {count} symbols ({count/len(df)*100:.1f}%)")
                
                # Correlation analysis
                correlation = df['local_score'].corr(df['openai_score'])
                print(f"\n📈 Correlation Analysis:")
                print(f"   Local vs OpenAI correlation: {correlation:.3f}")
                
                # Divergent cases (for algorithm improvement)
                print(f"\n🔍 Divergent Cases (for algorithm improvement):")
                # High local, low OpenAI
                high_local_low_openai = df[(df['local_score'] >= 70) & (df['openai_score'] <= 30)]
                print(f"   High Local (≥70) + Low OpenAI (≤30): {len(high_local_low_openai)} symbols")
                if len(high_local_low_openai) > 0:
                    for _, row in high_local_low_openai.head(5).iterrows():
                        print(f"     {row['symbol']}: Local={row['local_score']:.1f}, OpenAI={row['openai_score']:.1f}")
                
                # Low local, high OpenAI
                low_local_high_openai = df[(df['local_score'] <= 40) & (df['openai_score'] >= 40)]
                print(f"   Low Local (≤40) + High OpenAI (≥40): {len(low_local_high_openai)} symbols")
                if len(low_local_high_openai) > 0:
                    for _, row in low_local_high_openai.head(5).iterrows():
                        print(f"     {row['symbol']}: Local={row['local_score']:.1f}, OpenAI={row['openai_score']:.1f}")
                
                return df
                
            else:
                print("❌ No dual scores data in response")
                return None
                
        else:
            print(f"❌ API request failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return None

def suggest_improvements(df):
    """Suggest improvements based on the analysis."""
    print(f"\n💡 Improvement Suggestions:")
    
    if df is None:
        return
    
    # Analyze OpenAI issues
    openai_unique = df['openai_score'].unique()
    if len(openai_unique) <= 5:
        print(f"   🚨 OpenAI Issue: Only {len(openai_unique)} unique scores - likely falling back to simplified scoring")
        print(f"   OpenAI scores: {sorted(openai_unique)}")
    
    # Analyze local algorithm
    local_std = df['local_score'].std()
    if local_std < 10:
        print(f"   ⚠️  Local Algorithm Issue: Low variance ({local_std:.1f}) - algorithm might be too conservative")
    elif local_std > 25:
        print(f"   ✅ Local Algorithm: Good variance ({local_std:.1f}) - algorithm is differentiating stocks well")
    
    # Threshold suggestions
    buy_count_65 = len(df[df['combined_score'] >= 65])
    buy_count_60 = len(df[df['combined_score'] >= 60])
    buy_count_55 = len(df[df['combined_score'] >= 55])
    
    print(f"\n📊 Threshold Recommendations:")
    print(f"   Current threshold (65): {buy_count_65} BUY recommendations ({buy_count_65/len(df)*100:.1f}%)")
    print(f"   Suggested threshold (60): {buy_count_60} BUY recommendations ({buy_count_60/len(df)*100:.1f}%)")
    print(f"   Suggested threshold (55): {buy_count_55} BUY recommendations ({buy_count_55/len(df)*100:.1f}%)")
    
    # Optimal threshold suggestion
    if buy_count_65 < 5:
        print(f"   💡 Recommendation: Lower BUY threshold to 60 or 55 for more actionable recommendations")
    elif buy_count_65 > 30:
        print(f"   💡 Recommendation: Consider raising BUY threshold to 70 for more selective recommendations")

def main():
    """Run the full distribution analysis."""
    print("🚀 Full Distribution Analysis")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Analyze full distribution
    df = analyze_full_distribution()
    
    # Suggest improvements
    suggest_improvements(df)
    
    print("\n" + "=" * 80)
    print("✅ Full Distribution Analysis Completed!")
    
    if df is not None:
        print(f"\n📋 Summary:")
        print(f"   Total symbols analyzed: {len(df)}")
        print(f"   Local algorithm variance: {df['local_score'].std():.1f}")
        print(f"   OpenAI algorithm variance: {df['openai_score'].std():.1f}")
        print(f"   BUY recommendations (threshold 65): {len(df[df['combined_score'] >= 65])}")
        print(f"   Next steps: Debug OpenAI scoring and optimize thresholds")

if __name__ == "__main__":
    main() 