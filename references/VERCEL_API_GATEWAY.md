# Multi‑Model Chat with smolagents + FastAPI + Vercel AI SDK (minimal)

This is a compact spec focused only on **model switching** between a fixed set of models.  
Assume:  
- Models: `gpt-4o`, `gpt-4o-mini`, `claude-3.5-sonnet`  
- Backend: FastAPI + `smolagents` over **Vercel AI Gateway**  
- Frontend: Next.js + Vercel AI SDK (`createChat`) talking to `/api/chat`

***

## 1. Models and IDs

Use a fixed mapping:

| `model_id`        | Meaning                          |
|-------------------|----------------------------------|
| `gpt-4o`          | `openai/gpt-4o`                  |
| `gpt-4o-mini`     | `openai/gpt-4o-mini`             |
| `claude-3.5-sonnet` | `anthropic/claude-3.5-sonnet`  |

All models are exposed via `https://ai-gateway.vercel.sh/v1`. [vercel](https://vercel.com/docs/ai-gateway)

In FastAPI, map each `model_id` to an `OpenAIServerModel` pointing at that base URL.

***

## 2. FastAPI backend: multi‑model chat (smolagents)

```python
import os
from typing import AsyncGenerator, List, Dict

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from smolagents import CodeAgent, OpenAIServerModel

app = FastAPI()

AI_GATEWAY_BASE = "https://ai-gateway.vercel.sh/v1"
AI_GATEWAY_KEY = os.getenv("AI_GATEWAY_API_KEY")

MODELS = {
    "gpt-4o": OpenAIServerModel(
        model_id="openai/gpt-4o",
        api_base=AI_GATEWAY_BASE,
        api_key=AI_GATEWAY_KEY,
    ),
    "gpt-4o-mini": OpenAIServerModel(
        model_id="openai/gpt-4o-mini",
        api_base=AI_GATEWAY_BASE,
        api_key=AI_GATEWAY_KEY,
    ),
    "claude-3.5-sonnet": OpenAIServerModel(
        model_id="anthropic/claude-3.5-sonnet",
        api_base=AI_GATEWAY_BASE,
        api_key=AI_GATEWAY_KEY,
    ),
}

class ChatRequest(BaseModel):
    model_id: str  # e.g. "gpt-4o"
    messages: List[Dict[str, str]]

@app.post("/chat", response_class=StreamingResponse)
async def chat(request: ChatRequest):
    model = MODELS.get(request.model_id)
    if not model:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model_id. Choose one of {list(MODELS.keys())}",
        )

    agent = CodeAgent(
        tools=[],            # add tools as needed
        model=model,
        stream_outputs=True,
    )

    async def event_stream() -> AsyncGenerator[bytes, None]:
        async for chunk in agent.run(request.messages):
            if chunk.content:
                yield f"data: {chunk.content}\n\n".encode("utf-8")

    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

***

## 3. Next.js API route: proxy to FastAPI

`app/api/chat/route.ts`:

```ts
import { NextRequest } from "next/server";

const FASTAPI_BASE_URL = process.env.FASTAPI_BASE_URL || "http://localhost:8000";

export async function POST(req: NextRequest) {
  const body = await req.json();

  const response = await fetch(`${FASTAPI_BASE_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model_id: body.model_id,
      messages: body.messages,
    }),
  });

  if (!response.ok) return new Response("Error", { status: 500 });

  return new Response(response.body, {
    headers: { "Content-Type": "text/event-stream" },
  });
}
```

***

## 4. Next.js frontend: minimal model switch

Using `createChat` from Vercel AI SDK:

```tsx
import { createChat } from "ai";
import { useState } from "react";

type ModelId = "gpt-4o" | "gpt-4o-mini" | "claude-3.5-sonnet";

const MODEL_OPTIONS: Array<{ label: string; value: ModelId }> = [
  { label: "GPT‑4o", value: "gpt-4o" },
  { label: "GPT‑4o‑mini", value: "gpt-4o-mini" },
  { label: "Claude 3.5 Sonnet", value: "claude-3.5-sonnet" },
];

export function Chat() {
  const [modelId, setModelId] = useState<ModelId>("gpt-4o");

  const { messages, input, handleInputChange, handleSubmit } = createChat({
    api: "/api/chat",
    body: { model_id: modelId },
  });

  return (
    <div className="flex flex-col h-screen">
      <div className="p-4 border-b">
        <label>Model:</label>
        <select
          value={modelId}
          onChange={(e) => setModelId(e.target.value as ModelId)}
        >
          {MODEL_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      <div className="flex-1 p-4">
        {messages.map((m) => (
          <div key={m.id}>
            <div>{m.content}</div>
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="p-4 border-t">
        <input
          value={input}
          onChange={handleInputChange}
          placeholder="Type a message..."
          className="w-full px-3 py-2 border rounded"
        />
      </form>
    </div>
  );
}
```
