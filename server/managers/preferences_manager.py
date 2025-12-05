"""
Preferences Management Module
Handles saving and loading user preferences to/from JSON files
"""

import json
import os
from datetime import datetime
from pathlib import Path


class PreferencesManager:
    """Manages user preferences storage and retrieval"""
    
    def __init__(self, preferences_dir='../data/preferences'):
        """
        Initialize the preferences manager
        
        Args:
            preferences_dir (str): Directory to store preference JSON files
        """
        self.preferences_dir = Path(preferences_dir)
        self.preferences_dir.mkdir(exist_ok=True)
    
    def save_preferences(self, user_id, preferences):
        """
        Save user preferences to a JSON file
        
        Args:
            user_id (str): Unique identifier for the user
            preferences (dict): Dictionary containing user preferences
                {
                    'riskTolerance': str,
                    'totalInvestment': float,
                    'targetedReturns': float,
                    'areasInterested': list
                }
        
        Returns:
            bool: True if save was successful, False otherwise
        """
        try:
            # Validate preferences structure
            required_fields = ['riskTolerance', 'totalInvestment', 'targetedReturns', 'areasInterested']
            if not all(field in preferences for field in required_fields):
                raise ValueError(f"Missing required fields. Expected: {required_fields}")
            
            # Add metadata
            preferences_with_metadata = {
                'timestamp': datetime.now().isoformat(),
                'user_id': user_id,
                **preferences
            }
            
            # Create file path
            file_path = self.preferences_dir / f'{user_id}_preferences.json'
            
            # Save to JSON file
            with open(file_path, 'w') as f:
                json.dump(preferences_with_metadata, f, indent=2)
            
            print(f"Preferences saved successfully to {file_path}")
            return True
        
        except Exception as e:
            print(f"Error saving preferences: {str(e)}")
            return False
    
    def load_preferences(self, user_id):
        """
        Load user preferences from JSON file
        
        Args:
            user_id (str): Unique identifier for the user
        
        Returns:
            dict: User preferences, or None if file doesn't exist
        """
        try:
            file_path = self.preferences_dir / f'{user_id}_preferences.json'
            
            if not file_path.exists():
                print(f"No preferences file found for user {user_id}")
                return None
            
            with open(file_path, 'r') as f:
                preferences = json.load(f)
            
            return preferences
        
        except Exception as e:
            print(f"Error loading preferences: {str(e)}")
            return None
    
    def delete_preferences(self, user_id):
        """
        Delete user preferences file
        
        Args:
            user_id (str): Unique identifier for the user
        
        Returns:
            bool: True if delete was successful, False otherwise
        """
        try:
            file_path = self.preferences_dir / f'{user_id}_preferences.json'
            
            if file_path.exists():
                file_path.unlink()
                print(f"Preferences deleted for user {user_id}")
                return True
            else:
                print(f"No preferences file found for user {user_id}")
                return False
        
        except Exception as e:
            print(f"Error deleting preferences: {str(e)}")
            return False
    
    def list_all_preferences(self):
        """
        List all preference files
        
        Returns:
            list: List of user_ids with saved preferences
        """
        try:
            preference_files = list(self.preferences_dir.glob('*_preferences.json'))
            user_ids = [f.stem.replace('_preferences', '') for f in preference_files]
            return user_ids
        
        except Exception as e:
            print(f"Error listing preferences: {str(e)}")
            return []


# Example usage
if __name__ == "__main__":
    manager = PreferencesManager()
    
    # Example: Save preferences
    sample_preferences = {
        'riskTolerance': 'medium',
        'totalInvestment': 50000,
        'targetedReturns': 8.5,
        'areasInterested': ['Technology', 'Healthcare', 'Finance']
    }
    
    manager.save_preferences('user_001', sample_preferences)
    
    # Example: Load preferences
    loaded_prefs = manager.load_preferences('user_001')
    print("Loaded preferences:", json.dumps(loaded_prefs, indent=2))
    
    # Example: List all preferences
    all_users = manager.list_all_preferences()
    print("All users with preferences:", all_users)
