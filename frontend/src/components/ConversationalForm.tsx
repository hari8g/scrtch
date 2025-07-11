import React, { useState, useEffect, useRef } from 'react';
import { 
  startConversation, 
  continueConversation, 
  ConversationResponse,
  ConversationMessage
} from '../services/conversation_api';

interface ConversationalFormProps {
  onFormulationReady: (enhancedQuery: string) => void;
}

const ConversationalForm: React.FC<ConversationalFormProps> = ({ onFormulationReady }) => {
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [currentInput, setCurrentInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isConversationComplete, setIsConversationComplete] = useState(false);
  const [exchangeCount, setExchangeCount] = useState<number>(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'end',
        inline: 'nearest'
      });
    }
  };

  // Auto-scroll when messages change or loading state changes
  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Auto-scroll when conversation starts
  useEffect(() => {
    if (messages.length > 0) {
      scrollToBottom();
    }
  }, [messages.length]);

  const handleStartConversation = async (initialQuery: string) => {
    if (!initialQuery.trim()) return;

    setIsLoading(true);
    try {
      const response: ConversationResponse = await startConversation(initialQuery);
      
      setConversationId(response.conversation_id);
      setMessages(response.conversation_history);
      setExchangeCount(response.exchange_count || 1);
      
      if (response.ready_for_formulation) {
        setIsConversationComplete(true);
        onFormulationReady(response.enhanced_query || '');
      }
    } catch (error) {
      console.error('Error starting conversation:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleContinueConversation = async (userResponse: string) => {
    if (!userResponse.trim() || !conversationId) return;

    setIsLoading(true);
    try {
      const response: ConversationResponse = await continueConversation(
        conversationId,
        userResponse,
        messages
      );
      
      setMessages(response.conversation_history);
      setExchangeCount(response.exchange_count || exchangeCount + 1);
      
      if (response.ready_for_formulation) {
        setIsConversationComplete(true);
        onFormulationReady(response.enhanced_query || '');
      }
    } catch (error) {
      console.error('Error continuing conversation:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (isLoading || !currentInput.trim()) return;

    const userInput = currentInput.trim();
    setCurrentInput('');

    if (messages.length === 0) {
      // Starting a new conversation
      await handleStartConversation(userInput);
    } else {
      // Continuing the conversation
      await handleContinueConversation(userInput);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const getProgressMessage = () => {
    if (exchangeCount === 0) return '';
    if (exchangeCount >= 4) return 'Final exchange - completing formulation...';
    if (exchangeCount >= 3) return 'Almost there - one more question...';
    if (exchangeCount >= 2) return 'Great progress - gathering key details...';
    return 'Starting conversation...';
  };

  return (
    <div className="conversational-form">
      <div className="chat-container" ref={chatContainerRef}>
        {messages.length === 0 ? (
          <div className="welcome-message">
            <h3>Let's create your perfect formulation!</h3>
            <p>Tell me what you'd like to create, and I'll guide you through the process step by step.</p>
            <div className="exchange-limit-info">
              <p> I'll ask 3-4 focused questions to understand your needs perfectly.</p>
            </div>
          </div>
        ) : (
          <div className="messages">
            {messages.filter(m => m.role !== 'system').map((message, index) => (
              <div
                key={index}
                className={`message ${message.role === 'user' ? 'user-message' : 'assistant-message'}`}
              >
                <div className="message-content">
                  {message.content}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="message assistant-message">
                <div className="message-content">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
        
        {/* Progress indicator */}
        {messages.length > 0 && !isConversationComplete && (
          <div className="progress-indicator">
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${(exchangeCount / 4) * 100}%` }}
              ></div>
            </div>
            <div className="progress-text">
              <span className="exchange-count">Exchange {exchangeCount}/4</span>
              <span className="progress-message">{getProgressMessage()}</span>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {!isConversationComplete && (
        <form onSubmit={handleSubmit} className="input-form">
          <div className="input-container">
            <textarea
              value={currentInput}
              onChange={(e) => setCurrentInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={messages.length === 0 
                ? "Tell me what you'd like to create..." 
                : "Type your response..."
              }
              disabled={isLoading}
              rows={1}
              className="message-input"
            />
            <button 
              type="submit" 
              disabled={isLoading || !currentInput.trim()}
              className="send-button"
            >
              {isLoading ? '⏳' : '➤'}
            </button>
          </div>
        </form>
      )}
    </div>
  );
};

export default ConversationalForm; 