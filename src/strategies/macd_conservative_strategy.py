"""
MACD Conservative Strategy

A long-term trading variant of the MACD strategy with conservative parameters
for stable, long-term positions with lower risk.
"""

from .macd_strategy import MACDStrategy


class MACDConservativeStrategy(MACDStrategy):
    """
    Conservative MACD Strategy for long-term positions.
    
    Features:
    - Higher entry threshold (0.6) for stronger signals
    - Narrower RSI range (45-55) for more precise entries
    - Slower exits (10% take profit, 5% stop loss)
    - Longer holding periods (60 days max)
    - Balanced weights for stability
    """
    
    def __init__(self, config=None):
        """Initialize the conservative MACD strategy."""
        super().__init__(config)
        
        # Override with conservative parameters
        self.entry_threshold = 0.6  # Higher threshold for stronger signals
        self.rsi_range = [45, 55]  # Narrower range for precision
        self.take_profit_pct = 10.0  # Higher profit target
        self.stop_loss_pct = 5.0     # Wider stop loss
        self.max_hold_days = 60      # Longer holding period
        
        # Balanced entry weights
        self.entry_weights = {
            'macd_crossover_up': 0.4,      # Balanced MACD weight
            'rsi_neutral': 0.4,             # Higher RSI weight for stability
            'price_above_ema_short': 0.1,   # Standard EMA weight
            'price_above_ema_long': 0.1     # Standard EMA weight
        }
        
        self.strategy_name = "MACDConservativeStrategy"
    
    def should_entry(self, data, i):
        """
        Check if we should enter a position (conservative version).
        
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
        
        # Calculate entry score with conservative parameters
        score = 0
        reasons = []
        
        # MACD crossover (balanced weight)
        if current.get('macd_crossover_up', False):
            score += self.entry_weights['macd_crossover_up']
            reasons.append('MACD crossover up')
        
        # RSI in neutral range (narrower range)
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
        Check if we should exit a position (conservative version).
        
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
        
        # Time-based exit (longer period)
        days_held = (current_date - entry_date).days
        
        # Conservative exit conditions
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
        
        # MACD crossover down (conservative exit)
        if current.get('macd_crossover_down', False):
            return {
                'signal': True,
                'reason': 'MACD crossover down',
                'pnl_pct': pnl_pct,
                'exit_type': 'macd_exit'
            }
        
        # RSI overbought/oversold (narrower range)
        rsi = current.get('rsi', 50)
        if rsi > 70 or rsi < 30:
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