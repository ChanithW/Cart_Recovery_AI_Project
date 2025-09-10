import React, { useState, useEffect, useRef } from 'react';
import './ChatWidget.css';

interface ChatMessage {
  type: string;
  message: string;
  timestamp: string;
  suggestions?: string[];
  offers?: any[];
  product_suggestions?: any[];
  cart_summary?: any;
  next_actions?: string[];
  recommendations?: any[];
}

interface ChatWidgetProps {
  sessionId: string;
  isLoggedIn?: boolean;
}

const ChatWidget: React.FC<ChatWidgetProps> = ({ sessionId }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const connectWebSocket = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    // For development, use localhost:8000 for WebSocket connection
    const wsUrl = `ws://localhost:8000/ws/chat/${sessionId}`;
    
    console.log('Connecting to WebSocket:', wsUrl);
    wsRef.current = new WebSocket(wsUrl);

    wsRef.current.onopen = () => {
      console.log('Chat WebSocket connected successfully');
      setIsConnected(true);
    };

    wsRef.current.onmessage = (event) => {
      try {
        console.log('Received WebSocket message:', event.data);
        const messageData = JSON.parse(event.data);
        setMessages(prev => [...prev, messageData]);
        setIsTyping(false);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    wsRef.current.onclose = (event) => {
      console.log('Chat WebSocket disconnected. Code:', event.code, 'Reason:', event.reason);
      setIsConnected(false);
      // Attempt to reconnect after 3 seconds
      setTimeout(() => {
        if (isOpen) {
          console.log('Attempting to reconnect...');
          connectWebSocket();
        }
      }, 3000);
    };

    wsRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsConnected(false);
    };
  };

  const disconnectWebSocket = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  };

  const sendMessage = () => {
    if (!inputMessage.trim() || !isConnected) return;

    // Add user message to chat
    const userMessage: ChatMessage = {
      type: 'user_message',
      message: inputMessage,
      timestamp: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setIsTyping(true);

    // Send to WebSocket
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const messagePayload = {
        type: 'user_message',
        message: inputMessage
      };
      console.log('Sending message:', messagePayload);
      wsRef.current.send(JSON.stringify(messagePayload));
    } else {
      console.error('WebSocket not connected, cannot send message');
      setIsTyping(false);
    }

    setInputMessage('');
  };

  const handleSuggestionClick = (suggestion: string) => {
    setInputMessage(suggestion);
    // Auto-send after a brief delay to update the input visually
    setTimeout(() => {
      if (suggestion.trim() && isConnected) {
        // Add user message to chat
        const userMessage: ChatMessage = {
          type: 'user_message',
          message: suggestion,
          timestamp: new Date().toISOString()
        };
        
        setMessages(prev => [...prev, userMessage]);
        setIsTyping(true);

        // Send to WebSocket
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          const messagePayload = {
            type: 'user_message',
            message: suggestion
          };
          console.log('Sending suggestion message:', messagePayload);
          wsRef.current.send(JSON.stringify(messagePayload));
        }
        
        setInputMessage('');
      }
    }, 100);
  };

  const toggleChat = () => {
    setIsOpen(!isOpen);
    if (!isOpen) {
      connectWebSocket();
    } else {
      disconnectWebSocket();
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const renderMessage = (msg: ChatMessage, index: number) => {
    const isUser = msg.type === 'user_message';
    
    return (
      <div key={index} className={`message ${isUser ? 'user' : 'assistant'}`}>
        <div className="message-content">
          <p>{msg.message}</p>
          
          {/* Render suggestions */}
          {msg.suggestions && msg.suggestions.length > 0 && (
            <div className="suggestions">
              {msg.suggestions.map((suggestion, idx) => (
                <button
                  key={idx}
                  className="suggestion-btn"
                  onClick={() => handleSuggestionClick(suggestion)}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          )}

          {/* Render offers */}
          {msg.offers && msg.offers.length > 0 && (
            <div className="offers">
              <h4>Available Offers:</h4>
              {msg.offers.map((offer, idx) => (
                <div key={idx} className="offer-card">
                  <strong>{offer.title}</strong>
                  <p>{offer.description}</p>
                  {offer.discount && <span className="discount">{offer.discount}</span>}
                </div>
              ))}
            </div>
          )}

          {/* Render product recommendations */}
          {msg.recommendations && msg.recommendations.length > 0 && (
            <div className="recommendations">
              <h4>Recommendations:</h4>
              {msg.recommendations.map((rec, idx) => (
                <div key={idx} className="recommendation-card">
                  <strong>{rec.name}</strong>
                  <p>{rec.reason}</p>
                  {rec.price_range && <span className="price">{rec.price_range}</span>}
                </div>
              ))}
            </div>
          )}

          {/* Render cart summary */}
          {msg.cart_summary && (
            <div className="cart-summary">
              <h4>Cart Summary:</h4>
              <p>Items: {msg.cart_summary.items?.length || 0}</p>
              <p>Total: ${msg.cart_summary.total_value?.toFixed(2) || '0.00'}</p>
            </div>
          )}
        </div>
        <div className="message-time">{formatTime(msg.timestamp)}</div>
      </div>
    );
  };

  return (
    <>
      {/* Chat Toggle Button */}
      <button 
        className={`chat-toggle ${isOpen ? 'open' : ''}`}
        onClick={toggleChat}
        aria-label="Toggle chat"
      >
        {isOpen ? (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        ) : (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="m3 21 1.9-5.7a8.5 8.5 0 1 1 3.8 3.8z"></path>
          </svg>
        )}
        {!isConnected && isOpen && <div className="connection-indicator offline"></div>}
        {isConnected && <div className="connection-indicator online"></div>}
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div className="chat-widget">
          <div className="chat-header">
            <h3>Shopping Assistant</h3>
            <div className="connection-status">
              {isConnected ? (
                <span className="status online">●</span>
              ) : (
                <span className="status offline">●</span>
              )}
            </div>
          </div>

          <div className="chat-messages">
            {messages.length === 0 && (
              <div className="welcome-message">
                <p>👋 Hi! I'm your shopping assistant. How can I help you today?</p>
                <div className="quick-actions">
                  <button onClick={() => handleSuggestionClick("Show recommendations")}>
                    Show recommendations
                  </button>
                  <button onClick={() => handleSuggestionClick("Check my cart")}>
                    Check my cart
                  </button>
                  <button onClick={() => handleSuggestionClick("Find deals")}>
                    Find deals
                  </button>
                </div>
              </div>
            )}
            
            {messages.map((msg, index) => renderMessage(msg, index))}
            
            {isTyping && (
              <div className="typing-indicator">
                <div className="typing-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
                <span>Assistant is typing...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="chat-input">
            <div className="input-container">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={isConnected ? "Type your message..." : "Connecting..."}
                disabled={!isConnected}
                rows={1}
              />
              <button 
                onClick={sendMessage}
                disabled={!inputMessage.trim() || !isConnected}
                className="send-btn"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="22" y1="2" x2="11" y2="13"></line>
                  <polygon points="22,2 15,22 11,13 2,9 22,2"></polygon>
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default ChatWidget;
