"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Copy, Check } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { getSession } from "@/lib/api";
import { Message, Session, SSEMessage } from "@/lib/types";
import { useChatStream } from "@/lib/useChatStream";
import { MarkdownRenderer } from "@/components/MarkdownRenderer";
import { MultimediaRenderer } from "@/components/MultimediaRenderer";
import { ChainOfThought } from "@/components/ChainOfThought";
import { useSessionTitle } from "@/lib/SessionContext";
import { ChatInput } from "@/components/ChatInput";
import { cn } from "@/lib/utils";

const MODELS = [
  { id: "gpt-4o", name: "GPT-4o" },
  { id: "gpt-4o-mini", name: "GPT-4o mini" },
  { id: "claude-haiku-4.5", name: "Claude Haiku 4.5" },
];

function MessageWithCopy({ message }: { message: Message }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      className={cn(
        "flex flex-col animate-fade-in",
        message.role === "user" ? "items-end" : "items-start",
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
      <button
        onClick={handleCopy}
        className="mt-1 p-1 text-muted-foreground hover:text-foreground transition-colors"
      >
        {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
      </button>
    </div>
  );
}

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
  const messagesRef = useRef<Message[]>([]);
  messagesRef.current = messages;
  const [pendingMessage, setPendingMessage] = useState<{ content: string; id: number } | null>(null);
  const pendingMessageRef = useRef<{ content: string; id: number } | null>(null);
  pendingMessageRef.current = pendingMessage;
  const [completedSteps, setCompletedSteps] = useState<SSEMessage[]>([]);
  const [currentStep, setCurrentStep] = useState<SSEMessage | null>(null);
  const [streamingContent, setStreamingContent] = useState("");
  const [streamingOutputType, setStreamingOutputType] = useState<"text" | "image">("text");
  const [streamingUrl, setStreamingUrl] = useState<string | null>(null);
  const [streamingMimeType, setStreamingMimeType] = useState<string | null>(null);
  const [isStreamingFinished, setIsStreamingFinished] = useState(false);
  const [modelId, setModelId] = useState(MODELS[0].id);

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

        setPendingMessage(null);
        setMessages((prev) => [
          ...prev,
          {
            id: generateMessageId(),
            role: "user",
            content: event.content || "",
            timestamp: new Date().toISOString(),
          },
        ]);
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
    modelId,
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

      const pendingId = generateMessageId();
      setPendingMessage({ content: trimmed, id: pendingId });

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

    autoStartLockRef.current = true;
    const nextQuery = pendingAutoStartRef.current.query;
    pendingAutoStartRef.current = null;
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
    setPendingMessage(null);
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
            <MessageWithCopy key={message.id} message={message} />
          ))}

          {pendingMessage && (
            <motion.div
              key={pendingMessage.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="flex justify-end"
            >
              <div className="max-w-3xl rounded-3xl px-6 py-4 bg-card">
                <p className="whitespace-pre-wrap text-sm leading-relaxed">{pendingMessage.content}</p>
                <motion.div
                  className="mt-2 h-1 rounded-full bg-primary/30"
                  initial={{ width: 0 }}
                  animate={{ width: "100%" }}
                  transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
                />
              </div>
            </motion.div>
          )}

          {hasSteps && (
            <div className="flex justify-start px-6">
              <div className="w-full max-w-3xl">
                <ChainOfThought
                  steps={completedSteps}
                  currentStep={currentStep}
                  isStreaming={isStreaming && !isStreamingFinished}
                />
              </div>
            </div>
          )}

          {streamingContent && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className="flex justify-start px-6"
            >
              <div className="w-full max-w-3xl p-6 text-foreground shadow-sm">
                <MultimediaRenderer
                  output={streamingContent}
                  output_type={streamingOutputType}
                  url={streamingUrl}
                  mime_type={streamingMimeType}
                />
              </div>
            </motion.div>
          )}

          {isStreaming && !streamingContent && !hasSteps && (
            <div className="flex justify-start px-6">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Thinking...</span>
              </div>
            </div>
          )}

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
            modelId={modelId}
            onModelChange={setModelId}
            models={MODELS}
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
