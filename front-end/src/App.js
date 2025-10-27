import React, { useState } from 'react';
import './App.css';
import logo from './tradewise-logo.png';


// This component is JUST the content for the "Main" view
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
      <div className="right-panel">
        <h3>YOUR PREFERENCE</h3>
        <p>BLAHBLAHBLAH</p>
        <h4>Settings for preference</h4>
        <ul>
          <li>risk tolerance</li>
          <li>Total Investment</li>
          <li>High Returns</li>
          <li>Targeted Return</li>
        </ul>
      </div>
    </div>
  );
};

// This component is JUST the content for the "Chat" view
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
    if (currentInput.trim() === '') return; // Don't send empty messages

    const newUserMessage = {
      id: Date.now(),
      text: currentInput,
      sender: 'user',
    };

    // Add user message to the list
    setMessages(prevMessages => [...prevMessages, newUserMessage]);
    setCurrentInput(''); // Clear the input field

    // Simulate a bot reply after 1 second
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
      {/* The chat-interface is now the full content area, no more grid */}
      <div className="chat-interface">
        
        {/* This div will hold all the message bubbles */}
        <div className="message-list">
          {messages.map(message => (
            <div
              key={message.id}
              // Apply 'user' or 'bot' class for styling
              className={`chat-bubble ${message.sender === 'user' ? 'user' : 'bot'}`}
            >
              {message.text}
            </div>
          ))}
        </div>
        
        {/* The input area stays at the bottom */}
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
      {/* The recommendation-card is now removed */}
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

