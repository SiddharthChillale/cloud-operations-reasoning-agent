## 1. FastAPI Backend Changes

- [x] 1.1 Add CORS middleware to allow localhost:3000
- [x] 1.2 Add is_json_request() helper function
- [x] 1.3 Modify GET /sessions to return JSON when Accept: application/json
- [x] 1.4 Modify POST /sessions to return JSON when Accept: application/json
- [x] 1.5 Modify GET /sessions/{id} to return JSON when Accept: application/json
- [x] 1.6 Modify PATCH /sessions/{id} to return JSON when Accept: application/json
- [x] 1.7 Modify DELETE /sessions/{id} to return JSON when Accept: application/json
- [x] 1.8 Modify GET /sessions/{id}/tokens to return JSON when Accept: application/json
- [x] 1.9 Add new GET /sessions/{id}/stream endpoint for SSE with JSON format

## 2. Next.js Project Setup

- [x] 2.1 Create Next.js app at clients/web_ui/nextjs/
- [x] 2.2 Install dependencies (ai, @tanstack/react-query, tailwindcss, lucide-react)
- [x] 2.3 Configure Tailwind CSS
- [x] 2.4 Set up project structure (components/, lib/, app/)

## 3. API Client Implementation

- [x] 3.1 Create lib/types.ts with TypeScript interfaces
- [x] 3.2 Create lib/api.ts with getSessions, createSession, getSession, etc.
- [ ] 3.3 Create lib/useChat.ts hook for streaming chat

## 4. UI Components

- [x] 4.1 Create Sidebar component for session list
- [x] 4.2 Create MessageList component for displaying messages
- [x] 4.3 Create ChatInput component for user input
- [x] 4.4 Create StepViewer component for agent steps
- [x] 4.5 Create TokenUsage component for displaying tokens

## 5. Pages

- [x] 5.1 Create app/page.tsx (home - session list)
- [x] 5.2 Create app/layout.tsx (root layout with providers)
- [x] 5.3 Create app/sessions/[id]/page.tsx (chat page)

## 6. Testing

- [ ] 6.1 Test FastAPI endpoints with curl (JSON mode)
- [ ] 6.2 Test SSE streaming endpoint
- [ ] 6.3 Verify Next.js can connect to FastAPI
- [ ] 6.4 Verify both HTMX and Next.js work simultaneously
