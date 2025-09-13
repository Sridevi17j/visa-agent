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
    <div className="flex flex-col h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-sm border-b border-gray-200/50 p-6 shadow-sm">
        <div className="flex items-center justify-between max-w-4xl mx-auto">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full flex items-center justify-center">
              <span className="text-white font-bold text-lg">V</span>
            </div>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                Veazy
              </h1>
              <p className="text-sm text-gray-600 font-medium">
                AI Visa Assistant
              </p>
            </div>
          </div>
          <button
            onClick={resetChat}
            className="p-3 text-gray-500 hover:text-gray-700 hover:bg-white/60 rounded-full transition-all duration-200 shadow-sm"
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
            Connection error: {error.message}. Make sure the LangGraph server is running on port 8000.
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
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {displayMessages.length === 0 && !isLoading && (
            <div className="text-center py-12">
              <div className="w-16 h-16 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-white font-bold text-xl">V</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-700 mb-2">Welcome to Veazy</h3>
              <p className="text-gray-500">Your AI-powered visa assistant. Ask me anything about visa applications!</p>
            </div>
          )}
          
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
      <div className="border-t border-gray-200/50 bg-white/60 backdrop-blur-sm p-6">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
          <div className="flex gap-3 items-end">
            <button
              type="button"
              onClick={() => setShowFileUpload(!showFileUpload)}
              className="p-3 text-gray-500 hover:text-gray-700 hover:bg-white/80 rounded-xl transition-all duration-200 shadow-sm"
              title="Upload document"
            >
              <Paperclip className="w-5 h-5" />
            </button>
            
            <div className="flex-1 relative">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about visa requirements, documents, or application process..."
                disabled={isLoading}
                className="w-full p-4 pl-6 pr-4 bg-white border border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50 disabled:cursor-not-allowed shadow-sm transition-all duration-200"
              />
            </div>
            
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="p-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl hover:from-blue-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-gray-300 disabled:cursor-not-allowed transition-all duration-200 shadow-lg"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}