"use client";

import Image from "next/image";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import { useSearchParams } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { createSession } from "@/lib/api";
import { Session } from "@/lib/types";
import { ChatInput } from "@/components/ChatInput";
import { ChatSessionView } from "@/components/ChatSessionView";
import { cn } from "@/lib/utils";
import { useSessionTitle } from "@/lib/SessionContext";

export default function ChatPage() {
  const { theme } = useTheme();
  const searchParams = useSearchParams();
  const resetToken = searchParams.get("new");
  const [mounted, setMounted] = useState(false);
  const [stage, setStage] = useState<"idle" | "bootstrapping" | "active">("idle");
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [pendingQuery, setPendingQuery] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const { setSessionTitle } = useSessionTitle();

  const createSessionMutation = useMutation({
    mutationFn: createSession,
    onSuccess: (data, variables) => {
      queryClient.setQueryData(["sessions"], (old: Session[] | undefined) => {
        const newSession: Session = {
          id: data.session_id,
          title: variables || "New Chat",
          status: "idle",
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };
        return old ? [newSession, ...old] : [newSession];
      });
      setActiveSessionId(data.session_id);
      setStage("active");
    },
    onError: () => {
      setStage("idle");
      setPendingQuery(null);
    },
  });

  const handleInitialSubmit = (query: string) => {
    if (!query.trim()) return;
    setPendingQuery(query);
    setStage("bootstrapping");
    createSessionMutation.mutate(query);
  };

  const handleInitialQueryConsumed = () => {
    setPendingQuery(null);
  };

  const showHero = stage !== "active";

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    setActiveSessionId(null);
    setPendingQuery(null);
    setStage("idle");
    setSessionTitle("");
  }, [resetToken, setSessionTitle]);

  return (
    <div className="relative flex h-full flex-1 flex-col overflow-hidden">
      <AnimatePresence mode="wait">
        {showHero && (
          <motion.section
            key="chat-hero"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -40, scale: 0.98 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
            className="relative z-10 flex flex-1 flex-col items-center justify-center bg-muted/5 px-6 py-10"
          >
            <div className="mb-10 flex flex-col items-center text-center">
              <div className="mb-6 flex items-center justify-center">
                <Image
                  src={mounted && theme === "dark" ? "/cora-icon-dark.svg" : "/cora-icon-large.svg"}
                  alt="CORA"
                  width={72}
                  height={72}
                  className="object-contain"
                  priority
                />
              </div>
              <h3 className="mb-4 text-3xl font-black tracking-tighter text-foreground">
                How can I help you today?
              </h3>
              <p className="max-w-xl text-base leading-relaxed text-muted-foreground">
                Ask anything about your cloud infrastructure, costs, or architecture. I&apos;m ready to reason.
              </p>
            </div>

            <motion.div layoutId="chat-input-shell" className="w-full max-w-3xl">
              <ChatInput
                onSubmit={handleInitialSubmit}
                isStreaming={createSessionMutation.isPending || stage === "bootstrapping"}
                placeholder="Type your first query..."
              />
            </motion.div>
          </motion.section>
        )}
      </AnimatePresence>

      <AnimatePresence mode="wait">
        {activeSessionId && (
          <motion.div
            key={activeSessionId}
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 40 }}
            transition={{ duration: 0.45, ease: "easeOut" }}
            className={cn("flex h-full flex-1", showHero && "pointer-events-none opacity-0")}
          >
            <ChatSessionView
              sessionId={activeSessionId}
              initialQuery={pendingQuery ?? undefined}
              onInitialQueryConsumed={handleInitialQueryConsumed}
              autoFocusInput={!showHero}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
