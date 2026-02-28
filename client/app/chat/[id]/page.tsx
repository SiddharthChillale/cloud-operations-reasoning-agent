"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { useState, useRef, useEffect, useCallback } from "react";
import {
  Send,
  Loader2,
  Square,
} from "lucide-react";
import {
  getSession,
} from "@/lib/api";
import { Message, SSEMessage } from "@/lib/types";
import { useChatStream } from "@/lib/useChatStream";
import { MarkdownRenderer } from "@/components/MarkdownRenderer";
import { MultimediaRenderer } from "@/components/MultimediaRenderer";
import { LiveThinking } from "@/components/LiveThinking";
import { ReasoningHistory } from "@/components/ReasoningHistory";
import { AnimatePresence, motion } from "framer-motion";

export default function ChatSessionPage() {
  const params = useParams();
  const queryClient = useQueryClient();
  const sessionId = params.id as string;
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [completedSteps, setCompletedSteps] = useState<SSEMessage[]>([]);
  const [currentStep, setCurrentStep] = useState<SSEMessage | null>(null);
  const [streamingContent, setStreamingContent] = useState("");
  const [streamingOutputType, setStreamingOutputType] = useState<"text" | "image">("text");
  const [streamingUrl, setStreamingUrl] = useState<string | null>(null);
  const [streamingMimeType, setStreamingMimeType] = useState<string | null>(null);
  const [isStreamingFinished, setIsStreamingFinished] = useState(false);

  const { data: sessionData, isLoading, error } = useQuery({
    queryKey: ["session", sessionId],
    queryFn: () => getSession(sessionId),
  });

  const handlePlanning = useCallback((event: SSEMessage) => {
    setCompletedSteps((prev) => [...prev, event]);
    setCurrentStep(event);
  }, []);

  const handleAction = useCallback((event: SSEMessage) => {
    setCompletedSteps((prev) => [...prev, event]);
    setCurrentStep(event);
  }, []);

  const handleFinal = useCallback((event: SSEMessage) => {
    setCurrentStep(null);
    setStreamingContent(event.output || "");
    setStreamingOutputType(event.output_type || "text");
    setStreamingUrl(event.url || null);
    setStreamingMimeType(event.mime_type || null);
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
    setCurrentStep(null);
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
  }, [messages, streamingContent, completedSteps, currentStep]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;

    const query = input.trim();
    setInput("");
    setStreamingContent("");
    setCompletedSteps([]);
    setCurrentStep(null);
    setIsStreamingFinished(false);

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

  const hasSteps = completedSteps.length > 0 || currentStep !== null;
  const planningSteps = completedSteps.filter((s) => s.step_type === "PlanningStep");
  const actionSteps = completedSteps.filter((s) => s.step_type === "ActionStep");

  return (
    <div className="relative flex-1 flex flex-col h-full overflow-hidden">
      <div
        ref={chatContainerRef}
        className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-primary/10 scrollbar-track-transparent"
      >
        <div className="p-6 pb-40 space-y-6 max-w-4xl mx-auto">

          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${
                message.role === "user" ? "justify-end" : "justify-start"
              } animate-fade-in`}
            >
              <div
                className={`max-w-3xl px-6 py-4 rounded-3xl ${
                  message.role === "user"
                    ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20"
                    : "bg-card border border-border/60 text-foreground shadow-sm"
                }`}
              >
                {message.role === "user" ? (
                  <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</p>
                ) : (
                  <div className="text-sm leading-relaxed">
                    <MarkdownRenderer content={message.content} />
                  </div>
                )}
              </div>
            </div>
          ))}

          {hasSteps && (
            <div className="flex justify-start px-6">
              <div className="max-w-3xl w-full">
                <AnimatePresence mode="wait">
                  {isStreamingFinished ? (
                    <motion.div
                      key="history"
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                    >
                      <ReasoningHistory steps={[...completedSteps, currentStep].filter((s): s is SSEMessage => s !== null)} />
                    </motion.div>
                  ) : (
                    <motion.div
                      key="live"
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                    >
                      <LiveThinking step={currentStep} />
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>
          )}

          {streamingContent && (
            <div className="flex justify-start px-6">
              <div className="max-w-3xl w-full p-6 bg-card border border-border/60 rounded-3xl text-foreground shadow-sm">
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
            <LiveThinking step={null} />
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-background via-background/80 to-transparent pointer-events-none">
        <div className="max-w-3xl mx-auto pointer-events-auto">
          <form onSubmit={handleSubmit} className="flex gap-2 bg-background p-2 shadow-2xl border border-border rounded-2xl overflow-hidden backdrop-blur-sm">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Query cloud infrastructure..."
              disabled={isStreaming}
              className="flex-1 px-4 py-2 focus:outline-none disabled:bg-muted bg-transparent text-foreground"
            />
            <button
              type={isStreaming ? "button" : "submit"}
              disabled={!input.trim() && !isStreaming}
              onClick={(e) => {
                if (isStreaming) {
                  e.preventDefault();
                  stopStream();
                }
              }}
              className={`p-2 rounded-lg transition-all ${
                isStreaming
                  ? "ring-2 ring-red-500 animate-pulse"
                  : "hover:bg-muted"
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              {isStreaming ? (
                <div className="w-5 h-5 bg-red-100 rounded-full flex items-center justify-center">
                  <Square className="w-3.5 h-3.5 text-red-600" />
                </div>
              ) : (
                <Send className="w-5 h-5 text-primary" />
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
