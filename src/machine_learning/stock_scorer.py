"""
Unified Stock Scoring System for the SMART STOCK TRADING SYSTEM.

This module provides a unified scoring system that:
- Creates separate scoring lists for different modes (backtesting, historical, automation)
- Integrates with strategy+profile selection
- Generates signals for the trading system
- Supports multiple data sources (NASDAQ, DOW, etc.)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from src.utils.config_loader import ConfigLoader
from src.utils.logger import get_logger
from src.data_engine import DataEngine
from src.indicators import TechnicalIndicators
from src.strategies import MACDStrategy


class DataSource(Enum):
    """Supported data sources for stock scoring."""
    NASDAQ = "NASDAQ"
    DOW = "DOW"
    SP500 = "SP500"
    CUSTOM = "CUSTOM"


class ScoringMethod(Enum):
    """Available scoring methods."""
    TECHNICAL = "technical"
    INDUSTRY = "industry"
    TREND = "trend"
    HYBRID = "hybrid"


class ScoringMode(Enum):
    """Different scoring modes for different use cases."""
    BACKTESTING = "backtesting"
    HISTORICAL = "historical"
    AUTOMATION = "automation"


@dataclass
class StockScore:
    """Represents a stock score with metadata."""
    symbol: str
    score: float
    confidence: float
    method: ScoringMethod
    signals: Dict[str, Any]
    timestamp: datetime
    data_source: DataSource
    strategy_profile: str
    mode: ScoringMode


class UnifiedStockScorer:
    """
    Unified stock scoring system that creates separate lists for different modes.
    
    This system:
    - Creates separate scoring lists for backtesting, historical, and automation
    - Integrates strategy+profile selection
    - Generates signals for the trading system
    - Maintains separate caches for different modes
    """
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        """Initialize the unified stock scorer."""
        self.config = ConfigLoader(config_path)
        self.logger = get_logger(__name__)
        
        # Core components
        self.data_engine = DataEngine()
        self.indicators = TechnicalIndicators()
        
        # Scoring configuration
        self.scoring_config = self.config.get('stock_scoring', {})
        self.default_profile = self.scoring_config.get('default_profile', 'balanced')
        
        # Separate caches for different modes
        self.score_cache = {
            ScoringMode.BACKTESTING: {},
            ScoringMode.HISTORICAL: {},
            ScoringMode.AUTOMATION: {}
        }
        self.cache_duration = timedelta(minutes=self.scoring_config.get('cache_duration_minutes', 15))
        
        # Separate scoring lists for different modes
        self.scoring_lists = {
            ScoringMode.BACKTESTING: [],
            ScoringMode.HISTORICAL: [],
            ScoringMode.AUTOMATION: []
        }
        
        self.logger.info("Unified Stock Scorer initialized")
    
    def create_scoring_list(self, 
                           mode: ScoringMode,
                           strategy: str = "MACD",
                           profile: str = "balanced",
                           symbol: str = None,
                           max_stocks: int = 50,
                           min_score: float = 0.3) -> List[StockScore]:
        """
        Create a scoring list for a specific mode.
        
        Args:
            mode: Scoring mode (backtesting, historical, automation)
            strategy: Strategy to use
            profile: Strategy profile to use
            symbol: Specific symbol for backtesting (None for historical/automation)
            max_stocks: Maximum number of stocks to score
            min_score: Minimum score threshold
            
        Returns:
            List of stock scores for the specified mode
        """
        try:
            # Get stock universe based on mode
            if mode == ScoringMode.BACKTESTING and symbol:
                # For backtesting, score only the specified symbol
                symbols = [symbol]
                self.logger.info(f"Backtesting mode: scoring single symbol {symbol}")
            elif mode == ScoringMode.HISTORICAL:
                # For historical, use all available stocks
                symbols = self._get_all_stocks()
                self.logger.info(f"Historical mode: scoring {len(symbols)} symbols")
            else:  # AUTOMATION
                # For automation, use watchlist
                symbols = self._get_watchlist_stocks()
                self.logger.info(f"Automation mode: scoring {len(symbols)} symbols")
            
            # Limit to max_stocks
            symbols = symbols[:max_stocks]
            self.logger.info(f"Limited to {len(symbols)} symbols for scoring")
            
            # Score each stock
            scores = []
            successful_scores = 0
            for sym in symbols:
                try:
                    score = self._score_single_stock(sym, strategy, profile, mode)
                    if score and score.score >= min_score:
                        scores.append(score)
                        successful_scores += 1
                        self.logger.debug(f"Scored {sym}: {score.score:.3f}")
                except Exception as e:
                    self.logger.warning(f"Error scoring {sym}: {str(e)}")
                    continue
            
            # Sort by score (highest first)
            scores.sort(key=lambda x: x.score, reverse=True)
            
            # Store in mode-specific list
            self.scoring_lists[mode] = scores
            
            self.logger.info(f"Created {mode.value} scoring list with {len(scores)} stocks (successful scores: {successful_scores})")
            return scores
            
        except Exception as e:
            self.logger.error(f"Error creating {mode.value} scoring list: {str(e)}")
            return []
    
    def get_scoring_list(self, mode: ScoringMode) -> List[StockScore]:
        """Get the current scoring list for a mode."""
        return self.scoring_lists.get(mode, [])
    
    def update_scoring_list(self, mode: ScoringMode, strategy: str, profile: str, 
                          symbol: str = None, max_stocks: int = 50, min_score: float = 0.3):
        """Update the scoring list for a specific mode."""
        return self.create_scoring_list(mode, strategy, profile, symbol, max_stocks, min_score)
    
    def generate_trading_signals(self, mode: ScoringMode, strategy: str, profile: str) -> List[Dict[str, Any]]:
        """
        Generate trading signals for the current scoring list.
        
        Args:
            mode: Scoring mode
            strategy: Strategy to use
            profile: Strategy profile to use
            
        Returns:
            List of trading signals
        """
        signals = []
        scoring_list = self.get_scoring_list(mode)
        
        for score in scoring_list:
            try:
                signal = self._generate_trading_signal(score, strategy, profile)
                if signal:
                    signals.append(signal)
            except Exception as e:
                self.logger.warning(f"Error generating signal for {score.symbol}: {str(e)}")
                continue
        
        return signals
    
    def _score_single_stock(self, symbol: str, strategy: str, profile: str, mode: ScoringMode) -> Optional[StockScore]:
        """
        Score a single stock using the specified strategy and profile.
        
        Args:
            symbol: Stock symbol
            strategy: Strategy to use
            profile: Strategy profile to use
            mode: Scoring mode
            
        Returns:
            StockScore object or None if scoring fails
        """
        try:
            # Check cache first
            cache_key = f"{symbol}_{strategy}_{profile}_{mode.value}"
            cache = self.score_cache[mode]
            
            if cache_key in cache:
                cached_score = cache[cache_key]
                if datetime.now() - cached_score.timestamp < self.cache_duration:
                    return cached_score
            
            # Get data for scoring based on mode
            end_date = datetime.now()
            if mode == ScoringMode.HISTORICAL:
                # For historical mode, get 1 year of data for scoring
                start_date = end_date - timedelta(days=365)
            else:
                # For other modes, get 30 days of recent data
                start_date = end_date - timedelta(days=30)
            
            data = self.data_engine.fetch_data(symbol, start_date.strftime('%Y-%m-%d'), 
                                             end_date.strftime('%Y-%m-%d'))
            
            if data.empty:
                return None
            
            # Calculate indicators
            data_with_indicators = self.indicators.calculate_all_indicators(data)
            
            # Get strategy with profile
            strategy_instance = self._get_strategy_with_profile(strategy, profile)
            
            # Calculate technical score
            technical_score = self._calculate_technical_score(data_with_indicators, strategy_instance)
            
            # Calculate industry score
            industry_score = self._calculate_industry_score(symbol, data_with_indicators)
            
            # Calculate trend score
            trend_score = self._calculate_trend_score(data_with_indicators)
            
            # Combine scores
            weights = self.scoring_config.get('scoring_weights', {
                'technical': 0.5,
                'industry': 0.25,
                'trend': 0.25
            })
            
            total_score = (
                technical_score * weights.get('technical', 0.5) +
                industry_score * weights.get('industry', 0.25) +
                trend_score * weights.get('trend', 0.25)
            )
            
            # Calculate confidence
            confidence = self._calculate_confidence(data_with_indicators, strategy_instance)
            
            # Generate signals
            signals = self._generate_signals(data_with_indicators, strategy_instance)
            
            # Create score object
            score = StockScore(
                symbol=symbol,
                score=min(max(total_score, 0.0), 1.0),  # Clamp between 0 and 1
                confidence=confidence,
                method=ScoringMethod.HYBRID,
                signals=signals,
                timestamp=datetime.now(),
                data_source=DataSource.NASDAQ,  # Default for now
                strategy_profile=f"{strategy}_{profile}",
                mode=mode
            )
            
            # Cache the result
            cache[cache_key] = score
            
            return score
            
        except Exception as e:
            self.logger.error(f"Error scoring {symbol}: {str(e)}")
            return None
    
    def _get_strategy_with_profile(self, strategy: str, profile: str) -> MACDStrategy:
        """Get a strategy instance with the specified profile."""
        # Create a new strategy instance with the profile
        strategy_config = self.config.get('strategies', {}).get('MACD', {})
        return MACDStrategy(config_dict=strategy_config, profile=profile)
    
    def _get_all_stocks(self) -> List[str]:
        """Get all available stocks from all data sources."""
        all_stocks = []
        
        # Get stocks from all data sources
        data_sources = self.config.get('data_collection', {}).get('sources', [])
        self.logger.info(f"Found {len(data_sources)} data sources in config")
        
        for source in data_sources:
            symbols = source.get('symbols', [])
            self.logger.info(f"Source {source.get('name', 'Unknown')}: {len(symbols)} symbols")
            all_stocks.extend(symbols)
        
        # Also get stocks from automation watchlist
        watchlist = self.config.get('automation', {}).get('watchlist', [])
        self.logger.info(f"Watchlist: {len(watchlist)} symbols")
        all_stocks.extend(watchlist)
        
        # Remove duplicates and return
        unique_stocks = list(set(all_stocks))
        self.logger.info(f"Total unique stocks available: {len(unique_stocks)}")
        self.logger.info(f"Sample stocks: {unique_stocks[:10]}")
        
        return unique_stocks
    
    def _get_watchlist_stocks(self) -> List[str]:
        """Get stocks from the watchlist."""
        return self.config.get('automation.watchlist', [])
    
    def _calculate_technical_score(self, data: pd.DataFrame, strategy: MACDStrategy) -> float:
        """Calculate technical score based on strategy signals."""
        if data.empty:
            return 0.0
        
        # Get latest data point
        latest_data = data.iloc[-1]
        
        # Check entry conditions
        should_entry, entry_reason = strategy.should_entry(data, len(data) - 1)
        
        if should_entry:
            # High score for entry signal
            return 0.8
        else:
            # Lower score based on individual conditions
            score = 0.0
            
            # MACD crossover
            if latest_data.get('macd_crossover_up', False):
                score += 0.3
            
            # RSI in neutral range
            rsi = latest_data.get('rsi', 50)
            if 40 <= rsi <= 60:
                score += 0.2
            
            # Price above EMAs
            if latest_data.get('price_above_ema_short', False):
                score += 0.15
            
            if latest_data.get('price_above_ema_long', False):
                score += 0.15
            
            return min(score, 0.6)  # Cap at 0.6 for non-entry signals
    
    def _calculate_industry_score(self, symbol: str, data: pd.DataFrame) -> float:
        """Calculate industry-based score."""
        # For now, return a neutral score
        # This can be enhanced with industry classification and analysis
        return 0.5
    
    def _calculate_trend_score(self, data: pd.DataFrame) -> float:
        """Calculate trend-based score."""
        if len(data) < 20:
            return 0.0
        
        # Calculate trend strength
        close_prices = data['close'].values
        trend_strength = np.corrcoef(np.arange(len(close_prices)), close_prices)[0, 1]
        
        # Normalize to 0-1 range
        trend_score = (trend_strength + 1) / 2
        
        return max(0.0, min(1.0, trend_score))
    
    def _calculate_confidence(self, data: pd.DataFrame, strategy: MACDStrategy) -> float:
        """Calculate confidence score for the signal."""
        if data.empty:
            return 0.0
        
        # Calculate confidence based on signal strength and data quality
        confidence = 0.5  # Base confidence
        
        # Adjust based on data quality
        if len(data) >= 30:
            confidence += 0.2
        
        # Adjust based on signal strength
        latest_data = data.iloc[-1]
        if latest_data.get('macd_crossover_up', False):
            confidence += 0.2
        
        # Adjust based on volume
        if 'volume' in data.columns:
            avg_volume = data['volume'].mean()
            if avg_volume > 1000000:  # 1M volume
                confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _generate_signals(self, data: pd.DataFrame, strategy: MACDStrategy) -> Dict[str, Any]:
        """Generate trading signals from the data."""
        if data.empty:
            return {}
        
        latest_data = data.iloc[-1]
        signals = {}
        
        # MACD signals
        if 'macd' in data.columns and 'macd_signal' in data.columns:
            signals['macd_crossover_up'] = latest_data.get('macd_crossover_up', False)
            signals['macd_crossover_down'] = latest_data.get('macd_crossover_down', False)
        
        # RSI signals
        if 'rsi' in data.columns:
            rsi = latest_data.get('rsi', 50)
            signals['rsi_overbought'] = rsi > 70
            signals['rsi_oversold'] = rsi < 30
            signals['rsi_neutral'] = 40 <= rsi <= 60
        
        # EMA signals
        signals['price_above_ema_short'] = latest_data.get('price_above_ema_short', False)
        signals['price_above_ema_long'] = latest_data.get('price_above_ema_long', False)
        
        return signals
    
    def _generate_trading_signal(self, score: StockScore, strategy: str, profile: str) -> Optional[Dict[str, Any]]:
        """Generate a trading signal from a stock score."""
        try:
            # Get recent data for signal generation
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)  # Last 7 days
            
            data = self.data_engine.fetch_data(score.symbol, start_date.strftime('%Y-%m-%d'), 
                                             end_date.strftime('%Y-%m-%d'))
            
            if data.empty:
                return None
            
            # Calculate indicators
            data_with_indicators = self.indicators.calculate_all_indicators(data)
            
            # Get strategy with profile
            strategy_instance = self._get_strategy_with_profile(strategy, profile)
            
            # Check for entry signal
            should_entry, entry_reason = strategy_instance.should_entry(data_with_indicators, len(data_with_indicators) - 1)
            
            if should_entry:
                return {
                    'symbol': score.symbol,
                    'action': 'BUY',
                    'reason': entry_reason.get('summary', 'Strategy Entry'),
                    'confidence': score.confidence,
                    'score': score.score,
                    'timestamp': datetime.now(),
                    'strategy': strategy,
                    'profile': profile,
                    'price': data_with_indicators['close'].iloc[-1]
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error generating trading signal for {score.symbol}: {str(e)}")
            return None
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the scoring cache."""
        stats = {}
        for mode in ScoringMode:
            cache = self.score_cache[mode]
            stats[mode.value] = {
                'cached_scores': len(cache),
                'list_size': len(self.scoring_lists[mode])
            }
        return stats
    
    def clear_cache(self, mode: ScoringMode = None):
        """Clear the scoring cache for a specific mode or all modes."""
        if mode:
            self.score_cache[mode].clear()
            self.logger.info(f"Cleared cache for {mode.value}")
        else:
            for m in ScoringMode:
                self.score_cache[m].clear()
            self.logger.info("Cleared all caches") 