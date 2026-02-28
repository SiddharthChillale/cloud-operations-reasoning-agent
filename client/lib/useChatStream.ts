import { useState, useEffect, useCallback, useRef } from "react";
import { SSEMessage } from "./types";
import { interruptSession } from "./api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface UseChatStreamOptions {
  sessionId: string;
  onPlanning?: (event: SSEMessage) => void;
  onAction?: (event: SSEMessage) => void;
  onFinal?: (event: SSEMessage) => void;
  onError?: (error: string) => void;
  onDone?: () => void;
}

interface UseChatStreamReturn {
  isStreaming: boolean;
  startStream: (query: string) => void;
  stopStream: () => void;
  closeStream: () => void;
}

export function useChatStream({
  sessionId,
  onPlanning,
  onAction,
  onFinal,
  onError,
  onDone,
}: UseChatStreamOptions): UseChatStreamReturn {
  const [isStreaming, setIsStreaming] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);

  const stopStream = useCallback(async () => {
    if (eventSourceRef.current) {
      console.log("[useChatStream] Interrupting agent and closing EventSource");
      try {
        await interruptSession(sessionId);
      } catch (e) {
        console.warn("[useChatStream] Failed to interrupt session:", e);
      }
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setIsStreaming(false);
  }, [sessionId]);

  // Wrapper for external use (e.g., stop button) that doesn't call interrupt
  const closeStream = useCallback(() => {
    if (eventSourceRef.current) {
      console.log("[useChatStream] Closing EventSource");
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setIsStreaming(false);
  }, []);

  const startStream = useCallback(
    (query: string) => {
      console.log("[useChatStream] Starting stream for query:", query);
      stopStream();

      const url = `${API_BASE}/sessions/${sessionId}/stream?${new URLSearchParams(
        { query }
      )}`;
      console.log("[useChatStream] Connecting to:", url);

      const eventSource = new EventSource(url);
      eventSourceRef.current = eventSource;

      setIsStreaming(true);

      eventSource.onopen = () => {
        console.log("[useChatStream] EventSource opened");
      };

      eventSource.onmessage = (event) => {
        console.log("[useChatStream] Raw message:", event.data);
        try {
          const data = JSON.parse(event.data) as SSEMessage;
          console.log("[useChatStream] Parsed event:", data.type, data.step_number, data.step_type);

          switch (data.type) {
            case "planning":
              onPlanning?.(data);
              break;
            case "action":
              onAction?.(data);
              break;
            case "final":
              onFinal?.(data);
              break;
            case "error":
              onError?.(data.error || "Unknown error");
              break;
            case "cancelled":
              console.log("[useChatStream] Stream cancelled");
              closeStream();
              break;
            case "done":
              console.log("[useChatStream] Stream done");
              onDone?.();
              closeStream();
              break;
          }
        } catch (e) {
          console.error("[useChatStream] Failed to parse event:", e);
        }
      };

      eventSource.onerror = (error) => {
        console.error("[useChatStream] EventSource error:", error);
        // Just close the EventSource without interrupting - don't call interruptSession on errors
        if (eventSourceRef.current) {
          eventSourceRef.current.close();
          eventSourceRef.current = null;
        }
        setIsStreaming(false);
      };
    },
    [sessionId, stopStream, closeStream, onPlanning, onAction, onFinal, onError, onDone]
  );

  useEffect(() => {
    return () => {
      stopStream();
    };
  }, [stopStream]);

  return {
    isStreaming,
    startStream,
    stopStream,
    closeStream,
  };
}
