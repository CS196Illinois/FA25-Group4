import React, { useState, useEffect } from 'react';
import './PreferencesPanel.css';

const PreferencesPanel = () => {
  const [preferences, setPreferences] = useState({
    riskTolerance: 'medium',
    totalInvestment: '',
    targetedReturns: '',
    areasInterested: []
  });

  const [savedMessage, setSavedMessage] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  // Risk tolerance options
  const riskOptions = ['low', 'medium', 'high'];

  // Areas of interest options
  const areaOptions = [
    'Technology',
    'Healthcare',
    'Finance',
    'Energy',
    'Consumer',
    'Industrial',
    'Real Estate',
    'Utilities'
  ];

  // Load preferences from localStorage on component mount
  useEffect(() => {
    const loadPreferences = async () => {
      try {
        // Try to load from localStorage first
        const savedPrefs = localStorage.getItem('userPreferences');
        if (savedPrefs) {
          setPreferences(JSON.parse(savedPrefs));
        }
      } catch (error) {
        console.error('Error loading preferences:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadPreferences();
  }, []);

  // Handle input changes for text fields
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setPreferences(prev => ({
      ...prev,
      [name]: value
    }));
    setSavedMessage('');
  };

  // Handle risk tolerance selection
  const handleRiskChange = (risk) => {
    setPreferences(prev => ({
      ...prev,
      riskTolerance: risk
    }));
    setSavedMessage('');
  };

  // Handle areas of interest checkbox
  const handleAreaToggle = (area) => {
    setPreferences(prev => ({
      ...prev,
      areasInterested: prev.areasInterested.includes(area)
        ? prev.areasInterested.filter(a => a !== area)
        : [...prev.areasInterested, area]
    }));
    setSavedMessage('');
  };

  // Save preferences to localStorage and JSON file
  const handleSave = async () => {
    try {
      // Save to localStorage
      localStorage.setItem('userPreferences', JSON.stringify(preferences));

      // Prepare data to send to backend
      const dataToSend = {
        user_id: 'default_user', // You can change this to actual user ID
        ...preferences
      };

      // Try to save to backend (if available)
      try {
        const response = await fetch('http://localhost:5000/api/preferences', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(dataToSend)
        });

        const responseData = await response.json();

        if (response.ok) {
          console.log('Backend response:', responseData);
          setSavedMessage('✓ Preferences saved successfully to backend!');
        } else {
          console.error('Backend error:', responseData);
          setSavedMessage('✓ Saved to browser (backend unavailable)');
        }
      } catch (error) {
        // If backend not available, just save to localStorage
        console.log('Backend not available, saved to browser storage only');
        setSavedMessage('✓ Saved to browser (backend unavailable)');
      }

      setTimeout(() => setSavedMessage(''), 3000);
    } catch (error) {
      console.error('Error saving preferences:', error);
      setSavedMessage('✗ Error saving preferences');
    }
  };

  // Reset preferences to defaults
  const handleReset = () => {
    setPreferences({
      riskTolerance: 'medium',
      totalInvestment: '',
      targetedReturns: '',
      areasInterested: []
    });
    setSavedMessage('');
  };

  if (isLoading) {
    return <div className="preferences-panel"><p>Loading preferences...</p></div>;
  }

  return (
    <div className="preferences-panel">
      <h3>YOUR PREFERENCES</h3>
      
      <div className="preference-section">
        <label className="section-title">Risk Tolerance</label>
        <div className="radio-group">
          {riskOptions.map(option => (
            <label key={option} className="radio-label">
              <input
                type="radio"
                name="riskTolerance"
                value={option}
                checked={preferences.riskTolerance === option}
                onChange={() => handleRiskChange(option)}
              />
              <span className="radio-text">{option.charAt(0).toUpperCase() + option.slice(1)}</span>
            </label>
          ))}
        </div>
      </div>

      <div className="preference-section">
        <label className="section-title">Total Investment</label>
        <input
          type="number"
          name="totalInvestment"
          placeholder="Enter amount ($)"
          value={preferences.totalInvestment}
          onChange={handleInputChange}
          min="0"
          step="100"
          className="input-field"
        />
      </div>

      <div className="preference-section">
        <label className="section-title">Targeted Returns (%)</label>
        <input
          type="number"
          name="targetedReturns"
          placeholder="Enter target return percentage"
          value={preferences.targetedReturns}
          onChange={handleInputChange}
          min="0"
          max="100"
          step="0.1"
          className="input-field"
        />
      </div>

      <div className="preference-section">
        <label className="section-title">Areas Interested</label>
        <div className="checkbox-group">
          {areaOptions.map(area => (
            <label key={area} className="checkbox-label">
              <input
                type="checkbox"
                value={area}
                checked={preferences.areasInterested.includes(area)}
                onChange={() => handleAreaToggle(area)}
              />
              <span className="checkbox-text">{area}</span>
            </label>
          ))}
        </div>
      </div>

      <div className="button-group">
        <button className="save-btn" onClick={handleSave}>Save Preferences</button>
        <button className="reset-btn" onClick={handleReset}>Reset</button>
      </div>

      {savedMessage && (
        <div className={`message ${savedMessage.startsWith('✓') ? 'success' : 'error'}`}>
          {savedMessage}
        </div>
      )}
    </div>
  );
};

export default PreferencesPanel;
