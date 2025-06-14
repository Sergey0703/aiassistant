import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { Send, Trash2, FileText, Loader } from 'lucide-react';
import axios from 'axios';
import { Message, ChatMessage, ChatResponse, ChatHistory } from '../types/api';

const UserChat: React.FC = () => {
  const { t, i18n } = useTranslation();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = (): void => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    loadChatHistory();
  }, []);

  const loadChatHistory = async (): Promise<void> => {
    try {
      const response = await axios.get<ChatHistory>('/api/user/chat/history');
      if (response.data.history) {
        const formattedHistory: Message[] = response.data.history
          .map(item => [
            { 
              type: 'user' as const, 
              content: item.message,
              timestamp: new Date()
            },
            { 
              type: 'assistant' as const, 
              content: item.response, 
              sources: item.sources || [],
              timestamp: new Date()
            }
          ])
          .flat();
        setMessages(formattedHistory);
      }
    } catch (error) {
      console.error('Error loading chat history:', error);
    }
  };

  const sendMessage = async (): Promise<void> => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = inputMessage.trim();
    setInputMessage('');
    setError('');
    setIsLoading(true);

    // Add user message
    const newUserMessage: Message = {
      type: 'user',
      content: userMessage,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, newUserMessage]);

    try {
      const chatRequest: ChatMessage = {
        message: userMessage,
        language: i18n.language
      };

      const response = await axios.post<ChatResponse>('/api/user/chat', chatRequest);

      // Add assistant response
      const assistantMessage: Message = {
        type: 'assistant',
        content: response.data.response,
        sources: response.data.sources || [],
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);

    } catch (error) {
      console.error('Error sending message:', error);
      setError(t('chat.error'));
    } finally {
      setIsLoading(false);
    }
  };

  const clearChat = (): void => {
    setMessages([]);
    setError('');
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>): void => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-800">{t('chat.title')}</h1>
          <button
            onClick={clearChat}
            className="flex items-center space-x-2 px-3 py-2 text-sm text-red-600 hover:text-red-800 hover:bg-red-50 rounded-md transition-colors"
          >
            <Trash2 size={16} />
            <span>{t('chat.clear')}</span>
          </button>
        </div>
      </div>

      {/* Chat Messages */}
      <div className="bg-white rounded-lg shadow-sm mb-6">
        <div className="h-96 overflow-y-auto p-6 space-y-4 chat-messages">
          {messages.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              <p>{t('chat.empty')}</p>
            </div>
          ) : (
            messages.map((message, index) => (
              <div key={index} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                  message.type === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  <p className="whitespace-pre-wrap">{message.content}</p>
                  
                  {/* Sources */}
                  {message.sources && message.sources.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-gray-300">
                      <div className="flex items-center space-x-1 text-xs text-gray-600">
                        <FileText size={12} />
                        <span>{t('chat.sources')}:</span>
                      </div>
                      <ul className="mt-1 text-xs text-gray-600">
                        {message.sources.map((source, idx) => (
                          <li key={idx} className="truncate">• {source}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
          
          {/* Loading indicator */}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 text-gray-800 max-w-xs lg:max-w-md px-4 py-2 rounded-lg">
                <div className="flex items-center space-x-2">
                  <Loader className="animate-spin" size={16} />
                  <span>{t('chat.thinking')}</span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Error Message */}
        {error && (
          <div className="px-6 pb-4">
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          </div>
        )}

        {/* Input Area */}
        <div className="border-t p-4">
          <div className="flex space-x-4">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={t('chat.placeholder')}
              className="flex-1 resize-none border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={2}
              disabled={isLoading}
            />
            <button
              onClick={sendMessage}
              disabled={!inputMessage.trim() || isLoading}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              <Send size={16} />
              <span>{t('chat.send')}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserChat;