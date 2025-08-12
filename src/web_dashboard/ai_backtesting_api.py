#!/usr/bin/env python3
"""
AI Backtesting API
API endpoints for AI strategy backtesting functionality.
Completely separate from existing portfolio functionality.
"""

from flask import Blueprint, request, jsonify
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Import the backtesting engine
try:
    from ..backtesting.ai_backtesting_engine import (
        AIBacktestingEngine, 
        BacktestParameters, 
        RiskLevel
    )
except ImportError:
    # Fallback for when running from dashboard app context
    from src.backtesting.ai_backtesting_engine import (
        AIBacktestingEngine, 
        BacktestParameters, 
        RiskLevel
    )

# Create blueprint
ai_backtesting_api = Blueprint('ai_backtesting', __name__, url_prefix='/api/ai-backtesting')

# Initialize backtesting engine
backtesting_engine = AIBacktestingEngine()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@ai_backtesting_api.route('/status', methods=['GET'])
def get_status():
    """Get current backtesting engine status."""
    try:
        status = {
            'success': True,
            'engine_status': 'ready',
            'parameters': {
                'available_cash': backtesting_engine.parameters.available_cash,
                'transaction_limit_pct': backtesting_engine.parameters.transaction_limit_pct,
                'stop_loss_pct': backtesting_engine.parameters.stop_loss_pct,
                'stop_gain_pct': backtesting_engine.parameters.stop_gain_pct,
                'safe_net': backtesting_engine.parameters.safe_net,
                'risk_tolerance': backtesting_engine.parameters.risk_tolerance.value,
                'recommendation_threshold': backtesting_engine.parameters.recommendation_threshold
            },
            'has_results': len(backtesting_engine.get_results()) > 0,
            'total_strategies_tested': len(backtesting_engine.get_results()),
            'last_execution': backtesting_engine.summary.execution_timestamp.isoformat() if backtesting_engine.summary else None
        }
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting backtesting status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_backtesting_api.route('/parameters', methods=['GET', 'PUT'])
def manage_parameters():
    """Get or update backtesting parameters."""
    if request.method == 'GET':
        try:
            params = backtesting_engine.parameters
            return jsonify({
                'success': True,
                'parameters': {
                    'available_cash': params.available_cash,
                    'transaction_limit_pct': params.transaction_limit_pct,
                    'stop_loss_pct': params.stop_loss_pct,
                    'stop_gain_pct': params.stop_gain_pct,
                    'safe_net': params.safe_net,
                    'risk_tolerance': params.risk_tolerance.value,
                    'recommendation_threshold': params.recommendation_threshold
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting parameters: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'No data provided'
                }), 400
            
            # Create new parameters object
            new_params = BacktestParameters(
                available_cash=float(data.get('available_cash', 1_000_000.0)),
                transaction_limit_pct=float(data.get('transaction_limit_pct', 0.02)),
                stop_loss_pct=float(data.get('stop_loss_pct', 0.05)),
                stop_gain_pct=float(data.get('stop_gain_pct', 0.20)),
                safe_net=float(data.get('safe_net', 10_000.0)),
                risk_tolerance=RiskLevel(data.get('risk_tolerance', 'moderate')),
                recommendation_threshold=float(data.get('recommendation_threshold', 0.20))
            )
            
            # Update engine parameters
            backtesting_engine.set_parameters(new_params)
            
            return jsonify({
                'success': True,
                'message': 'Parameters updated successfully',
                'parameters': {
                    'available_cash': new_params.available_cash,
                    'transaction_limit_pct': new_params.transaction_limit_pct,
                    'stop_loss_pct': new_params.stop_loss_pct,
                    'stop_gain_pct': new_params.stop_gain_pct,
                    'safe_net': new_params.safe_net,
                    'risk_tolerance': new_params.risk_tolerance.value,
                    'recommendation_threshold': new_params.recommendation_threshold
                }
            })
            
        except Exception as e:
            logger.error(f"Error updating parameters: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500


@ai_backtesting_api.route('/strategies', methods=['GET'])
def get_available_strategies():
    """Get available trading strategies."""
    try:
        strategies = backtesting_engine.get_available_strategies()
        strategy_list = [{'value': s.value, 'label': s.value.replace('_', ' ').title()} for s in strategies]
        
        return jsonify({
            'success': True,
            'strategies': strategy_list
        })
        
    except Exception as e:
        logger.error(f"Error getting strategies: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_backtesting_api.route('/combinations', methods=['GET'])
def get_strategy_combinations():
    """Get available strategy combinations."""
    try:
        max_combinations = request.args.get('max_combinations', 3, type=int)
        combinations = backtesting_engine.generate_strategy_combinations(max_combinations)
        
        # Format combinations for frontend
        formatted_combinations = []
        for combo in combinations:
            formatted_combinations.append({
                'combination': combo,
                'name': ' + '.join(combo),
                'count': len(combo)
            })
        
        return jsonify({
            'success': True,
            'combinations': formatted_combinations,
            'total_count': len(formatted_combinations)
        })
        
    except Exception as e:
        logger.error(f"Error getting strategy combinations: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_backtesting_api.route('/run', methods=['POST'])
def run_backtest():
    """Run AI backtesting on historical data."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Get data collection ID
        collection_id = data.get('collection_id')
        if not collection_id:
            return jsonify({
                'success': False,
                'error': 'Collection ID is required'
            }), 400
        
        # Get strategy combinations (optional)
        strategy_combinations = data.get('strategy_combinations')
        
        # Get historical data from the collection
        # This is a placeholder - in real implementation, you'd fetch from data manager
        historical_data = _get_historical_data(collection_id)
        
        if historical_data is None or historical_data.empty:
            return jsonify({
                'success': False,
                'error': f'No historical data found for collection {collection_id}'
            }), 404
        
        # Run backtesting
        summary = backtesting_engine.run_backtest(historical_data, strategy_combinations)
        
        return jsonify({
            'success': True,
            'message': f'Backtesting completed successfully. Tested {summary.total_strategies_tested} strategies.',
            'summary': {
                'total_strategies_tested': summary.total_strategies_tested,
                'best_strategy': {
                    'name': summary.best_strategy.strategy_name,
                    'total_return_pct': summary.best_strategy.total_return_pct,
                    'sharpe_ratio': summary.best_strategy.sharpe_ratio,
                    'risk_score': summary.best_strategy.risk_score
                },
                'average_return': summary.average_return,
                'average_sharpe': summary.average_sharpe,
                'recommendations': summary.recommendations,
                'execution_timestamp': summary.execution_timestamp.isoformat(),
                'total_execution_time': summary.total_execution_time
            }
        })
        
    except Exception as e:
        logger.error(f"Error running backtest: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_backtesting_api.route('/results', methods=['GET'])
def get_results():
    """Get backtesting results."""
    try:
        results = backtesting_engine.get_results()
        
        if not results:
            return jsonify({
                'success': True,
                'message': 'No backtesting results available',
                'results': []
            })
        
        # Format results for frontend
        formatted_results = []
        for result in results:
            formatted_results.append({
                'strategy_name': result.strategy_name,
                'strategy_combination': result.strategy_combination,
                'total_return': result.total_return,
                'total_return_pct': result.total_return_pct,
                'sharpe_ratio': result.sharpe_ratio,
                'max_drawdown': result.max_drawdown,
                'max_drawdown_pct': result.max_drawdown_pct,
                'total_trades': result.total_trades,
                'winning_trades': result.winning_trades,
                'losing_trades': result.losing_trades,
                'win_rate': result.win_rate,
                'risk_score': result.risk_score,
                'final_portfolio_value': result.final_portfolio_value,
                'execution_time': result.execution_time
            })
        
        return jsonify({
            'success': True,
            'results': formatted_results,
            'total_count': len(formatted_results)
        })
        
    except Exception as e:
        logger.error(f"Error getting results: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_backtesting_api.route('/summary', methods=['GET'])
def get_summary():
    """Get backtesting summary."""
    try:
        summary = backtesting_engine.get_summary()
        
        if not summary:
            return jsonify({
                'success': True,
                'message': 'No backtesting summary available',
                'summary': None
            })
        
        formatted_summary = {
            'total_strategies_tested': summary.total_strategies_tested,
            'best_strategy': {
                'name': summary.best_strategy.strategy_name,
                'total_return_pct': summary.best_strategy.total_return_pct,
                'sharpe_ratio': summary.best_strategy.sharpe_ratio,
                'risk_score': summary.best_strategy.risk_score,
                'win_rate': summary.best_strategy.win_rate
            },
            'worst_strategy': {
                'name': summary.worst_strategy.strategy_name,
                'total_return_pct': summary.worst_strategy.total_return_pct,
                'sharpe_ratio': summary.worst_strategy.sharpe_ratio,
                'risk_score': summary.worst_strategy.risk_score
            },
            'average_return': summary.average_return,
            'average_sharpe': summary.average_sharpe,
            'recommendations': summary.recommendations,
            'execution_timestamp': summary.execution_timestamp.isoformat(),
            'total_execution_time': summary.total_execution_time
        }
        
        return jsonify({
            'success': True,
            'summary': formatted_summary
        })
        
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_backtesting_api.route('/reset', methods=['POST'])
def reset_results():
    """Reset all backtesting results."""
    try:
        backtesting_engine.reset_results()
        
        return jsonify({
            'success': True,
            'message': 'Backtesting results reset successfully'
        })
        
    except Exception as e:
        logger.error(f"Error resetting results: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_backtesting_api.route('/export', methods=['POST'])
def export_results():
    """Export backtesting results to CSV."""
    try:
        data = request.get_json() or {}
        filename = data.get('filename')
        
        exported_file = backtesting_engine.export_results(filename)
        
        return jsonify({
            'success': True,
            'message': 'Results exported successfully',
            'filename': exported_file
        })
        
    except Exception as e:
        logger.error(f"Error exporting results: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def _get_historical_data(collection_id: str):
    """
    Get historical data from a data collection.
    This is a placeholder - in real implementation, you'd fetch from data manager.
    """
    try:
        # Placeholder: create sample data for testing
        import pandas as pd
        import numpy as np
        
        # Generate sample OHLCV data
        dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
        np.random.seed(42)  # For reproducible results
        
        sample_data = pd.DataFrame({
            'date': dates,
            'symbol': 'AAPL',
            'open': 150 + np.random.randn(len(dates)) * 5,
            'high': 155 + np.random.randn(len(dates)) * 3,
            'low': 145 + np.random.randn(len(dates)) * 3,
            'close': 150 + np.random.randn(len(dates)) * 5,
            'volume': np.random.randint(1000000, 10000000, len(dates))
        })
        
        # Ensure realistic OHLC relationships
        sample_data['high'] = np.maximum(sample_data['high'], sample_data[['open', 'close']].max(axis=1))
        sample_data['low'] = np.minimum(sample_data['low'], sample_data[['open', 'close']].min(axis=1))
        
        logger.info(f"Generated sample data for collection {collection_id}: {len(sample_data)} records")
        return sample_data
        
    except Exception as e:
        logger.error(f"Error getting historical data: {e}")
        return None


# Error handlers
@ai_backtesting_api.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404


@ai_backtesting_api.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500
