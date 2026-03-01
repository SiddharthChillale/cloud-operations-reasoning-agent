"use client";

import { type KeyboardEvent, useCallback, useEffect, useRef, useState } from "react";
import { Send, Square } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  onSubmit: (value: string) => void;
  isStreaming?: boolean;
  stopStream?: () => void;
  placeholder?: string;
  autoFocus?: boolean;
  className?: string;
}

export function ChatInput({
  onSubmit,
  isStreaming = false,
  stopStream,
  placeholder = "Ask anything...",
  autoFocus = true,
  className,
}: ChatInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    if (autoFocus) {
      textareaRef.current?.focus();
    }
  }, [autoFocus]);

  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 180)}px`;
  }, [value]);

  const resetInput = useCallback(() => {
    setValue("");
    textareaRef.current?.focus();
  }, []);

  const handleSubmit = useCallback(() => {
    const nextValue = value.trim();
    if (!nextValue || isStreaming) return;
    onSubmit(nextValue);
    resetInput();
  }, [isStreaming, onSubmit, resetInput, value]);

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div
      className={cn(
        "relative rounded-3xl border border-border/70 bg-background/80 shadow-xl shadow-primary/5 backdrop-blur",
        className,
      )}
    >
      <textarea
        ref={textareaRef}
        value={value}
        placeholder={placeholder}
        onChange={(event) => setValue(event.target.value)}
        onKeyDown={handleKeyDown}
        className="w-full resize-none bg-transparent px-5 py-4 pr-16 text-sm leading-relaxed text-foreground placeholder:text-muted-foreground focus:outline-none"
        rows={1}
        disabled={isStreaming && !stopStream}
      />

      <div className="absolute bottom-3 right-3 flex items-center gap-2">
        <AnimatePresence initial={false} mode="wait">
          {isStreaming ? (
            <motion.button
              key="stop"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              whileTap={{ scale: 0.94 }}
              onClick={stopStream}
              disabled={!stopStream}
              className={cn(
                "flex h-9 w-9 items-center justify-center rounded-2xl border border-destructive/40 bg-destructive/10 text-destructive transition-colors hover:bg-destructive/20",
                !stopStream && "cursor-not-allowed opacity-60",
              )}
              title="Stop generating"
            >
              <Square className="h-4 w-4" />
            </motion.button>
          ) : (
            <motion.button
              key="send"
              type="button"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              whileTap={{ scale: 0.94 }}
              onClick={handleSubmit}
              className="flex h-9 w-9 items-center justify-center rounded-2xl bg-primary text-primary-foreground transition-colors hover:bg-primary/90"
              title="Send message"
            >
              <Send className="h-4 w-4" />
            </motion.button>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
