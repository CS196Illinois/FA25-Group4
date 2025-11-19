"""
Flask API for handling user preferences
This module provides REST endpoints for saving and retrieving user preferences
"""

from flask import Blueprint, request, jsonify
from preferences_manager import PreferencesManager

# Create a Flask blueprint for preferences routes
preferences_bp = Blueprint('preferences', __name__, url_prefix='/api')

# Initialize the preferences manager
prefs_manager = PreferencesManager()


@preferences_bp.route('/preferences', methods=['POST'])
def save_preferences():
    """
    Save user preferences
    
    Request JSON:
    {
        "user_id": "user_001",
        "riskTolerance": "medium",
        "totalInvestment": 50000,
        "targetedReturns": 8.5,
        "areasInterested": ["Technology", "Healthcare"]
    }
    """
    try:
        data = request.get_json()
        
        # Extract user_id, default to 'default_user' if not provided
        user_id = data.pop('user_id', 'default_user')
        
        # Save preferences
        success = prefs_manager.save_preferences(user_id, data)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Preferences saved successfully',
                'user_id': user_id
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to save preferences'
            }), 500
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error saving preferences: {str(e)}'
        }), 400


@preferences_bp.route('/preferences/<user_id>', methods=['GET'])
def get_preferences(user_id):
    """
    Get user preferences by user_id
    """
    try:
        preferences = prefs_manager.load_preferences(user_id)
        
        if preferences:
            return jsonify({
                'status': 'success',
                'data': preferences
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': f'No preferences found for user {user_id}'
            }), 404
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error retrieving preferences: {str(e)}'
        }), 400


@preferences_bp.route('/preferences/<user_id>', methods=['DELETE'])
def delete_preferences(user_id):
    """
    Delete user preferences
    """
    try:
        success = prefs_manager.delete_preferences(user_id)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f'Preferences deleted for user {user_id}'
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': f'No preferences found for user {user_id}'
            }), 404
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error deleting preferences: {str(e)}'
        }), 400


@preferences_bp.route('/preferences/list/all', methods=['GET'])
def list_all_preferences():
    """
    List all users with saved preferences
    """
    try:
        user_ids = prefs_manager.list_all_preferences()
        
        return jsonify({
            'status': 'success',
            'users': user_ids,
            'count': len(user_ids)
        }), 200
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error listing preferences: {str(e)}'
        }), 400


# Example of how to register this blueprint in your main Flask app:
# 
# from flask import Flask
# from preferences_api import preferences_bp
# 
# app = Flask(__name__)
# app.register_blueprint(preferences_bp)
