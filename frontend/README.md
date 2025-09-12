# Visa Agent Frontend

Professional Next.js frontend for the Visa Agent application.

## Features

- Modern, professional UI with Tailwind CSS
- Real-time chat interface with typing indicators
- Drag & drop file upload for documents
- Context switching support
- Responsive design
- TypeScript for type safety

## Quick Start

1. **Install dependencies:**
```bash
cd frontend
npm install
```

2. **Start the development server:**
```bash
npm run dev
```

3. **Make sure LangGraph API is running:**
```bash
# In the root directory
langgraph dev --port 2024
```

4. **Open your browser:**
Navigate to `http://localhost:3000`

## Architecture

- **Frontend:** Next.js 14 with App Router
- **Styling:** Tailwind CSS with custom components
- **API Integration:** Proxy to LangGraph API server
- **State Management:** React hooks for chat state
- **File Uploads:** Drag & drop with file validation

## API Integration

The frontend communicates with the LangGraph API server through:
- Thread creation for new conversations
- Message streaming for real-time responses
- File upload handling for document processing
- Context switching support

## Development

The app uses Next.js API rewrites to proxy requests to the LangGraph server, avoiding CORS issues during development.