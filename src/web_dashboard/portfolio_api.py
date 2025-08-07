from flask import Blueprint, request, jsonify
import logging
from datetime import datetime, date
from typing import Dict, List, Optional

from ..portfolio_management.portfolio_manager import PortfolioManager
from ..portfolio_management.portfolio_database import PortfolioType, TransactionType
from ..data_collection.data_manager import DataCollectionManager as DataManager
from ..ai_ranking.hybrid_ranking_engine import HybridRankingEngine

# Create Blueprint
portfolio_api = Blueprint('portfolio_api', __name__)

# Initialize components
data_manager = DataManager()
hybrid_ranking_engine = HybridRankingEngine(data_manager)
portfolio_manager = PortfolioManager(data_manager, hybrid_ranking_engine)

@portfolio_api.route('/portfolios', methods=['GET'])
def get_portfolios():
    """Get all portfolios."""
    try:
        portfolios = portfolio_manager.db.get_all_portfolios()
        
        portfolio_data = []
        for portfolio in portfolios:
            summary = portfolio_manager.get_portfolio_summary(portfolio.id)
            portfolio_data.append({
                'id': portfolio.id,
                'name': portfolio.name,
                'type': portfolio.portfolio_type.value,
                'initial_cash': portfolio.initial_cash,
                'current_cash': portfolio.current_cash,
                'created_at': portfolio.created_at.isoformat(),
                'updated_at': portfolio.updated_at.isoformat(),
                'settings': portfolio.settings,
                'summary': {
                    'total_value': summary.total_value if summary else 0,
                    'total_pnl': summary.total_pnl if summary else 0,
                    'total_pnl_pct': summary.total_pnl_pct if summary else 0,
                    'positions_count': summary.positions_count if summary else 0,
                    'cash': summary.cash if summary else 0,
                    'positions_value': summary.positions_value if summary else 0
                } if summary else None
            })
        
        return jsonify({
            'success': True,
            'portfolios': portfolio_data
        })
        
    except Exception as e:
        logging.error(f"Error getting portfolios: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@portfolio_api.route('/portfolios/<int:portfolio_id>', methods=['GET'])
def get_portfolio(portfolio_id: int):
    """Get specific portfolio details."""
    try:
        portfolio = portfolio_manager.db.get_portfolio(portfolio_id)
        if not portfolio:
            return jsonify({
                'success': False,
                'error': 'Portfolio not found'
            }), 404
        
        summary = portfolio_manager.get_portfolio_summary(portfolio_id)
        positions = portfolio_manager.db.get_portfolio_positions(portfolio_id)
        transactions = portfolio_manager.db.get_portfolio_transactions(portfolio_id, limit=50)
        
        return jsonify({
            'success': True,
            'portfolio': {
                'id': portfolio.id,
                'name': portfolio.name,
                'type': portfolio.portfolio_type.value,
                'initial_cash': portfolio.initial_cash,
                'current_cash': portfolio.current_cash,
                'created_at': portfolio.created_at.isoformat(),
                'updated_at': portfolio.updated_at.isoformat(),
                'settings': portfolio.settings
            },
            'summary': {
                'total_value': summary.total_value if summary else 0,
                'total_pnl': summary.total_pnl if summary else 0,
                'total_pnl_pct': summary.total_pnl_pct if summary else 0,
                'positions_count': summary.positions_count if summary else 0,
                'cash': summary.cash if summary else 0,
                'positions_value': summary.positions_value if summary else 0,
                'best_position': {
                    'symbol': summary.best_position.symbol,
                    'pnl_pct': summary.best_position.pnl_pct
                } if summary and summary.best_position else None,
                'worst_position': {
                    'symbol': summary.worst_position.symbol,
                    'pnl_pct': summary.worst_position.pnl_pct
                } if summary and summary.worst_position else None
            } if summary else None,
            'positions': [
                {
                    'id': pos.id,
                    'symbol': pos.symbol,
                    'shares': pos.shares,
                    'avg_price': pos.avg_price,
                    'current_price': pos.current_price,
                    'pnl': pos.pnl,
                    'pnl_pct': pos.pnl_pct,
                    'value': pos.shares * pos.current_price,
                    'created_at': pos.created_at.isoformat(),
                    'updated_at': pos.updated_at.isoformat()
                }
                for pos in positions
            ],
            'transactions': [
                {
                    'id': trans.id,
                    'symbol': trans.symbol,
                    'type': trans.transaction_type.value,
                    'shares': trans.shares,
                    'price': trans.price,
                    'total_amount': trans.total_amount,
                    'pnl': trans.pnl,
                    'timestamp': trans.timestamp.isoformat(),
                    'notes': trans.notes
                }
                for trans in transactions
            ]
        })
        
    except Exception as e:
        logging.error(f"Error getting portfolio {portfolio_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@portfolio_api.route('/portfolios/<int:portfolio_id>/buy', methods=['POST'])
def buy_stock(portfolio_id: int):
    """Buy stock for a portfolio."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        symbol = data.get('symbol')
        shares = data.get('shares')
        price = data.get('price')  # Optional - will fetch last traded price if not provided
        notes = data.get('notes')
        
        if not all([symbol, shares]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: symbol, shares'
            }), 400
        
        # Convert price to float if provided, otherwise None
        price_float = float(price) if price is not None else None
        
        success = portfolio_manager.buy_stock(
            portfolio_id=portfolio_id,
            symbol=symbol.upper(),
            shares=float(shares),
            price=price_float,
            notes=notes
        )
        
        if success:
            price_msg = f" at ${price}" if price else " at last traded price"
            return jsonify({
                'success': True,
                'message': f'Successfully bought {shares} shares of {symbol}{price_msg}'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to buy stock'
            }), 400
        
    except Exception as e:
        logging.error(f"Error buying stock: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@portfolio_api.route('/portfolios/<int:portfolio_id>/sell', methods=['POST'])
def sell_stock(portfolio_id: int):
    """Sell stock from a portfolio."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        symbol = data.get('symbol')
        shares = data.get('shares')
        price = data.get('price')  # Optional - will fetch last traded price if not provided
        notes = data.get('notes')
        
        if not all([symbol, shares]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: symbol, shares'
            }), 400
        
        # Convert price to float if provided, otherwise None
        price_float = float(price) if price is not None else None
        
        success = portfolio_manager.sell_stock(
            portfolio_id=portfolio_id,
            symbol=symbol.upper(),
            shares=float(shares),
            price=price_float,
            notes=notes
        )
        
        if success:
            price_msg = f" at ${price}" if price else " at last traded price"
            return jsonify({
                'success': True,
                'message': f'Successfully sold {shares} shares of {symbol}{price_msg}'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to sell stock'
            }), 400
        
    except Exception as e:
        logging.error(f"Error selling stock: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@portfolio_api.route('/portfolios/<int:portfolio_id>/manage-ai', methods=['POST'])
def manage_ai_portfolio(portfolio_id: int):
    """Manage AI portfolio based on hybrid ranking."""
    try:
        data = request.get_json() or {}
        collection_id = data.get('collection_id', 'ALL_20250803_160817')
        
        result = portfolio_manager.manage_ai_portfolio(
            portfolio_id=portfolio_id,
            collection_id=collection_id
        )
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Error managing AI portfolio: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@portfolio_api.route('/portfolios/<int:portfolio_id>/performance', methods=['GET'])
def get_portfolio_performance(portfolio_id: int):
    """Get portfolio performance history."""
    try:
        days = request.args.get('days', 30, type=int)
        
        performance_history = portfolio_manager.db.get_portfolio_performance_history(
            portfolio_id=portfolio_id,
            days=days
        )
        
        return jsonify({
            'success': True,
            'performance': [
                {
                    'date': perf.date.isoformat(),
                    'total_value': perf.total_value,
                    'pnl': perf.pnl,
                    'return_pct': perf.return_pct,
                    'cash': perf.cash,
                    'positions_value': perf.positions_value
                }
                for perf in performance_history
            ]
        })
        
    except Exception as e:
        logging.error(f"Error getting portfolio performance: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@portfolio_api.route('/portfolios/comparison', methods=['GET'])
def get_portfolio_comparison():
    """Get comparison between user and AI portfolios."""
    try:
        comparison = portfolio_manager.get_portfolio_comparison()
        
        return jsonify({
            'success': True,
            'comparison': comparison
        })
        
    except Exception as e:
        logging.error(f"Error getting portfolio comparison: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@portfolio_api.route('/portfolios/<int:portfolio_id>/update-prices', methods=['POST'])
def update_portfolio_prices(portfolio_id: int):
    """Update portfolio prices."""
    try:
        data = request.get_json()
        
        if not data or 'prices' not in data:
            return jsonify({
                'success': False,
                'error': 'No price data provided'
            }), 400
        
        price_data = data['prices']
        
        # Update prices
        portfolio_manager.update_portfolio_prices(portfolio_id, price_data)
        
        # Record daily snapshot
        portfolio_manager.record_daily_snapshot(portfolio_id, price_data)
        
        return jsonify({
            'success': True,
            'message': f'Updated prices for portfolio {portfolio_id}'
        })
        
    except Exception as e:
        logging.error(f"Error updating portfolio prices: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@portfolio_api.route('/portfolios/<int:portfolio_id>/transactions', methods=['GET'])
def get_portfolio_transactions(portfolio_id: int):
    """Get portfolio transactions."""
    try:
        limit = request.args.get('limit', 100, type=int)
        
        transactions = portfolio_manager.db.get_portfolio_transactions(
            portfolio_id=portfolio_id,
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'transactions': [
                {
                    'id': trans.id,
                    'symbol': trans.symbol,
                    'type': trans.transaction_type.value,
                    'shares': trans.shares,
                    'price': trans.price,
                    'total_amount': trans.total_amount,
                    'pnl': trans.pnl,
                    'timestamp': trans.timestamp.isoformat(),
                    'notes': trans.notes
                }
                for trans in transactions
            ]
        })
        
    except Exception as e:
        logging.error(f"Error getting portfolio transactions: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@portfolio_api.route('/portfolios/<int:portfolio_id>/positions', methods=['GET'])
def get_portfolio_positions(portfolio_id: int):
    """Get portfolio positions."""
    try:
        positions = portfolio_manager.db.get_portfolio_positions(portfolio_id)
        
        return jsonify({
            'success': True,
            'positions': [
                {
                    'id': pos.id,
                    'symbol': pos.symbol,
                    'shares': pos.shares,
                    'avg_price': pos.avg_price,
                    'current_price': pos.current_price,
                    'pnl': pos.pnl,
                    'pnl_pct': pos.pnl_pct,
                    'value': pos.shares * pos.current_price,
                    'created_at': pos.created_at.isoformat(),
                    'updated_at': pos.updated_at.isoformat()
                }
                for pos in positions
            ]
        })
        
    except Exception as e:
        logging.error(f"Error getting portfolio positions: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500 