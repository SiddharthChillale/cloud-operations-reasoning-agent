"use client";

import { useEffect, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Brain, Code, Loader2 } from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { SSEMessage } from "@/lib/types";
import { animationConfig } from "@/lib/config";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface LiveThinkingProps {
  step: SSEMessage | null;
  className?: string;
}

function parseThought(modelOutput: string): string {
  try {
    const parsed = JSON.parse(modelOutput);
    if (parsed.thought) return parsed.thought;
  } catch {
    // Not JSON, return as-is
  }
  return modelOutput;
}

function getStepContent(step: SSEMessage): string {
  if (step.step_type === "PlanningStep") {
    return step.plan || "";
  } else {
    return parseThought(step.model_output || "");
  }
}

export function LiveThinking({ step, className }: LiveThinkingProps) {
  const [displayedContent, setDisplayedContent] = useState("");
  const [isComplete, setIsComplete] = useState(false);

  const content = step ? getStepContent(step) : "";

  useEffect(() => {
    if (!step || !content) {
      setDisplayedContent("");
      setIsComplete(false);
      return;
    }

    setDisplayedContent("");
    setIsComplete(false);

    let currentIndex = 0;
    const chars = content.split("");
    const minDuration = animationConfig.minCharDuration;
    const maxDuration = animationConfig.maxCharDuration;

    const typeNextChar = () => {
      if (currentIndex < chars.length) {
        setDisplayedContent(chars.slice(0, currentIndex + 1).join(""));
        currentIndex++;
        const randomDuration = Math.random() * (maxDuration - minDuration) + minDuration;
        setTimeout(typeNextChar, randomDuration);
      } else {
        setIsComplete(true);
      }
    };

    const initialDelay = setTimeout(typeNextChar, 300);
    return () => clearTimeout(initialDelay);
  }, [content, step]);

  if (!step) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        className={cn("flex items-center gap-3 px-4 py-3 rounded-lg", className)}
      >
        <div className="relative">
          <Loader2 className="w-5 h-5 animate-spin text-primary" />
          <motion.div
            animate={{ scale: [1, 1.2, 1], opacity: [0.5, 0, 0.5] }}
            transition={{ repeat: Infinity, duration: 1.5 }}
            className="absolute inset-0 bg-primary rounded-full"
          />
        </div>
        <span className="text-muted-foreground">Thinking...</span>
      </motion.div>
    );
  }

  const isPlanning = step.step_type === "PlanningStep";

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={step.step_number}
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: 20 }}
        transition={{ duration: 0.2 }}
        className={cn(
          "flex items-start gap-3 px-4 py-3 rounded-lg",
          "bg-muted/50 border border-border/50",
          className
        )}
      >
        <div className="flex-shrink-0 mt-0.5">
          {isPlanning ? (
            <motion.div
              animate={{ rotate: [0, 360] }}
              transition={{ repeat: Infinity, duration: 3, ease: "linear" }}
            >
              <Brain className="w-5 h-5 text-purple-500" />
            </motion.div>
          ) : (
            <motion.div
              initial={{ scale: 0.8 }}
              animate={{ scale: 1 }}
              transition={{ type: "spring", stiffness: 500, damping: 30 }}
            >
              <Code className="w-5 h-5 text-blue-500" />
            </motion.div>
          )}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={cn("text-xs font-medium uppercase tracking-wide", isPlanning ? "text-purple-600" : "text-blue-600")}>
              {isPlanning ? "Planning" : "Action"}
            </span>
            <span className="text-xs text-muted-foreground">
              Step {step.step_number}
            </span>
            {!isComplete && (
              <motion.span
                animate={{ opacity: [1, 0] }}
                transition={{ repeat: Infinity, duration: 0.5 }}
                className="w-2 h-2 bg-primary rounded-full"
              />
            )}
          </div>

          <div className="text-sm text-foreground">
            <TypewriterContent content={displayedContent} isComplete={isComplete} />
          </div>

          {step.code_action && !isPlanning && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="mt-2"
            >
              <CodePreview code={step.code_action} />
            </motion.div>
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  );
}

function TypewriterContent({ content, isComplete }: { content: string; isComplete: boolean }) {
  const [showCursor, setShowCursor] = useState(true);

  useEffect(() => {
    if (isComplete) {
      const timer = setTimeout(() => setShowCursor(false), 500);
      return () => clearTimeout(timer);
    }

    const interval = setInterval(() => {
      setShowCursor((prev) => !prev);
    }, 530);
    return () => clearInterval(interval);
  }, [isComplete]);

  return (
    <span className="whitespace-pre-wrap">
      {content}
      <motion.span
        animate={{ opacity: showCursor ? 1 : 0 }}
        transition={{ duration: 0.1 }}
        className="inline-block w-0.5 h-4 ml-0.5 align-middle bg-primary"
      />
    </span>
  );
}

function CodePreview({ code }: { code: string }) {
  const preview = code.length > 200 ? code.slice(0, 200) + "..." : code;
  const [isExpanded, setIsExpanded] = useState(false);
  const displayCode = isExpanded ? code : preview;
  const isTruncated = code.length > 200;

  return (
    <div className="rounded bg-gray-900 text-gray-100 text-xs font-mono overflow-hidden">
      <div className="flex items-center justify-between px-3 py-1.5 bg-gray-800/50">
        <span className="text-gray-400 text-[10px] uppercase tracking-wider">Code</span>
        {isTruncated && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
          >
            {isExpanded ? "Show less" : "Show more"}
          </button>
        )}
      </div>
      <pre className="px-3 py-2 overflow-x-auto">
        <code>{displayCode}</code>
      </pre>
    </div>
  );
}

export function useTypewriter(text: string, speed: number = 30) {
  const [displayed, setDisplayed] = useState("");

  useEffect(() => {
    if (!text) {
      setDisplayed("");
      return;
    }

    setDisplayed("");
    let index = 0;

    const interval = setInterval(() => {
      if (index < text.length) {
        setDisplayed(text.slice(0, index + 1));
        index++;
      } else {
        clearInterval(interval);
      }
    }, speed);

    return () => clearInterval(interval);
  }, [text, speed]);

  return displayed;
}
