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
        // Production endpoint
        const response = await fetch('https://visa-agent-1.onrender.com/threads', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: '{}'
        });
        // Local development endpoint (commented for production deployment)
        // const response = await fetch('http://localhost:8000/threads', {
        //   method: 'POST',
        //   headers: { 'Content-Type': 'application/json' },
        //   body: '{}'
        // });
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

    // Generate unique ID for this conversation turn (ignoring backend chunk IDs)
    const conversationTurnId = `ai_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    // Add user message immediately
    const userMessage: Message = {
      id: Math.random().toString(),
      type: 'human',
      content,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      // NON-STREAMING ENDPOINT (COMMENTED OUT FOR BACKUP)
      // const response = await fetch(`http://localhost:8000/threads/${threadId}/runs/wait`, {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({
      //     messages: [{ content }]
      //   })
      // });
      // if (!response.ok) {
      //   throw new Error(`HTTP ${response.status}: ${await response.text()}`);
      // }
      // const result = await response.json();
      // if (result.messages) {
      //   const aiMessages: Message[] = result.messages.map((msg: any) => ({
      //     id: Math.random().toString(),
      //     type: 'ai' as const,
      //     content: msg.content,
      //     timestamp: new Date()
      //   }));
      //   setMessages(prev => [...prev, ...aiMessages]);
      // }

      // STREAMING ENDPOINT
      const response = await fetch(`https://visa-agent-1.onrender.com/threads/${threadId}/runs/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          input: {
            messages: [{ content }]
          }
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${await response.text()}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (reader) {
        let currentAiMessage: Message | null = null;
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                
                if (data.type === 'ai' && data.content) {
                  if (!currentAiMessage) {
                    // Start new AI message with unique conversation turn ID (ignore backend chunk ID)
                    currentAiMessage = {
                      id: conversationTurnId,
                      type: 'ai',
                      content: data.content,
                      timestamp: new Date()
                    };
                    setMessages(prev => [...prev, currentAiMessage!]);
                  } else {
                    // Update existing AI message with new content
                    currentAiMessage.content += data.content;
                    setMessages(prev => prev.map(msg => 
                      msg.id === currentAiMessage!.id 
                        ? { ...msg, content: currentAiMessage!.content }
                        : msg
                    ));
                  }
                }
              } catch (parseError) {
                console.warn('Failed to parse streaming data:', line);
              }
            }
          }
        }
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