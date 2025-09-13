'use client';

import { Bot } from 'lucide-react';

export default function TypingIndicator() {
  return (
    <div className="flex gap-4 mb-6">
      <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full flex items-center justify-center shadow-lg">
        <Bot className="w-5 h-5 text-white" />
      </div>
      <div className="bg-white rounded-2xl rounded-bl-md shadow-lg border border-gray-100 px-6 py-4">
        <div className="typing-indicator">
          <div className="typing-dot bg-blue-400"></div>
          <div className="typing-dot bg-purple-400"></div>
          <div className="typing-dot bg-blue-400"></div>
        </div>
      </div>
    </div>
  );
}