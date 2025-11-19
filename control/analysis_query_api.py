"""
Flask API for handling analysis queries (company names + detail level)
"""

from flask import Blueprint, request, jsonify
from analysis_query_manager import AnalysisQueryManager

# Create a Flask blueprint for analysis routes
analysis_bp = Blueprint('analysis', __name__, url_prefix='/api')

# Initialize the query manager
query_manager = AnalysisQueryManager()


@analysis_bp.route('/analysis/query', methods=['POST'])
def save_analysis_query():
    """
    Save an analysis query (company name + detail level)
    
    Request JSON:
    {
        "company_name": "Apple Inc.",
        "detail_level": "detailed"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        company_name = data.get('company_name', '').strip()
        detail_level = data.get('detail_level', 'light')
        
        if not company_name:
            return jsonify({'error': 'Company name is required'}), 400
        
        if detail_level not in ['light', 'detailed']:
            return jsonify({'error': 'Detail level must be "light" or "detailed"'}), 400
        
        # Save the query
        success = query_manager.save_query(company_name, detail_level)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Query saved successfully',
                'company_name': company_name,
                'detail_level': detail_level
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to save query'
            }), 500
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error: {str(e)}'
        }), 400


@analysis_bp.route('/analysis/queries', methods=['GET'])
def get_all_queries():
    """
    Get all saved analysis queries
    """
    try:
        queries = query_manager.get_all_queries()
        
        return jsonify({
            'status': 'success',
            'queries': queries,
            'count': len(queries)
        }), 200
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error retrieving queries: {str(e)}'
        }), 400


@analysis_bp.route('/analysis/queries/latest', methods=['GET'])
def get_latest_query():
    """
    Get the most recent analysis query
    """
    try:
        latest = query_manager.get_latest_query()
        
        if latest:
            return jsonify({
                'status': 'success',
                'query': latest
            }), 200
        else:
            return jsonify({
                'status': 'no_queries',
                'message': 'No queries found'
            }), 404
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error retrieving latest query: {str(e)}'
        }), 400


@analysis_bp.route('/analysis/queries', methods=['DELETE'])
def clear_all_queries():
    """
    Clear all saved analysis queries
    """
    try:
        success = query_manager.clear_queries()
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'All queries cleared'
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to clear queries'
            }), 500
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error: {str(e)}'
        }), 400


# Example of how to register this blueprint in your main Flask app:
# 
# from flask import Flask
# from analysis_query_api import analysis_bp
# 
# app = Flask(__name__)
# app.register_blueprint(analysis_bp)
