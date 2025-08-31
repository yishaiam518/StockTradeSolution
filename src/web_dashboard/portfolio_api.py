from flask import Blueprint, request, jsonify
import logging
from datetime import datetime, date
from typing import Dict, List, Optional
import sqlite3
import json

from ..portfolio_management.portfolio_manager import PortfolioManager, PortfolioSettings, RiskLevel
from ..portfolio_management.portfolio_database import PortfolioType, TransactionType
from ..data_collection.data_manager import DataCollectionManager as DataManager
from ..ai_ranking.hybrid_ranking_engine import HybridRankingEngine

# Create Blueprint
portfolio_api = Blueprint('portfolio_api', __name__)

# Initialize components lazily
_data_manager = None
_portfolio_manager = None

def get_portfolio_manager():
    """Get or create portfolio manager instance."""
    global _data_manager, _portfolio_manager
    if _portfolio_manager is None:
        try:
            _data_manager = DataManager()
            _portfolio_manager = PortfolioManager(_data_manager)
        except Exception as e:
            logging.error(f"Error initializing portfolio manager: {e}")
            raise
    return _portfolio_manager

@portfolio_api.route('/portfolios', methods=['GET', 'POST'])
def portfolios():
    """Get all portfolios or create a new portfolio."""
    if request.method == 'GET':
        try:
            portfolio_manager = get_portfolio_manager()
            portfolios = portfolio_manager.db.get_all_portfolios()
            
            portfolio_data = []
            for portfolio in portfolios:
                # Calculate summary directly instead of relying on portfolio manager
                try:
                    logging.info(f"Calculating summary for portfolio {portfolio.id}: {portfolio.name}")
                    positions = get_portfolio_manager().db.get_portfolio_positions(portfolio.id)
                    logging.info(f"Retrieved {len(positions)} positions for portfolio {portfolio.id}")
                    
                    positions_value = sum(pos.shares * pos.current_price for pos in positions)
                    total_value = portfolio.current_cash + positions_value
                    total_pnl = total_value - portfolio.initial_cash
                    total_pnl_pct = (total_pnl / portfolio.initial_cash) * 100 if portfolio.initial_cash > 0 else 0
                    
                    summary = {
                        'total_value': float(total_value),
                        'total_pnl': float(total_pnl),
                        'total_pnl_pct': float(total_pnl_pct),
                        'positions_count': int(len(positions)),
                        'cash': float(portfolio.current_cash),
                        'positions_value': float(positions_value)
                    }
                    logging.info(f"Summary calculated for portfolio {portfolio.id}: {summary}")
                except Exception as e:
                    logging.error(f"Error calculating summary for portfolio {portfolio.id}: {e}")
                    import traceback
                    logging.error(traceback.format_exc())
                    summary = {
                        'total_value': 0,
                        'total_pnl': 0,
                        'total_pnl_pct': 0,
                        'positions_count': 0,
                        'cash': portfolio.current_cash,
                        'positions_value': 0
                    }
                
                logging.info(f"Adding portfolio {portfolio.id} to response with summary: {summary}")
                portfolio_data.append({
                    'id': portfolio.id,
                    'name': portfolio.name,
                    'type': portfolio.portfolio_type.value,
                    'initial_cash': portfolio.initial_cash,
                    'current_cash': portfolio.current_cash,
                    'created_at': portfolio.created_at.isoformat(),
                    'updated_at': portfolio.updated_at.isoformat(),
                    'settings': portfolio.settings,
                    'summary': summary
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
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'No data provided'
                }), 400
            
            name = data.get('name', 'New Portfolio')
            portfolio_type = data.get('portfolio_type', 'user_managed')
            initial_cash = data.get('initial_cash', 50000.0)  # Increased to $50,000 for testing
            
            # Convert portfolio type string to enum
            if portfolio_type == 'ai_managed':
                portfolio_type_enum = PortfolioType.AI_MANAGED
            else:
                portfolio_type_enum = PortfolioType.USER_MANAGED
            
            # Create default settings for the new portfolio
            
            if portfolio_type == 'ai_managed':
                default_settings = PortfolioSettings(
                    initial_cash=initial_cash,
                    max_position_size=0.08,
                    max_positions=15,
                    cash_reserve_pct=0.10,
                    risk_level=RiskLevel.CONSERVATIVE,
                    rebalance_frequency="monthly",
                    cash_for_trading=initial_cash,
                    available_cash_for_trading=initial_cash,
                    transaction_limit_pct=0.50,  # Increased to 50% for testing
                    safe_net=100.0,  # Reduced safe net for testing
                    stop_loss_pct=0.12,
                    stop_gain_pct=0.20
                )
            else:
                default_settings = PortfolioSettings(
                    initial_cash=initial_cash,
                    max_position_size=0.10,
                    max_positions=20,
                    cash_reserve_pct=0.10,
                    risk_level=RiskLevel.MODERATE,
                    rebalance_frequency="monthly",
                    cash_for_trading=initial_cash,
                    available_cash_for_trading=initial_cash,
                    transaction_limit_pct=0.50,  # Increased to 50% for testing
                    safe_net=100.0,  # Reduced safe net for testing
                    stop_loss_pct=0.15,
                    stop_gain_pct=0.25
                )
            
            # Convert enum to string for JSON serialization
            settings_dict = default_settings.__dict__.copy()
            settings_dict['risk_level'] = default_settings.risk_level.value
            
            portfolio_manager = get_portfolio_manager()
            # Create portfolio
            portfolio_id = portfolio_manager.db.create_portfolio(
                name=name,
                portfolio_type=portfolio_type_enum,
                initial_cash=initial_cash,
                settings=settings_dict
            )
            
            return jsonify({
                'success': True,
                'portfolio_id': portfolio_id,
                'message': f'Portfolio "{name}" created successfully'
            })
            
        except Exception as e:
            logging.error(f"Error creating portfolio: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

@portfolio_api.route('/portfolios/<int:portfolio_id>', methods=['GET'])
def get_portfolio(portfolio_id: int):
    """Get specific portfolio details."""
    try:
        portfolio_manager = get_portfolio_manager()
        portfolio = get_portfolio_manager().db.get_portfolio(portfolio_id)
        if not portfolio:
            return jsonify({
                'success': False,
                'error': 'Portfolio not found'
            }), 404
        
        # Calculate summary directly instead of relying on portfolio manager
        try:
            logging.info(f"Calculating summary for portfolio {portfolio_id}: {portfolio.name}")
            positions = get_portfolio_manager().db.get_portfolio_positions(portfolio_id)
            logging.info(f"Retrieved {len(positions)} positions for portfolio {portfolio_id}")
            
            positions_value = sum(pos.shares * pos.current_price for pos in positions)
            total_value = portfolio.current_cash + positions_value
            total_pnl = total_value - portfolio.initial_cash
            total_pnl_pct = (total_pnl / portfolio.initial_cash) * 100 if portfolio.initial_cash > 0 else 0
            
            summary = {
                'total_value': float(total_value),
                'total_pnl': float(total_pnl),
                'total_pnl_pct': float(total_pnl_pct),
                'positions_count': int(len(positions)),
                'cash': float(portfolio.current_cash),
                'positions_value': float(positions_value)
            }
            logging.info(f"Summary calculated successfully for portfolio {portfolio_id}: {summary}")
        except Exception as e:
            logging.error(f"Error calculating summary for portfolio {portfolio_id}: {e}")
            import traceback
            logging.error(traceback.format_exc())
            summary = {
                'total_value': 0,
                'total_pnl': 0,
                'total_pnl_pct': 0,
                'positions_count': 0,
                'cash': portfolio.current_cash,
                'positions_value': 0
            }
            
        # Get positions with calculated P&L from the portfolio manager
        positions = get_portfolio_manager().db.get_portfolio_positions(portfolio_id)
        # Calculate P&L for each position dynamically without modifying objects
            
        transactions = get_portfolio_manager().db.get_portfolio_transactions(portfolio_id, limit=50)
        
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
                'total_value': summary['total_value'] if summary else 0,
                'total_pnl': summary['total_pnl'] if summary else 0,
                'total_pnl_pct': summary['total_pnl_pct'] if summary else 0,
                'positions_count': summary['positions_count'] if summary else 0,
                'cash': summary['cash'] if summary else 0,
                'positions_value': summary['positions_value'] if summary else 0,
                'best_position': None,  # Not calculating best/worst positions for now
                'worst_position': None
            } if summary else None,
            'positions': [
                {
                    'id': pos.id,
                    'symbol': pos.symbol,
                    'shares': pos.shares,
                    'avg_price': pos.avg_price,
                    'current_price': pos.current_price,
                    'pnl': (pos.shares * pos.current_price) - (pos.shares * pos.avg_price),
                    'pnl_pct': ((pos.shares * pos.current_price) - (pos.shares * pos.avg_price)) / (pos.shares * pos.avg_price) * 100 if pos.shares * pos.avg_price > 0 else 0,
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
                    'pnl': 0,  # Transactions don't have P&L - they're just records
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
            # Get the specific error from the portfolio manager
            portfolio = get_portfolio_manager().db.get_portfolio(portfolio_id)
            if portfolio:
                # Load portfolio settings
                settings = portfolio.settings or {}
                available_cash = settings.get('available_cash_for_trading', portfolio.current_cash)
                cash_for_trading = settings.get('cash_for_trading', portfolio.initial_cash)
                transaction_limit_pct = settings.get('transaction_limit_pct', 0.02)
                safe_net = settings.get('safe_net', 1000.0)
                
                # Calculate total cost - use provided price or get from portfolio manager
                if price_float is not None:
                    total_cost = float(shares) * price_float
                else:
                    # Try to get the last traded price for error calculation
                    last_price = portfolio_manager._get_last_traded_price(symbol.upper())
                    total_cost = float(shares) * (last_price or 0)
                
                # Check various constraints
                if total_cost > available_cash:
                    return jsonify({
                        'success': False,
                        'error': f'Insufficient available cash for trading. Need ${total_cost:.2f}, have ${available_cash:.2f}'
                    }), 400
                elif total_cost > cash_for_trading * transaction_limit_pct:
                    return jsonify({
                        'success': False,
                        'error': f'Transaction exceeds {transaction_limit_pct*100:.1f}% limit. Cost: ${total_cost:.2f}, Limit: ${cash_for_trading * transaction_limit_pct:.2f}'
                    }), 400
                elif available_cash - total_cost < safe_net:
                    return jsonify({
                        'success': False,
                        'error': f'Transaction would violate safe net. Remaining: ${available_cash - total_cost:.2f}, Safe net: ${safe_net:.2f}'
                    }), 400
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Failed to buy stock - check position limits or other constraints'
                    }), 400
            else:
                return jsonify({
                    'success': False,
                    'error': 'Portfolio not found'
                }), 404
        
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
        
        performance_history = get_portfolio_manager().db.get_portfolio_performance_history(
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
        
        transactions = get_portfolio_manager().db.get_portfolio_transactions(
            portfolio_id=portfolio_id,
            limit=limit
        )
        
        # Get current prices for all symbols in transactions
        symbols = list(set(trans.symbol for trans in transactions))
        current_prices = {}
        
        if symbols:
            try:
                positions = get_portfolio_manager().db.get_portfolio_positions(portfolio_id)
                for pos in positions:
                    if pos.symbol in symbols:
                        current_prices[pos.symbol] = pos.current_price
            except Exception as e:
                logging.warning(f"Could not fetch current prices: {e}")
        
        return jsonify({
            'success': True,
            'transactions': [
                {
                    'id': trans.id,
                    'symbol': trans.symbol,
                    'type': trans.transaction_type.value,
                    'shares': trans.shares,
                    'price': trans.price,
                    'current_price': current_prices.get(trans.symbol, None),
                    'total_amount': trans.total_amount,
                    'pnl': trans.pnl if hasattr(trans, 'pnl') and trans.pnl is not None else 0,
                    'pnl_pct': trans.pnl_percentage if hasattr(trans, 'pnl_percentage') and trans.pnl_percentage is not None else 0,
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
        positions = get_portfolio_manager().db.get_portfolio_positions(portfolio_id)
        
        return jsonify({
            'success': True,
            'positions': [
                {
                    'id': pos.id,
                    'symbol': pos.symbol,
                    'shares': pos.shares,
                    'avg_price': pos.avg_price,
                    'current_price': pos.current_price,
                    'pnl': (pos.shares * pos.current_price) - (pos.shares * pos.avg_price),
                    'pnl_pct': ((pos.shares * pos.current_price) - (pos.shares * pos.avg_price)) / (pos.shares * pos.avg_price) * 100 if pos.shares * pos.avg_price > 0 else 0,
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

@portfolio_api.route('/portfolios/<int:portfolio_id>/settings', methods=['PUT'])
def update_portfolio_settings(portfolio_id: int):
    """Update portfolio settings and optionally current cash."""
    try:
        data = request.get_json() or {}
        
        portfolio = get_portfolio_manager().db.get_portfolio(portfolio_id)
        if not portfolio:
            return jsonify({'success': False, 'error': 'Portfolio not found'}), 404
        
        # Extract top-level fields
        current_cash = data.pop('current_cash', None)
        available_cash = data.pop('available_cash', None)
        
        # Merge into settings dict (flat keys)
        current_settings = portfolio.settings.copy() if portfolio.settings else {}
        for key, value in data.items():
            current_settings[key] = value
        
        # Persist
        with sqlite3.connect(portfolio_manager.db.db_path) as conn:
            cursor = conn.cursor()
            
            # If available_cash is provided, update both current_cash and settings
            if available_cash is not None:
                cursor.execute(
                    """
                    UPDATE portfolios
                    SET current_cash = ?, settings = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (float(available_cash), json.dumps(current_settings), portfolio_id),
                )
            elif current_cash is not None:
                cursor.execute(
                    """
                    UPDATE portfolios
                    SET current_cash = ?, settings = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (float(current_cash), json.dumps(current_settings), portfolio_id),
                )
            else:
                cursor.execute(
                    """
                    UPDATE portfolios
                    SET settings = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (json.dumps(current_settings), portfolio_id),
                )
            conn.commit()
        
        return jsonify({'success': True, 'settings': current_settings})
    except Exception as e:
        logging.error(f"Error updating portfolio settings: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500 