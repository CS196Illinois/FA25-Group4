"""
Flask Backend Server for TradeWise
Unified server using external manager classes and API blueprints
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sys
import os

# Add Product folder to path so we can import sentiment.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Product'))

from preferences_api import preferences_bp
from analysis_query_api import analysis_bp
from sentiment import get_sentiment_scores

# Initialize Flask app
app = Flask(__name__, static_folder='../build', static_url_path='')

# Enable CORS for all routes (allows React frontend to call backend)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Register blueprints
app.register_blueprint(preferences_bp)
app.register_blueprint(analysis_bp)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify server is running"""
    return jsonify({'status': 'ok', 'message': 'TradeWise server is running'}), 200


# ============================================================================
# Sentiment Analysis Routes
# ============================================================================

@app.route('/api/sentiment', methods=['POST'])
def analyze_sentiment():
    """
    Analyze sentiment for company news/text using HuggingFace transformers
    
    Request JSON:
    {
        "company_name": "Apple Inc.",
        "text": "Apple released a new iPhone with amazing features"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        company_name = data.get('company_name', '').strip()
        text = data.get('text', '').strip()
        
        if not company_name:
            return jsonify({'error': 'Company name is required'}), 400
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        # Get sentiment scores for the text
        scores = get_sentiment_scores([text])
        sentiment_score = scores[text]
        
        # Interpret the score
        if sentiment_score > 0.03:
            sentiment_label = 'Positive'
        elif sentiment_score < -0.03:
            sentiment_label = 'Negative'
        else:
            sentiment_label = 'Neutral'
        
        return jsonify({
            'status': 'success',
            'company_name': company_name,
            'text': text,
            'sentiment_score': sentiment_score,
            'sentiment_label': sentiment_label,
            'message': f'Sentiment analysis completed for {company_name}'
        }), 200
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error analyzing sentiment: {str(e)}'
        }), 500


@app.route('/', methods=['GET'])
def serve_react():
    """Serve the React app (when built)"""
    try:
        return send_from_directory('../build', 'index.html')
    except:
        return jsonify({'message': 'React app not yet built. Run: npm run build'}), 404


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
    print("=" * 70)
    print("Starting TradeWise Integrated Backend Server")
    print("=" * 70)
    print("\n📡 Available Endpoints:\n")
    print("Health Check:")
    print("  ✓ GET  /api/health")
    print("\nPreferences Management:")
    print("  ✓ POST   /api/preferences                  (Save preferences)")
    print("  ✓ GET    /api/preferences/<user_id>        (Load preferences)")
    print("  ✓ DELETE /api/preferences/<user_id>        (Delete preferences)")
    print("  ✓ GET    /api/preferences/list/all         (List all users)")
    print("\nAnalysis Queries:")
    print("  ✓ POST   /api/analysis/query               (Save query)")
    print("  ✓ GET    /api/analysis/queries             (Get all queries)")
    print("  ✓ GET    /api/analysis/queries/latest      (Get latest query)")
    print("  ✓ DELETE /api/analysis/queries             (Clear all queries)")
    print("\nSentiment Analysis:")
    print("  ✓ POST   /api/sentiment                    (Analyze sentiment for company news)")
    print("\n" + "=" * 70)
    print("🚀 Server running on: http://localhost:5000")
    print("🎨 React Frontend: http://localhost:3000")
    print("=" * 70)
    print("\nPress CTRL+C to stop the server\n")
    
    app.run(debug=True, port=5000, host='0.0.0.0')
