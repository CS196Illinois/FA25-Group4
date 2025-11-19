"""
Analysis Query Manager
Handles storage and retrieval of analysis queries (company names + detail level)
"""

import json
from datetime import datetime
from pathlib import Path


class AnalysisQueryManager:
    """Manages analysis query storage"""
    
    def __init__(self, queries_dir='./analysis_queries'):
        """
        Initialize the query manager
        
        Args:
            queries_dir (str): Directory to store query JSON files
        """
        self.queries_dir = Path(queries_dir)
        self.queries_dir.mkdir(exist_ok=True)
        self.queries_file = self.queries_dir / 'queries.json'
    
    def save_query(self, company_name, detail_level):
        """
        Save an analysis query
        
        Args:
            company_name (str): Name of the company to analyze
            detail_level (str): 'light' or 'detailed'
        
        Returns:
            bool: True if successful
        """
        try:
            # Validate inputs
            if not company_name or not isinstance(company_name, str):
                raise ValueError("Company name must be a non-empty string")
            
            if detail_level not in ['light', 'detailed']:
                raise ValueError("Detail level must be 'light' or 'detailed'")
            
            # Load existing queries
            queries = []
            if self.queries_file.exists():
                with open(self.queries_file, 'r') as f:
                    queries = json.load(f)
            
            # Create new query entry
            query_entry = {
                'timestamp': datetime.now().isoformat(),
                'company_name': company_name.strip(),
                'detail_level': detail_level
            }
            
            # Add to list
            queries.append(query_entry)
            
            # Save to file
            with open(self.queries_file, 'w') as f:
                json.dump(queries, f, indent=2)
            
            print(f"Query saved: {company_name} ({detail_level})")
            return True
        
        except Exception as e:
            print(f"Error saving query: {str(e)}")
            return False
    
    def get_all_queries(self):
        """
        Get all saved queries
        
        Returns:
            list: List of query dictionaries
        """
        try:
            if self.queries_file.exists():
                with open(self.queries_file, 'r') as f:
                    return json.load(f)
            return []
        
        except Exception as e:
            print(f"Error loading queries: {str(e)}")
            return []
    
    def get_latest_query(self):
        """
        Get the most recent query
        
        Returns:
            dict: Latest query or None
        """
        queries = self.get_all_queries()
        return queries[-1] if queries else None
    
    def clear_queries(self):
        """Clear all saved queries"""
        try:
            if self.queries_file.exists():
                self.queries_file.unlink()
            return True
        except Exception as e:
            print(f"Error clearing queries: {str(e)}")
            return False


# Example usage
if __name__ == "__main__":
    manager = AnalysisQueryManager()
    
    # Save some queries
    manager.save_query('Apple Inc.', 'detailed')
    manager.save_query('Tesla Inc.', 'light')
    manager.save_query('Microsoft Corporation', 'detailed')
    
    # Get all queries
    all_queries = manager.get_all_queries()
    print("All queries:")
    print(json.dumps(all_queries, indent=2))
    
    # Get latest
    latest = manager.get_latest_query()
    print("\nLatest query:")
    print(json.dumps(latest, indent=2))
