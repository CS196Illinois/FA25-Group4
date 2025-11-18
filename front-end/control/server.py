"""
Flask Backend Server for TradeWise
Handles preferences API and serves the React frontend
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pathlib import Path
import os

# Import the preferences modules
from preferences_manager import PreferencesManager
from preferences_api import preferences_bp

# Initialize Flask app
app = Flask(__name__, static_folder='front-end/build', static_url_path='')

# Enable CORS for all routes (allows React frontend to call backend)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialize preferences manager
prefs_manager = PreferencesManager(preferences_dir='user_preferences')

# Register the preferences API blueprint
app.register_blueprint(preferences_bp)


# ============================================================================
# Routes
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify server is running"""
    return jsonify({'status': 'ok', 'message': 'Flask server is running'}), 200


@app.route('/api/preferences', methods=['POST'])
def save_preferences():
    """
    Save user preferences endpoint
    
    Expected JSON payload:
    {
        "user_id": "default_user",
        "riskTolerance": "medium",
        "totalInvestment": 50000,
        "targetedReturns": 8.5,
        "areasInterested": ["Technology", "Healthcare"]
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Extract user_id (default to 'default_user' if not provided)
        user_id = data.get('user_id', 'default_user')
        
        # Prepare preferences dict (remove user_id to avoid duplication)
        preferences = {
            'riskTolerance': data.get('riskTolerance'),
            'totalInvestment': data.get('totalInvestment'),
            'targetedReturns': data.get('targetedReturns'),
            'areasInterested': data.get('areasInterested', [])
        }
        
        # Validate required fields
        if not all(v is not None for v in preferences.values()):
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields'
            }), 400
        
        # Save preferences using the manager
        success = prefs_manager.save_preferences(user_id, preferences)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Preferences saved successfully',
                'user_id': user_id,
                'file_path': f'user_preferences/{user_id}_preferences.json'
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


@app.route('/api/preferences/<user_id>', methods=['GET'])
def get_preferences(user_id):
    """
    Retrieve user preferences by user_id
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


@app.route('/api/sentiment', methods=['POST'])
def analyze_sentiment():
    """
    Placeholder for sentiment analysis endpoint
    This will integrate with HariniSentimentAnalysis.py
    """
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        # TODO: Integrate with HariniSentimentAnalysis.py
        return jsonify({
            'status': 'not_implemented',
            'message': 'Sentiment analysis endpoint pending integration'
        }), 501
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error analyzing sentiment: {str(e)}'
        }), 400


@app.route('/', methods=['GET'])
def serve_react():
    """Serve the React app (when built)"""
    return send_from_directory('front-end/build', 'index.html')


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Route not found'}), 404


@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("Starting TradeWise Flask Backend Server")
    print("=" * 60)
    print("Available Endpoints:")
    print("  - GET  /api/health                    (Health check)")
    print("  - POST /api/preferences               (Save preferences)")
    print("  - GET  /api/preferences/<user_id>    (Load preferences)")
    print("  - POST /api/sentiment                 (Sentiment analysis)")
    print("=" * 60)
    print("Server running on: http://localhost:5000")
    print("React Frontend: http://localhost:3000")
    print("=" * 60)
    
    app.run(debug=True, port=5000, host='0.0.0.0')
