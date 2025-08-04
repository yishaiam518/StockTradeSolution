"""
MACD Aggressive Strategy

A high-frequency trading variant of the MACD strategy with more aggressive parameters
for faster entry and exit signals.
"""

from .macd_strategy import MACDStrategy


class MACDAggressiveStrategy(MACDStrategy):
    """
    Aggressive MACD Strategy for high-frequency trading.
    
    Features:
    - Lower entry threshold (0.2) for more frequent signals
    - Wider RSI range (30-70) for more opportunities
    - Faster exits (3% take profit, 2% stop loss)
    - Shorter holding periods (7 days max)
    - Higher MACD weight (0.7) for trend following
    """
    
    def __init__(self, config=None):
        """Initialize the aggressive MACD strategy."""
        super().__init__(config)
        
        # Override with aggressive parameters
        self.entry_threshold = 0.2  # Lower threshold for more signals
        self.rsi_range = [30, 70]  # Wider range for more opportunities
        self.take_profit_pct = 3.0  # Faster profit taking
        self.stop_loss_pct = 2.0    # Tighter stop loss
        self.max_hold_days = 7      # Shorter holding period
        
        # More aggressive entry weights
        self.entry_weights = {
            'macd_crossover_up': 0.7,      # Higher weight for MACD
            'rsi_neutral': 0.2,             # Lower RSI weight
            'price_above_ema_short': 0.05,  # Minimal EMA weight
            'price_above_ema_long': 0.05    # Minimal EMA weight
        }
        
        self.strategy_name = "MACDAggressiveStrategy"
    
    def should_entry(self, data, i):
        """
        Check if we should enter a position (aggressive version).
        
        Args:
            data: DataFrame with price and indicator data
            i: Current index
            
        Returns:
            dict: Entry signal with confidence and reason
        """
        if i < 50:  # Need enough data for indicators
            return {'signal': False, 'confidence': 0, 'reason': 'Insufficient data'}
        
        # Get current data point
        current = data.iloc[i]
        
        # Calculate entry score with aggressive parameters
        score = 0
        reasons = []
        
        # MACD crossover (higher weight)
        if current.get('macd_crossover_up', False):
            score += self.entry_weights['macd_crossover_up']
            reasons.append('MACD crossover up')
        
        # RSI in neutral range (wider range)
        rsi = current.get('rsi', 50)
        if self.rsi_range[0] <= rsi <= self.rsi_range[1]:
            score += self.entry_weights['rsi_neutral']
            reasons.append(f'RSI neutral ({rsi:.1f})')
        
        # Price above short EMA
        if current.get('price_above_ema_short', False):
            score += self.entry_weights['price_above_ema_short']
            reasons.append('Price above short EMA')
        
        # Price above long EMA
        if current.get('price_above_ema_long', False):
            score += self.entry_weights['price_above_ema_long']
            reasons.append('Price above long EMA')
        
        # Check if we should enter
        should_enter = score >= self.entry_threshold
        
        return {
            'signal': should_enter,
            'confidence': score,
            'reason': ' + '.join(reasons) if reasons else 'No signals',
            'score': score,
            'threshold': self.entry_threshold
        }
    
    def should_exit(self, data, i, entry_price, entry_date):
        """
        Check if we should exit a position (aggressive version).
        
        Args:
            data: DataFrame with price and indicator data
            i: Current index
            entry_price: Entry price
            entry_date: Entry date
            
        Returns:
            dict: Exit signal with reason and details
        """
        if i < 50:
            return {'signal': False, 'reason': 'Insufficient data'}
        
        current = data.iloc[i]
        current_price = current['close']
        current_date = data.index[i]
        
        # Calculate PnL
        pnl_pct = ((current_price - entry_price) / entry_price) * 100
        
        # Time-based exit (shorter period)
        days_held = (current_date - entry_date).days
        
        # Aggressive exit conditions
        if pnl_pct >= self.take_profit_pct:
            return {
                'signal': True,
                'reason': f'Take profit ({pnl_pct:.2f}%)',
                'pnl_pct': pnl_pct,
                'exit_type': 'take_profit'
            }
        
        if pnl_pct <= -self.stop_loss_pct:
            return {
                'signal': True,
                'reason': f'Stop loss ({pnl_pct:.2f}%)',
                'pnl_pct': pnl_pct,
                'exit_type': 'stop_loss'
            }
        
        if days_held >= self.max_hold_days:
            return {
                'signal': True,
                'reason': f'Max hold days ({days_held} days)',
                'pnl_pct': pnl_pct,
                'exit_type': 'time_exit'
            }
        
        # MACD crossover down (aggressive exit)
        if current.get('macd_crossover_down', False):
            return {
                'signal': True,
                'reason': 'MACD crossover down',
                'pnl_pct': pnl_pct,
                'exit_type': 'macd_exit'
            }
        
        # RSI overbought/oversold (wider range)
        rsi = current.get('rsi', 50)
        if rsi > 75 or rsi < 25:
            return {
                'signal': True,
                'reason': f'RSI extreme ({rsi:.1f})',
                'pnl_pct': pnl_pct,
                'exit_type': 'rsi_exit'
            }
        
        return {
            'signal': False,
            'reason': f'Holding (PnL: {pnl_pct:.2f}%, Days: {days_held})',
            'pnl_pct': pnl_pct,
            'days_held': days_held
        } 