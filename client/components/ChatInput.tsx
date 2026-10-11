"use client";

import { type KeyboardEvent, useCallback, useEffect, useRef, useState } from "react";
import { Send, Square, ChevronDown } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface ModelOption {
  id: string;
  name: string;
}

interface ChatInputProps {
  onSubmit: (value: string) => void;
  isStreaming?: boolean;
  stopStream?: () => void;
  placeholder?: string;
  autoFocus?: boolean;
  className?: string;
  modelId?: string;
  onModelChange?: (modelId: string) => void;
  models?: ModelOption[];
}

export function ChatInput({
  onSubmit,
  isStreaming = false,
  stopStream,
  placeholder = "Ask anything...",
  autoFocus = true,
  className,
  modelId,
  onModelChange,
  models = [],
}: ChatInputProps) {
  const [value, setValue] = useState("");
  const [showModelDropdown, setShowModelDropdown] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const dropdownRef = useRef<HTMLDivElement | null>(null);

  const currentModel = models.find(m => m.id === modelId) || models[0];

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

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowModelDropdown(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

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

  const handleModelSelect = (id: string) => {
    onModelChange?.(id);
    setShowModelDropdown(false);
  };

  return (
    <div
      className={cn(
        "relative mx-auto rounded-3xl border border-border/70 bg-background/80 shadow-xl shadow-primary/5 backdrop-blur",
        className,
      )}
    >
      <textarea
        ref={textareaRef}
        value={value}
        placeholder={placeholder}
        onChange={(event) => setValue(event.target.value)}
        onKeyDown={handleKeyDown}
        className="w-full resize-none bg-transparent px-5 py-4 pr-40 text-sm leading-relaxed text-foreground placeholder:text-muted-foreground focus:outline-none"
        rows={1}
        disabled={isStreaming && !stopStream}
      />

      <div className="absolute bottom-3 right-3 flex items-center gap-2">
        {models.length > 0 && (
          <div ref={dropdownRef} className="relative">
            <button
              type="button"
              onClick={() => setShowModelDropdown(!showModelDropdown)}
              className={cn(
                "flex items-center gap-1 rounded-lg px-2 py-1.5 text-xs font-medium transition-colors",
                "bg-muted hover:bg-muted/80 text-foreground",
                isStreaming && "opacity-50 cursor-not-allowed"
              )}
              disabled={isStreaming}
            >
              <span>{currentModel?.name || "Model"}</span>
              <ChevronDown className="h-3 w-3" />
            </button>
            
            <AnimatePresence>
              {showModelDropdown && (
                <motion.div
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 4 }}
                  className="absolute bottom-full right-0 mb-1 w-40 rounded-lg border bg-background p-1 shadow-lg"
                >
                  {models.map((model) => (
                    <button
                      key={model.id}
                      type="button"
                      onClick={() => handleModelSelect(model.id)}
                      className={cn(
                        "flex w-full items-center rounded-md px-2 py-1.5 text-left text-xs transition-colors",
                        model.id === modelId
                          ? "bg-primary/10 text-primary"
                          : "hover:bg-muted"
                      )}
                    >
                      {model.name}
                    </button>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}

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
