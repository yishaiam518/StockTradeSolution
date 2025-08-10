from flask import Blueprint, request, jsonify
from src.utils.config_loader import config as global_config

scheduler_api = Blueprint('scheduler_api', __name__)

@scheduler_api.route('/data-collection/scheduler/window', methods=['GET', 'PUT'])
def scheduler_window():
    if request.method == 'GET':
        try:
            # Get current settings from config
            cfg = global_config.config
            dc = cfg.get('data_collection', {})
            window = dc.get('scheduler_window', {})
            return jsonify({
                'success': True, 
                'settings': {
                    'start': window.get('start', '09:30'),
                    'end': window.get('end', '16:00'),
                    'weekdays': window.get('weekdays', [1,2,3,4,5])
                }
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    else:  # PUT method
        try:
            data = request.get_json() or {}
            start = data.get('start', '09:30')
            end = data.get('end', '16:00')
            weekdays = data.get('weekdays', [1,2,3,4,5])
            # Update in-memory config
            cfg = global_config.config
            dc = cfg.setdefault('data_collection', {})
            window = dc.setdefault('scheduler_window', {})
            window['enabled'] = True
            window['start'] = start
            window['end'] = end
            window['weekdays'] = weekdays
            # No file write to keep simple; takes effect next scheduler instantiation
            return jsonify({'success': True, 'window': window})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500