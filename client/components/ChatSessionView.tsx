"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { getSession } from "@/lib/api";
import { Message, Session, SSEMessage } from "@/lib/types";
import { useChatStream } from "@/lib/useChatStream";
import { MarkdownRenderer } from "@/components/MarkdownRenderer";
import { MultimediaRenderer } from "@/components/MultimediaRenderer";
import { LiveThinking } from "@/components/LiveThinking";
import { ReasoningHistory } from "@/components/ReasoningHistory";
import { useSessionTitle } from "@/lib/SessionContext";
import { ChatInput } from "@/components/ChatInput";
import { cn } from "@/lib/utils";

interface ChatSessionViewProps {
  sessionId: string;
  initialQuery?: string | null;
  onInitialQueryConsumed?: () => void;
  autoFocusInput?: boolean;
  className?: string;
}

export function ChatSessionView({
  sessionId,
  initialQuery,
  onInitialQueryConsumed,
  autoFocusInput = true,
  className,
}: ChatSessionViewProps) {
  const queryClient = useQueryClient();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const pendingAutoStartRef = useRef<{ id: string; query: string } | null>(
    initialQuery && initialQuery.trim() ? { id: sessionId, query: initialQuery.trim() } : null,
  );
  const autoStartLockRef = useRef(false);

  const [messages, setMessages] = useState<Message[]>([]);
  const [completedSteps, setCompletedSteps] = useState<SSEMessage[]>([]);
  const [currentStep, setCurrentStep] = useState<SSEMessage | null>(null);
  const [streamingContent, setStreamingContent] = useState("");
  const [streamingOutputType, setStreamingOutputType] = useState<"text" | "image">("text");
  const [streamingUrl, setStreamingUrl] = useState<string | null>(null);
  const [streamingMimeType, setStreamingMimeType] = useState<string | null>(null);
  const [isStreamingFinished, setIsStreamingFinished] = useState(false);

  const generateMessageId = () => Date.now() * 1000 + Math.floor(Math.random() * 1000);

  const { setSessionTitle } = useSessionTitle();

  const handleMessage = useCallback(
    (event: SSEMessage) => {
      if (event.role === "user" && event.content) {
        const title = event.content.slice(0, 27) + (event.content.length > 30 ? "..." : "");
        setSessionTitle(title);
        queryClient.setQueryData(["sessions"], (old: Session[] | undefined) =>
          old?.map((s) => (s.id === sessionId ? { ...s, title } : s)),
        );
      }
    },
    [queryClient, sessionId, setSessionTitle],
  );

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
          id: generateMessageId(),
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
    onMessage: handleMessage,
    onPlanning: handlePlanning,
    onAction: handleAction,
    onFinal: handleFinal,
    onError: handleError,
    onDone: handleDone,
  });

  const { data: sessionData, isLoading, error } = useQuery({
    queryKey: ["session", sessionId],
    queryFn: () => getSession(sessionId),
  });

  useEffect(() => {
    if (initialQuery && initialQuery.trim()) {
      pendingAutoStartRef.current = { id: sessionId, query: initialQuery.trim() };
      autoStartLockRef.current = false;
    } else if (!initialQuery) {
      pendingAutoStartRef.current = null;
      autoStartLockRef.current = false;
    }
  }, [initialQuery, sessionId]);

  const appendUserMessageAndStream = useCallback(
    (query: string) => {
      const trimmed = query.trim();
      if (!trimmed) return;

      setStreamingContent("");
      setCompletedSteps([]);
      setCurrentStep(null);
      setIsStreamingFinished(false);

      setMessages((prev) => [
        ...prev,
        {
          id: generateMessageId(),
          role: "user",
          content: trimmed,
          timestamp: new Date().toISOString(),
        },
      ]);

      setTimeout(() => {
        chatContainerRef.current?.scrollTo({
          top: chatContainerRef.current.scrollHeight,
          behavior: "smooth",
        });
      }, 100);

      startStream(trimmed);
    },
    [startStream],
  );

  useEffect(() => {
    if (!pendingAutoStartRef.current) return;
    if (pendingAutoStartRef.current.id !== sessionId) return;
    if (autoStartLockRef.current) return;

    const nextQuery = pendingAutoStartRef.current.query;
    pendingAutoStartRef.current = null;
    autoStartLockRef.current = true;
    appendUserMessageAndStream(nextQuery);
    onInitialQueryConsumed?.();
  }, [appendUserMessageAndStream, onInitialQueryConsumed, sessionId]);

  useEffect(() => {
    if (sessionData?.session) {
      setSessionTitle(sessionData.session.title);
    }
  }, [sessionData, setSessionTitle]);

  useEffect(() => {
    if (sessionData?.messages && sessionData.messages.length > 0) {
      setMessages(sessionData.messages);
    }
  }, [sessionData]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingContent, completedSteps, currentStep]);

  useEffect(() => {
    setCompletedSteps([]);
    setCurrentStep(null);
    setStreamingContent("");
    setStreamingOutputType("text");
    setStreamingUrl(null);
    setStreamingMimeType(null);
    setIsStreamingFinished(false);
    autoStartLockRef.current = false;
  }, [sessionId]);

  const handleSubmit = useCallback(
    (query: string) => {
      if (!query || isStreaming) return;
      appendUserMessageAndStream(query);
    },
    [appendUserMessageAndStream, isStreaming],
  );

  if (isLoading) {
    return (
      <div className={cn("flex flex-1 items-center justify-center", className)}>
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error || !sessionData) {
    return (
      <div className={cn("flex flex-1 flex-col items-center justify-center", className)}>
        <p className="mb-4 text-destructive">Session not found</p>
      </div>
    );
  }

  const tokens = sessionData.tokens;
  const hasSteps = completedSteps.length > 0 || currentStep !== null;

  return (
    <div className={cn("relative flex h-full flex-1 flex-col overflow-hidden", className)}>
      <div
        ref={chatContainerRef}
        className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-primary/10 scrollbar-track-transparent"
      >
        <div className="mx-auto max-w-3xl space-y-6 p-6 pb-40">
          {messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                "flex animate-fade-in",
                message.role === "user" ? "justify-end" : "justify-start",
              )}
            >
              <div
                className={cn(
                  "max-w-3xl rounded-3xl px-6 py-4",
                  message.role === "user" ? "bg-card" : "text-foreground",
                )}
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
              <div className="w-full max-w-3xl">
                <AnimatePresence mode="wait">
                  {isStreamingFinished ? (
                    <motion.div
                      key="history"
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                    >
                      <ReasoningHistory
                        steps={[...completedSteps, currentStep].filter((s): s is SSEMessage => s !== null)}
                      />
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
              <div className="w-full max-w-3xl p-6 text-foreground shadow-sm">
                <MultimediaRenderer
                  output={streamingContent}
                  output_type={streamingOutputType}
                  url={streamingUrl}
                  mime_type={streamingMimeType}
                />
              </div>
            </div>
          )}

          {isStreaming && !streamingContent && !hasSteps && <LiveThinking step={null} />}

          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="pointer-events-none absolute bottom-0 left-0 right-0 bg-gradient-to-t from-background via-background/80 to-transparent p-4">
        <motion.div layoutId="chat-input-shell" className="pointer-events-auto">
          <ChatInput
            onSubmit={handleSubmit}
            isStreaming={isStreaming}
            stopStream={stopStream}
            autoFocus={autoFocusInput}
          />
        </motion.div>
        {tokens && tokens.total_tokens > 0 && (
          <div className="pointer-events-auto mt-2 text-center text-xs text-muted-foreground">
            Tokens: {tokens.input_tokens} in / {tokens.output_tokens} out / {tokens.total_tokens} total
          </div>
        )}
      </div>
    </div>
  );
}
