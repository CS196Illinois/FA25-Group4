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
    { id: 1, text: 'Welcome! How can I help you analyze stocks today?', sender: 'bot' },
    { id: 2, text: 'Help me analyze the best stock today', sender: 'user' },
    { id: 3, text: '*Serious analysis on this option* \n\n (This is a simulated response)', sender: 'bot' },
  ]);
  // State for the user's current typed message
  const [currentInput, setCurrentInput] = useState('');

  // Function to handle sending a message
  const handleSend = () => {
    if (currentInput.trim() === '') return; // Empty Message check

    const newUserMessage = {
      id: Date.now(),
      text: currentInput,
      sender: 'user',
    };

    // Add user message to the list
    setMessages(prevMessages => [...prevMessages, newUserMessage]);
    setCurrentInput(''); // Clear the input field

    // Reply message
    setTimeout(() => {
      const botReply = {
        id: Date.now() + 1,
        text: `I am processing your request about "${newUserMessage.text}". Please wait for a moment.`,
        sender: 'bot',
      };
      setMessages(prevMessages => [...prevMessages, botReply]);
    }, 1000);
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
          <input 
            type="text" 
            placeholder="Type your message..." 
            value={currentInput}
            onChange={(e) => setCurrentInput(e.target.value)}
            onKeyPress={handleKeyPress}
          />
          <button className="search-icon" onClick={handleSend}>🔍</button>
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

