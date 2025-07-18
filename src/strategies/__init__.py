"""
Trading strategies for the SMART STOCK TRADING SYSTEM.
"""

from .base_strategy import BaseStrategy
from .macd_strategy import MACDStrategy
from .macd_canonical_strategy import MACDCanonicalStrategy
from .macd_aggressive_strategy import MACDAggressiveStrategy
from .macd_conservative_strategy import MACDConservativeStrategy

__all__ = [
    'BaseStrategy', 
    'MACDStrategy',
    'MACDCanonicalStrategy',
    'MACDAggressiveStrategy',
    'MACDConservativeStrategy'
] 