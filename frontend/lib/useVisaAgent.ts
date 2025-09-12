'use client';

import { useStream } from "@langchain/langgraph-sdk/react";
import { useState, useCallback } from "react";

interface Message {
  id: string;
  type: 'human' | 'ai';
  content: string;
  timestamp: Date;
}

export function useVisaAgent() {
  
  const stream = useStream({
    apiUrl: "http://localhost:2024",
    assistantId: "visa_agent",
    messagesKey: "messages",
    onError: (error) => {
      console.error("Stream error:", error);
    }
  });

  // Convert LangGraph messages to our UI format - filter out non-string content
  const messages: Message[] = (stream.messages || [])
    .filter(msg => typeof msg.content === 'string' && msg.content.trim().length > 0)
    .map(msg => ({
      id: msg.id || Math.random().toString(),
      type: msg.type === 'human' ? 'human' : 'ai',
      content: msg.content as string,
      timestamp: msg.created_at ? new Date(msg.created_at) : new Date()
    }));

  const sendMessage = useCallback((content: string) => {
    if (!content.trim()) return;
    
    stream.submit({
      messages: [{ type: 'human', content }]
    });
  }, [stream]);

  const resetChat = useCallback(() => {
    // Create a new thread by clearing current one
    window.location.reload(); // Simple reset for now
  }, []);

  return {
    messages,
    sendMessage,
    resetChat,
    isLoading: stream.status === 'inflight',
    isInitialized: true, // Always true since hook manages initialization
    threadId: stream.threadId,
    error: stream.error
  };
}