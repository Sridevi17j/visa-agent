'use client';

import { useState, useEffect, useRef } from 'react';
import { Send, RefreshCw, Paperclip } from 'lucide-react';
import { useVisaAgent } from '../lib/useVisaAgent';
import ChatMessage from './ChatMessage';
import TypingIndicator from './TypingIndicator';
import FileUpload from './FileUpload';

export default function ChatInterface() {
  const [input, setInput] = useState('');
  const [showFileUpload, setShowFileUpload] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Use the LangGraph SDK hook
  const { 
    messages, 
    sendMessage, 
    resetChat, 
    isLoading, 
    isInitialized,
    threadId,
    error 
  } = useVisaAgent();

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Use messages as-is, no welcome message
  const displayMessages = messages;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading || !isInitialized) return;

    sendMessage(input);
    setInput('');
  };

  const handleFileSelect = (file: File) => {
    // For demo purposes, we'll send the file name as a message
    // In production, you'd upload the file to a server first
    const filePath = `Uploaded: ${file.name}`;
    sendMessage(filePath);
    setShowFileUpload(false);
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-4 shadow-sm">
        <div className="flex items-center justify-between max-w-4xl mx-auto">
          <div>
            <h1 className="text-xl font-semibold text-gray-900">Veazy - AI Visa Assistant</h1>
            <p className="text-sm text-gray-600">
              Get help with your visa application
              {threadId && <span className="ml-2 text-xs text-gray-500">Thread: {threadId.slice(0, 8)}</span>}
            </p>
          </div>
          <button
            onClick={resetChat}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-full transition-colors"
            title="Start new conversation"
          >
            <RefreshCw className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 max-w-4xl mx-auto w-full">
          <p className="text-red-700 text-sm">
            Connection error: {error.message}. Make sure the LangGraph server is running on port 2024.
          </p>
        </div>
      )}

      {/* Loading State */}
      {!isInitialized && (
        <div className="flex items-center justify-center p-8">
          <div className="text-gray-500">Initializing chat...</div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="max-w-4xl mx-auto">
          {displayMessages.map((message, index) => (
            <ChatMessage key={message.id || index} message={message} />
          ))}
          
          {isLoading && <TypingIndicator />}
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* File Upload */}
      {showFileUpload && (
        <div className="border-t border-gray-200 bg-white p-4">
          <div className="max-w-4xl mx-auto">
            <FileUpload onFileSelect={handleFileSelect} />
            <button
              onClick={() => setShowFileUpload(false)}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              Cancel upload
            </button>
          </div>
        </div>
      )}

      {/* Input */}
      <div className="border-t border-gray-200 bg-white p-4">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
          <div className="flex gap-2 items-end">
            <button
              type="button"
              onClick={() => setShowFileUpload(!showFileUpload)}
              className="p-3 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-full transition-colors"
              title="Upload document"
            >
              <Paperclip className="w-5 h-5" />
            </button>
            
            <div className="flex-1">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type your message..."
                disabled={isLoading}
                className="w-full p-3 border border-gray-300 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
              />
            </div>
            
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="p-3 bg-primary-500 text-white rounded-full hover:bg-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}