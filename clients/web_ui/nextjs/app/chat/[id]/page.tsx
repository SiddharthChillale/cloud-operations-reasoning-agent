"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { useState, useRef, useEffect, useCallback } from "react";
import {
  Send,
  Loader2,
  ChevronDown,
  ChevronUp,
  Code,
  Lightbulb,
  Sparkles,
  Square,
} from "lucide-react";
import {
  getSession,
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

export default function ChatSessionPage() {
  const params = useParams();
  const queryClient = useQueryClient();
  const sessionId = params.id as string;
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);

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

  const { isStreaming, startStream, stopStream } = useChatStream({
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

    setTimeout(() => {
      chatContainerRef.current?.scrollTo({
        top: chatContainerRef.current.scrollHeight,
        behavior: "smooth",
      });
    }, 100);

    startStream(query);
  };

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error || !sessionData) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center">
        <p className="text-destructive mb-4">Session not found</p>
      </div>
    );
  }

  const currentSession = sessionData.session;
  const tokens = sessionData.tokens;

  const hasSteps = steps.length > 0;
  const planningSteps = steps.filter((s) => s.step_type === "PlanningStep");
  const actionSteps = steps.filter((s) => s.step_type === "ActionStep");

  return (
    <div className="relative flex-1 flex flex-col min-h-0">
      <div
        ref={chatContainerRef}
        className="flex-1 overflow-y-auto p-3 pb-32 space-y-4"
      >
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
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-foreground"
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
                className="flex items-center gap-2 text-sm font-medium rounded-lg px-3 py-2 w-full transition-colors hover:bg-muted"
              >
                <Sparkles className="w-4 h-4" />
                <span>
                  Reasoning 
                  <span className="text-muted-foreground">({planningSteps.length} planning, {actionSteps.length} actions)</span>
                </span>
                {isReasoningExpanded ? (
                  <ChevronUp className="w-4 h-4" />
                ) : (
                  <ChevronDown className="w-4 h-4" />
                )}
              </button>
              {isReasoningExpanded && (
                <div className="h-64 overflow-y-auto">
                  <div className="pl-2">
                    {steps.map((step, index) => (
                      <StepItem
                        key={index}
                        step={step}
                        stepIndex={index}
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {streamingContent && (
          <div className="flex justify-start">
            <div className="max-w-3xl px-4 py-2 rounded-lg bg-muted text-foreground">
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
            <div className="max-w-3xl px-4 py-2 rounded-lg bg-muted text-muted-foreground flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Thinking...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-background via-background/80 to-transparent pointer-events-none">
        <div className="max-w-3xl mx-auto pointer-events-auto">
          <form onSubmit={handleSubmit} className="flex gap-2 bg-background border rounded-lg p-2 shadow-lg">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask something..."
              disabled={isStreaming}
              className="flex-1 px-4 py-2 focus:outline-none disabled:bg-muted bg-transparent text-foreground"
            />
            <button
              type="submit"
              disabled={!input.trim() || isStreaming}
              onClick={(e) => {
                if (isStreaming) {
                  e.preventDefault();
                  stopStream();
                }
              }}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isStreaming ? (
                <Square className="w-5 h-5" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </form>
          {tokens && tokens.total_tokens > 0 && (
            <div className="mt-2 text-xs text-muted-foreground text-center">
              Tokens: {tokens.input_tokens} in / {tokens.output_tokens} out /{" "}
              {tokens.total_tokens} total
            </div>
          )}
        </div>
      </div>
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
        className="flex items-center gap-2 text-sm font-medium w-full"
      >
        {isPlanning ? (
          <Lightbulb className="w-4 h-4 flex-shrink-0 text-blue-500" />
        ) : (
          <Code className="w-4 h-4 flex-shrink-0 text-green-500" />
        )}
        <span className="truncate text-foreground">
          Step {step.step_number}: {isPlanning ? "Planning" : "Action"}
        </span>
        {step.error && (
          <span className="text-xs bg-destructive/10 text-destructive px-2 py-0.5 rounded">
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
        <div className="text-sm space-y-2 pl-2">
          {isPlanning && step.plan && (
            <div className="mt-2 rounded p-2 text-xs overflow-x-auto">
              <MarkdownRenderer content={step.plan} stripMarkdown />
            </div>
          )}

          {!isPlanning && thought && (
            <div className="rounded p-2 text-xs overflow-x-auto text-foreground">
              <MarkdownRenderer content={thought} stripMarkdown />
            </div>
          )}

          {step.code_action && (
            <div>
              <button
                onClick={() => toggleField("code_action")}
                className="flex items-center gap-1 font-medium text-xs uppercase tracking-wide text-green-600"
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
