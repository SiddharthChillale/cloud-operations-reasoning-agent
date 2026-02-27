"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import { useState, useRef, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Trash2,
  Send,
  Loader2,
  ChevronDown,
  ChevronRight,
  Code,
  Lightbulb,
  Sparkles,
  ChevronUp,
} from "lucide-react";
import {
  getSession,
  getSessions,
  deleteSession,
} from "@/lib/api";
import { Message, SSEMessage } from "@/lib/types";
import { useChatStream } from "@/lib/useChatStream";
import { CollapsibleField } from "@/components/CollapsibleField";
import { CodeBlock } from "@/components/CodeBlock";
import { MarkdownRenderer } from "@/components/MarkdownRenderer";
import { MultimediaRenderer } from "@/components/MultimediaRenderer";

function parseThought(modelOutput: string): string {
  try {
    const parsed = JSON.parse(modelOutput);
    if (parsed.thought) return parsed.thought;
  } catch {
    // Not JSON, return as-is
  }
  return modelOutput;
}

export default function SessionPage() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const sessionId = params.id as string;
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [streamingContent, setStreamingContent] = useState("");
  const [streamingOutputType, setStreamingOutputType] = useState<"text" | "image">("text");
  const [streamingUrl, setStreamingUrl] = useState<string | null>(null);
  const [streamingMimeType, setStreamingMimeType] = useState<string | null>(null);
  const [steps, setSteps] = useState<SSEMessage[]>([]);
  const [isReasoningExpanded, setIsReasoningExpanded] = useState(true);
  const [isStreamingFinished, setIsStreamingFinished] = useState(false);

  const { data: sessionData, isLoading, error } = useQuery({
    queryKey: ["session", sessionId],
    queryFn: () => getSession(sessionId),
  });

  const { data: sessions } = useQuery({
    queryKey: ["sessions"],
    queryFn: getSessions,
  });

  const handlePlanning = useCallback((event: SSEMessage) => {
    setSteps((prev) => [...prev, event]);
  }, []);

  const handleAction = useCallback((event: SSEMessage) => {
    setSteps((prev) => [...prev, event]);
  }, []);

  const handleFinal = useCallback((event: SSEMessage) => {
    setStreamingContent(event.output || "");
    setStreamingOutputType(event.output_type || "text");
    setStreamingUrl(event.url || null);
    setStreamingMimeType(event.mime_type || null);
    setIsReasoningExpanded(false);
  }, []);

  const handleError = useCallback((error: string) => {
    setStreamingContent(`Error: ${error}`);
  }, []);

  const handleDone = useCallback(() => {
    if (streamingContent) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now(),
          role: "agent",
          content: streamingContent,
          timestamp: new Date().toISOString(),
        },
      ]);
    }
    setStreamingContent("");
    setStreamingOutputType("text");
    setStreamingUrl(null);
    setStreamingMimeType(null);
    setIsStreamingFinished(true);
    queryClient.invalidateQueries({ queryKey: ["session", sessionId] });
    queryClient.invalidateQueries({ queryKey: ["sessions"] });
  }, [streamingContent, queryClient, sessionId]);

  const { isStreaming, startStream } = useChatStream({
    sessionId,
    onPlanning: handlePlanning,
    onAction: handleAction,
    onFinal: handleFinal,
    onError: handleError,
    onDone: handleDone,
  });

  useEffect(() => {
    if (sessionData?.messages) {
      setMessages(sessionData.messages);
    }
  }, [sessionData]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingContent, steps, isReasoningExpanded]);

  const deleteMutation = useMutation({
    mutationFn: () => deleteSession(sessionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sessions"] });
      router.push("/");
    },
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;

    const query = input.trim();
    setInput("");
    setStreamingContent("");
    setSteps([]);
    setIsStreamingFinished(false);
    setIsReasoningExpanded(true);

    setMessages((prev) => [
      ...prev,
      {
        id: Date.now(),
        role: "user",
        content: query,
        timestamp: new Date().toISOString(),
      },
    ]);

    startStream(query);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (error || !sessionData) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center">
        <p className="text-red-600 mb-4">Session not found</p>
        <Link href="/" className="text-blue-600 hover:underline">
          Go back home
        </Link>
      </div>
    );
  }

  const currentSession = sessionData.session;
  const tokens = sessionData.tokens;

  const hasSteps = steps.length > 0;
  const planningSteps = steps.filter((s) => s.step_type === "PlanningStep");
  const actionSteps = steps.filter((s) => s.step_type === "ActionStep");

  return (
    <div className="min-h-screen flex">
      <aside className="w-64 bg-white border-r flex flex-col">
        <div className="p-4 border-b">
          <Link
            href="/"
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </Link>
        </div>
        <div className="flex-1 overflow-y-auto">
          <ul className="p-2">
            {sessions?.map((session) => (
              <li key={session.id}>
                <Link
                  href={`/sessions/${session.id}`}
                  className={`block p-2 rounded ${
                    session.id === sessionId
                      ? "bg-blue-50 text-blue-700"
                      : "hover:bg-gray-50"
                  }`}
                >
                  <p className="truncate text-sm">{session.title}</p>
                </Link>
              </li>
            ))}
          </ul>
        </div>
        <div className="p-4 border-t">
          <Link
            href="/"
            className="flex items-center justify-center w-full gap-2 px-4 py-2 text-sm text-gray-600 hover:text-gray-900 border rounded-lg hover:bg-gray-50"
          >
            <ArrowLeft className="w-4 h-4" />
            All Sessions
          </Link>
        </div>
      </aside>

      <main className="flex-1 flex flex-col">
        <header className="bg-white border-b px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-semibold">{currentSession.title}</h1>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={() => deleteMutation.mutate()}
              className="p-2 text-red-600 hover:bg-red-50 rounded"
              title="Delete session"
            >
              <Trash2 className="w-5 h-5" />
            </button>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${
                message.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`max-w-3xl px-4 py-2 rounded-lg ${
                  message.role === "user"
                    ? "bg-blue-600 text-white"
                    : "bg-gray-100 text-gray-900"
                }`}
              >
                {message.role === "user" ? (
                  <p className="whitespace-pre-wrap">{message.content}</p>
                ) : (
                  <MarkdownRenderer content={message.content} />
                )}
              </div>
            </div>
          ))}

          {hasSteps && (
            <div className="flex justify-start">
              <div className="max-w-3xl w-full">
                <button
                  onClick={() => setIsReasoningExpanded(!isReasoningExpanded)}
                  className="flex items-center gap-2 text-sm font-medium rounded-lg px-3 py-2 w-full transition-colors"
                >
                  <Sparkles className="w-4 h-4" />
                  <span>
                    Reasoning 
                    <span className="text-gray-90">({planningSteps.length} planning, {actionSteps.length} actions)</span>
                  </span>
                  {isReasoningExpanded ? (
                    <ChevronUp className="w-4 h-4" />
                  ) : (
                    <ChevronDown className="w-4 h-4" />
                  )}
                </button>
                <div className="h-64 overflow-y-auto">
                  {isReasoningExpanded && (
                      <div className="pl-2">
                      {steps.map((step, index) => (
                        <StepItem
                          key={index}
                          step={step}
                          stepIndex={index}
                        />
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {streamingContent && (
            <div className="flex justify-start">
              <div className="max-w-3xl px-4 py-2 rounded-lg bg-gray-100 text-gray-900">
                <MultimediaRenderer
                  output={streamingContent}
                  output_type={streamingOutputType}
                  url={streamingUrl}
                  mime_type={streamingMimeType}
                />
              </div>
            </div>
          )}

          {isStreaming && !streamingContent && !hasSteps && (
            <div className="flex justify-start">
              <div className="max-w-3xl px-4 py-2 rounded-lg bg-gray-100 text-gray-500 flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Thinking...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <footer className="bg-white border-t p-4">
          <form onSubmit={handleSubmit} className="max-w-3xl mx-auto flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask something..."
              disabled={isStreaming}
              className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
            />
            <button
              type="submit"
              disabled={!input.trim() || isStreaming}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isStreaming ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </form>
          {tokens && tokens.total_tokens > 0 && (
            <div className="max-w-3xl mx-auto mt-2 text-xs text-gray-500">
              Tokens: {tokens.input_tokens} in / {tokens.output_tokens} out /{" "}
              {tokens.total_tokens} total
            </div>
          )}
        </footer>
      </main>
    </div>
  );
}

function StepItem({ step, stepIndex }: { step: SSEMessage; stepIndex: number }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [expandedFields, setExpandedFields] = useState<Set<string>>(new Set());

  const toggleField = (field: string) => {
    setExpandedFields((prev) => {
      const next = new Set(prev);
      if (next.has(field)) {
        next.delete(field);
      } else {
        next.add(field);
      }
      return next;
    });
  };

  const isFieldExpanded = (field: string) => expandedFields.has(field);

  const isPlanning = step.step_type === "PlanningStep";
  const thought = step.model_output ? parseThought(step.model_output) : "";

  return (
    <div className="p-2 w-full">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 text-sm font-medium text-yellow-800 w-full"
      >
        {isPlanning ? (
          <Lightbulb className="w-4 h-4 flex-shrink-0 text-blue-500" />
        ) : (
          <Code className="w-4 h-4 flex-shrink-0 text-green-500" />
        )}
        <span className="truncate">
          Step {step.step_number}: {isPlanning ? "Planning" : "Action"}
        </span>
        {step.error && (
          <span className="text-xs bg-red-100 text-red-800 px-2 py-0.5 rounded">
            Error
          </span>
        )}
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 flex-shrink-0" />
        ) : (
          <ChevronDown className="w-4 h-4 flex-shrink-0" />
        )}
      </button>

      {isExpanded && (
        <div className="text-sm text-yellow-900 space-y-2 pl-2">
          {isPlanning && step.plan && (
            <div>
              {isExpanded && (
                <div className="mt-2 rounded p-2 text-xs overflow-x-auto text-gray-900">
                  <MarkdownRenderer content={step.plan} stripMarkdown />
                </div>
              )}
            </div>
          )}

          {!isPlanning && thought && (
            <div className="rounded p-2 text-xs overflow-x-auto text-gray-900">
                  <MarkdownRenderer content={thought} stripMarkdown />
            </div>
          )}

          {step.code_action && (
            <div>
              <button
                onClick={() => toggleField("code_action")}
                className="flex items-center gap-1 font-medium text-xs uppercase tracking-wide hover:underline text-green-600"
              >
                Code
                {isFieldExpanded("code_action") ? (
                  <ChevronUp className="w-4 h-4 flex-shrink-0" />
                ) : (
                  <ChevronDown className="w-4 h-4 flex-shrink-0" />
                )}
              </button>
              {isFieldExpanded("code_action") && (
                <div className="mt-2">
                  <CodeBlock code={step.code_action} language="python" />
                </div>
              )}
            </div>
          )}

          {step.observations && (
            <CollapsibleField
              label="Output"
              content={step.observations}
              isExpanded={isFieldExpanded("observations")}
              onToggle={() => toggleField("observations")}
            />
          )}

          {step.error && (
            <CollapsibleField
              label="Error"
              content={step.error}
              isExpanded={isFieldExpanded("error")}
              onToggle={() => toggleField("error")}
              isError
            />
          )}
        </div>
      )}
    </div>
  );
}
