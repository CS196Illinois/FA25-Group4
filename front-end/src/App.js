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
    { id: 1, text: 'Welcome to TradeWise! 👋\n\nEnter any company name to get a comprehensive investment analysis including:\n• AI-powered sentiment scoring (1-9 scale)\n• Key investment insights\n• Important quotes from recent news\n• Analysis of full article content\n\nTip: Use "Light" mode for short-term trading, "Detailed" for long-term investing.', sender: 'bot' },
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
      const response = await fetch('http://localhost:5001/api/analysis/query', {
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

  // Comprehensive analysis for the company
  const analyzeSentiment = async (company) => {
    try {
      // Show loading message
      const loadingMessage = {
        id: Date.now() + 1,
        text: `🔍 Analyzing ${company}...\n\nThis may take 30-60 seconds as we:\n• Resolve company ticker\n• Fetch news from multiple sources\n• Verify relevance with AI\n• Fetch full article content\n• Extract key quotes\n• Generate investment summary`,
        sender: 'bot',
      };
      setMessages(prevMessages => [...prevMessages, loadingMessage]);

      // Map detail level to goal
      const goal = detailLevel === 'detailed' ? 'long-term' : 'short-term';

      const response = await fetch('http://localhost:5001/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          company_name: company,
          goal: goal
        })
      });

      if (response.ok) {
        const data = await response.json();

        if (data.success) {
          // Format the comprehensive response
          let analysisText = `📊 Investment Analysis: ${data.company} (${data.ticker})\n\n`;
          analysisText += `━━━━━━━━━━━━━━━━━━━━━\n`;
          analysisText += `🎯 Investment Sentiment: ${data.stance}\n`;
          analysisText += `📈 Score: ${data.score}/9 ${getScoreEmoji(data.score)}\n`;
          if (data.reason) {
            analysisText += `💡 ${data.reason}\n`;
          }
          analysisText += `━━━━━━━━━━━━━━━━━━━━━\n\n`;

          // Add bullets
          if (data.bullets && data.bullets.length > 0) {
            analysisText += `📌 Key Points:\n`;
            data.bullets.forEach(bullet => {
              analysisText += `  • ${bullet}\n`;
            });
            analysisText += `\n`;
          }

          // Add long summary
          if (data.long_summary) {
            analysisText += `📝 Summary:\n${data.long_summary}\n\n`;
          }

          // Add top quotes
          if (data.quotes && data.quotes.length > 0) {
            analysisText += `💬 Key Quotes (Top ${Math.min(3, data.quotes.length)}):\n`;
            data.quotes.slice(0, 3).forEach((quote, idx) => {
              const weight = (quote.weight * 10).toFixed(1);
              analysisText += `  ${idx + 1}. [${weight}/10] "${quote.quote}"\n`;
              analysisText += `     — ${quote.speaker}\n`;
              if (quote.context) {
                analysisText += `     Why: ${quote.context}\n`;
              }
            });
            analysisText += `\n`;
          }

          // Add headline count
          if (data.headlines && data.headlines.length > 0) {
            analysisText += `📰 Analyzed ${data.articles_analyzed} full articles from ${data.headlines.length} headlines\n`;
          }

          const botReply = {
            id: Date.now() + 2,
            text: analysisText,
            sender: 'bot',
          };

          setMessages(prevMessages => [...prevMessages.slice(0, -1), botReply]);
        } else {
          const botReply = {
            id: Date.now() + 2,
            text: `❌ Analysis failed: ${data.error}`,
            sender: 'bot',
          };
          setMessages(prevMessages => [...prevMessages.slice(0, -1), botReply]);
        }
      } else {
        const botReply = {
          id: Date.now() + 2,
          text: `❌ Analysis service currently unavailable. Please try again later.`,
          sender: 'bot',
        };
        setMessages(prevMessages => [...prevMessages.slice(0, -1), botReply]);
      }
    } catch (error) {
      console.error('Error analyzing:', error);
      const botReply = {
        id: Date.now() + 2,
        text: `❌ Unable to analyze at this time. Please ensure the backend server is running.`,
        sender: 'bot',
      };
      setMessages(prevMessages => [...prevMessages.slice(0, -1), botReply]);
    }
  };

  // Helper function to get emoji based on score
  const getScoreEmoji = (score) => {
    if (score >= 7) return '🚀';
    if (score >= 5) return '😐';
    return '⚠️';
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

