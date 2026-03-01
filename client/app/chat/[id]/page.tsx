"use client";

import { useParams, useSearchParams } from "next/navigation";
import { useCallback } from "react";
import { ChatSessionView } from "@/components/ChatSessionView";

export default function ChatSessionPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const sessionId = params.id as string;
  const initialQuery = searchParams.get("q");

  const handleInitialQueryConsumed = useCallback(() => {
    const newUrl = window.location.pathname;
    window.history.replaceState({ ...window.history.state, as: newUrl, url: newUrl }, "", newUrl);
  }, []);

  return (
    <ChatSessionView
      sessionId={sessionId}
      initialQuery={initialQuery ?? undefined}
      onInitialQueryConsumed={initialQuery ? handleInitialQueryConsumed : undefined}
      autoFocusInput={false}
    />
  );
}
