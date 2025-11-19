import React, { useState } from 'react';
import './App.css';
import logo from './tradewise-logo.png';
import PreferencesPanel from './PreferencesPanel';

const MainContent = () => {
  return (
    <div className="main-content-layout1">
      <div className="left-panel">
        <h3>Trading Insight Today</h3>
        <p>BLAHBLAHBLAH</p>
        <div className="insight-card">
          <span className="arrow-up">↑</span>
          <h4>Stock Picks For You</h4>
          <p>BLAHBLAHBLAH</p>
        </div>
      </div>
      <PreferencesPanel />
    </div>
  );
};

const ChatContent = () => {
  // State to hold all messages
  const [messages, setMessages] = useState([
    { id: 1, text: 'Welcome! Enter a company name to analyze sentiment.', sender: 'bot' },
  ]);
  // State for company name input
  const [companyName, setCompanyName] = useState('');
  // State for detail level (light or detailed)
  const [detailLevel, setDetailLevel] = useState('light');
  // State for error messages
  const [inputError, setInputError] = useState('');

  // Validate company name (only letters, numbers, and common symbols)
  const isValidCompanyName = (name) => {
    const trimmed = name.trim();
    // Allow letters, numbers, spaces, hyphens, periods, and ampersands
    return /^[a-zA-Z0-9\s\-\.&]{1,100}$/.test(trimmed) && trimmed.length > 0;
  };

  // Function to handle sending a message
  const handleSend = () => {
    setInputError('');

    // Validate company name
    if (!isValidCompanyName(companyName)) {
      setInputError('Please enter a valid company name (letters, numbers, hyphens, periods only)');
      return;
    }

    const companyNameTrimmed = companyName.trim();

    // Create user message
    const newUserMessage = {
      id: Date.now(),
      text: `Analyze ${companyNameTrimmed} (${detailLevel} mode)`,
      sender: 'user',
    };

    // Add user message to the list
    setMessages(prevMessages => [...prevMessages, newUserMessage]);

    // Save query to backend
    saveAnalysisQuery(companyNameTrimmed, detailLevel);

    // Analyze sentiment with company name
    analyzeSentiment(companyNameTrimmed);

    // Clear inputs
    setCompanyName('');
  };

  // Save analysis query to backend
  const saveAnalysisQuery = async (company, detail) => {
    try {
      const response = await fetch('http://localhost:5000/api/analysis/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          company_name: company,
          detail_level: detail
        })
      });

      if (response.ok) {
        console.log('Query saved to server');
      } else {
        console.log('Query saved locally (server unavailable)');
      }
    } catch (error) {
      console.log('Server not available, query saved in session');
    }
  };

  // Analyze sentiment for the company
  const analyzeSentiment = async (company) => {
    try {
      const response = await fetch('http://localhost:5000/api/sentiment', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          company_name: company,
          text: company
        })
      });

      if (response.ok) {
        const data = await response.json();
        
        // Create bot response with sentiment analysis
        const botReply = {
          id: Date.now() + 1,
          text: `📊 ${data.company_name} Sentiment Analysis:\n\nSentiment: ${data.sentiment_label}\nScore: ${data.sentiment_score.toFixed(4)}`,
          sender: 'bot',
        };
        
        setMessages(prevMessages => [...prevMessages, botReply]);
      } else {
        // Fallback if sentiment analysis fails
        const botReply = {
          id: Date.now() + 1,
          text: `Sentiment analysis service currently unavailable.`,
          sender: 'bot',
        };
        setMessages(prevMessages => [...prevMessages, botReply]);
      }
    } catch (error) {
      console.error('Error analyzing sentiment:', error);
      // Fallback if there's a network error
      const botReply = {
        id: Date.now() + 1,
        text: `Unable to analyze sentiment at this time. Please ensure the backend server is running.`,
        sender: 'bot',
      };
      setMessages(prevMessages => [...prevMessages, botReply]);
    }
  };

  // Allow sending with the "Enter" key
  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSend();
    }
  };

  return (
    <div className="main-content-layout2">
      <div className="chat-interface">
        <div className="message-list">
          {messages.map(message => (
            <div
              key={message.id}
              className={`chat-bubble ${message.sender === 'user' ? 'user' : 'bot'}`}
            >
              {message.text}
            </div>
          ))}
        </div>

        <div className="chat-input-area">
          <div className="input-controls">
            <input 
              type="text" 
              placeholder="Enter company name..." 
              value={companyName}
              onChange={(e) => {
                setCompanyName(e.target.value);
                setInputError('');
              }}
              onKeyPress={handleKeyPress}
              className={inputError ? 'input-error' : ''}
            />
            
            <div className="detail-toggle">
              <label className="toggle-label">
                <span className={detailLevel === 'light' ? 'active' : ''}>Light</span>
                <input
                  type="checkbox"
                  checked={detailLevel === 'detailed'}
                  onChange={(e) => setDetailLevel(e.target.checked ? 'detailed' : 'light')}
                  className="toggle-checkbox"
                />
                <span className={detailLevel === 'detailed' ? 'active' : ''}>Detailed</span>
              </label>
            </div>

            <button className="search-icon" onClick={handleSend}>🔍</button>
          </div>
          
          {inputError && <div className="error-message">{inputError}</div>}
        </div>
      </div>
    </div>
  );
};

function App() {
  // 'view' state can be 'main' or 'chat'
  const [currentView, setCurrentView] = useState('main'); // Default view

  return (
    <div className="App">

      <div className="layout-container">
        <div className="header">
          <img src={logo} alt="Tradewise Logo" className="logo" />
          <div className="nav-buttons">
            <button onClick={() => setCurrentView('main')}>Main</button>
            <button onClick={() => setCurrentView('chat')}>Chat</button>
            <button className="sign-in">Sign In</button>
            <button className="register">Register</button>
          </div>
        </div>

        {currentView === 'main' && <MainContent />}
        {currentView === 'chat' && <ChatContent />}
      </div>
    </div>
  );
}

export default App;

