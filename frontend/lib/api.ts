const API_BASE = '/api/visa';

export interface Message {
  role: 'human' | 'assistant';
  content: string;
  timestamp?: Date;
}

export interface Thread {
  thread_id: string;
}

export interface RunResponse {
  status: string;
  messages: Message[];
}

export class VisaAgentAPI {
  static async createThread(): Promise<string> {
    try {
      const response = await fetch(`${API_BASE}/threads`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: '{}',
      });
      
      if (!response.ok) {
        throw new Error(`Failed to create thread: ${response.statusText}`);
      }
      
      const thread: Thread = await response.json();
      return thread.thread_id;
    } catch (error) {
      console.error('Error creating thread:', error);
      throw error;
    }
  }

  static async sendMessage(threadId: string, message: string): Promise<Message[]> {
    try {
      const response = await fetch(`${API_BASE}/threads/${threadId}/runs/wait`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          assistant_id: 'visa_agent',
          input: {
            messages: [{ role: 'human', content: message }]
          }
        }),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to send message: ${response.statusText}`);
      }
      
      const result: RunResponse = await response.json();
      
      // Add timestamps and format messages
      return result.messages.map(msg => ({
        ...msg,
        timestamp: new Date(),
      }));
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
  }

  static async getThreadState(threadId: string): Promise<any> {
    try {
      const response = await fetch(`${API_BASE}/threads/${threadId}/state`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`Failed to get thread state: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting thread state:', error);
      throw error;
    }
  }
}