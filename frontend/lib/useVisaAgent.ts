'use client';

// Temporarily disable LangGraph SDK to test direct API calls
// import { useStream } from "@langchain/langgraph-sdk/react";
import { useState, useCallback, useEffect } from "react";

interface Message {
  id: string;
  type: 'human' | 'ai';
  content: string;
  timestamp: Date;
}

export function useVisaAgent() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [threadId, setThreadId] = useState<string | null>(null);
  const [error, setError] = useState<Error | null>(null);

  // Create thread on mount
  useEffect(() => {
    const createThread = async () => {
      try {
        const response = await fetch('http://localhost:8000/threads', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: '{}'
        });
        const data = await response.json();
        setThreadId(data.thread_id);
      } catch (err) {
        setError(err as Error);
      }
    };
    createThread();
  }, []);

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || !threadId) return;
    
    setIsLoading(true);
    setError(null);

    // Add user message immediately
    const userMessage: Message = {
      id: Math.random().toString(),
      type: 'human',
      content,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      const response = await fetch(`http://localhost:8000/threads/${threadId}/runs/wait`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [{ content }]
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${await response.text()}`);
      }

      const result = await response.json();
      
      // Add AI responses
      if (result.messages) {
        const aiMessages: Message[] = result.messages.map((msg: any) => ({
          id: Math.random().toString(),
          type: 'ai' as const,
          content: msg.content,
          timestamp: new Date()
        }));
        setMessages(prev => [...prev, ...aiMessages]);
      }

    } catch (err) {
      setError(err as Error);
      console.error('Send message error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [threadId]);

  const resetChat = useCallback(() => {
    setMessages([]);
    setThreadId(null);
    setError(null);
    // Recreate thread
    window.location.reload();
  }, []);

  return {
    messages,
    sendMessage,
    resetChat,
    isLoading,
    isInitialized: threadId !== null,
    threadId,
    error
  };
}