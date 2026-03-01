import { useState, useEffect, useCallback, useRef } from "react";
import { SSEMessage } from "./types";
import { interruptSession } from "./api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface UseChatStreamOptions {
  sessionId: string;
  onMessage?: (event: SSEMessage) => void;
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
  onMessage,
  onPlanning,
  onAction,
  onFinal,
  onError,
  onDone,
}: UseChatStreamOptions): UseChatStreamReturn {
  const [isStreaming, setIsStreaming] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);
  const runActiveRef = useRef(false);

  const closeEventSource = useCallback(
    async (shouldInterrupt: boolean) => {
      const currentSource = eventSourceRef.current;
      if (!currentSource) {
        setIsStreaming(false);
        return;
      }

      eventSourceRef.current = null;
      currentSource.close();

      if (shouldInterrupt && runActiveRef.current && sessionId) {
        console.log("[useChatStream] Interrupting agent and closing EventSource");
        try {
          await interruptSession(sessionId);
        } catch (e) {
          console.info("[useChatStream] Interrupt not needed or failed gracefully:", e);
        }
      }

      runActiveRef.current = false;
      setIsStreaming(false);
    },
    [sessionId]
  );

  const stopStream = useCallback(() => {
    void closeEventSource(true);
  }, [closeEventSource]);

  // Wrapper for external use (e.g., stop button) that doesn't call interrupt
  const closeStream = useCallback(() => {
    void closeEventSource(false);
  }, [closeEventSource]);

  const startStream = useCallback(
    (query: string) => {
      if (!sessionId) {
        console.warn("[useChatStream] Tried to start stream without a sessionId");
        return;
      }

      console.log("[useChatStream] Starting stream for query:", query);
      void closeEventSource(false);
      runActiveRef.current = false;

      const url = `${API_BASE}/sessions/${sessionId}/stream?${new URLSearchParams(
        { query }
      )}`;
      console.log("[useChatStream] Connecting to:", url);

      const eventSource = new EventSource(url);
      eventSourceRef.current = eventSource;

      setIsStreaming(true);

      eventSource.onopen = () => {
        console.log("[useChatStream] EventSource opened");
        runActiveRef.current = true;
      };

      eventSource.onmessage = (event) => {
        // console.log("[useChatStream] Raw message:", event.data);
        try {
          const data = JSON.parse(event.data) as SSEMessage;
          // console.log("[useChatStream] Parsed event:", data.type, data.step_number, data.step_type);

          switch (data.type) {
            case "message":
              onMessage?.(data);
              break;
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
        runActiveRef.current = false;
        // Just close the EventSource without interrupting - don't call interruptSession on errors
        if (eventSourceRef.current) {
          eventSourceRef.current.close();
          eventSourceRef.current = null;
        }
        setIsStreaming(false);
      };
    },
    [sessionId, closeEventSource, closeStream, onMessage, onPlanning, onAction, onFinal, onError, onDone]
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
