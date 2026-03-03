"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2, Loader2, Copy, Check, Sparkles, ChevronDown, ChevronUp } from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { SSEMessage } from "@/lib/types";
import { CodeBlock } from "./CodeBlock";
import { MarkdownRenderer } from "./MarkdownRenderer";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface ChainOfThoughtProps {
  steps: SSEMessage[];
  currentStep: SSEMessage | null;
  isStreaming: boolean;
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

function getPreviewText(step: SSEMessage): string {
  if (step.error) {
    return step.error.slice(0, 80);
  }
  const content = getStepContent(step);
  return content.slice(0, 80) + (content.length > 80 ? "..." : "");
}

export function ChainOfThought({
  steps,
  currentStep,
  isStreaming,
  className,
}: ChainOfThoughtProps) {
  const [displayedContent, setDisplayedContent] = useState("");
  const [isContentComplete, setIsContentComplete] = useState(false);
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set());
  const [isPanelExpanded, setIsPanelExpanded] = useState(true);
  const animationRef = useRef<NodeJS.Timeout | null>(null);

  const content = currentStep ? getStepContent(currentStep) : "";

  // Animation for streaming step
  useEffect(() => {
    if (!currentStep || !content) {
      setDisplayedContent("");
      setIsContentComplete(false);
      return;
    }

    if (animationRef.current) {
      clearTimeout(animationRef.current);
    }

    setDisplayedContent("");
    setIsContentComplete(false);

    const chunkSize = 4;
    const minDuration = 15;
    const maxDuration = 30;
    let currentIndex = 0;

    const typeNextChunk = () => {
      if (currentIndex < content.length) {
        const endIndex = Math.min(currentIndex + chunkSize, content.length);
        setDisplayedContent(content.slice(0, endIndex));
        currentIndex = endIndex;
        
        const randomDuration = Math.random() * (maxDuration - minDuration) + minDuration;
        animationRef.current = setTimeout(typeNextChunk, randomDuration);
      } else {
        setDisplayedContent(content);
        setIsContentComplete(true);
      }
    };

    animationRef.current = setTimeout(typeNextChunk, 200);

    return () => {
      if (animationRef.current) {
        clearTimeout(animationRef.current);
      }
    };
  }, [content, currentStep]);

  // When a new step arrives, collapse all previous steps and expand the new one
  const currentStepNumber = currentStep?.step_number;
  useEffect(() => {
    if (currentStepNumber && isStreaming) {
      setExpandedSteps(new Set([currentStepNumber]));
    }
  }, [currentStepNumber, isStreaming]);

  // When streaming finishes, keep the last step expanded and collapse the panel
  const lastStep = steps.length > 0 ? steps[steps.length - 1] : null;
  const lastStepNumber = lastStep?.step_number ?? null;
  useEffect(() => {
    if (!isStreaming && lastStepNumber !== null) {
      setExpandedSteps(new Set([lastStepNumber]));
      setIsPanelExpanded(false);
    }
  }, [isStreaming, lastStepNumber]);

  const toggleStep = (stepNumber: number, e: React.MouseEvent) => {
    e.stopPropagation();
    setExpandedSteps(prev => {
      const next = new Set(prev);
      if (next.has(stepNumber)) {
        next.delete(stepNumber);
      } else {
        next.add(stepNumber);
      }
      return next;
    });
  };

  const togglePanel = () => {
    setIsPanelExpanded(!isPanelExpanded);
  };

  const planningSteps = steps.filter((s) => s.step_type === "PlanningStep");
  const actionSteps = steps.filter((s) => s.step_type === "ActionStep");

  const allSteps = [...steps, ...(currentStep ? [currentStep] : [])];
  const hasSteps = allSteps.length > 0;

  if (!isStreaming && !hasSteps) {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn("rounded-lg overflow-hidden", className)}
    >
      {/* Header */}
      <div 
        className="flex items-center justify-between px-3 py-2 border-b border-border/50 cursor-pointer hover:bg-muted/50"
        onClick={togglePanel}
      >
        <div className="flex items-center gap-2">
          {isPanelExpanded ? (
            <ChevronUp className="w-4 h-4 text-muted-foreground" />
          ) : (
            <ChevronDown className="w-4 h-4 text-muted-foreground" />
          )}
          <Sparkles className="w-4 h-4 text-primary" />
          <span className="text-sm font-medium">Reasoning</span>
          <span className="text-xs text-muted-foreground">
            {planningSteps.length} planning, {actionSteps.length} actions
          </span>
        </div>
        {!isStreaming && <CopyAllButton steps={steps} />}
      </div>

      {/* Panel content */}
      {isPanelExpanded && (
        <div className="px-3 py-2 space-y-1">
          {/* Show completed steps - filter out currentStep during streaming */}
          {steps
            .filter((s) => !currentStep || s.step_number !== currentStep.step_number)
            .map((step, index) => {
              const stepNum = step.step_number;
              if (stepNum === undefined) return null;
              return (
                <StepItem
                  key={index}
                  step={step}
                  isExpanded={expandedSteps.has(stepNum)}
                  onToggle={(e) => toggleStep(stepNum, e)}
                  isActive={false}
                />
              );
            })}

          {/* Active streaming step */}
          {currentStep && (
            <StepItem
              step={currentStep}
              isExpanded={true}
              onToggle={() => {}}
              isActive={isStreaming}
              streamedContent={displayedContent}
              isContentComplete={isContentComplete}
            />
          )}

          {/* Pending indicator when streaming but no active step yet */}
          {isStreaming && !currentStep && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground py-1">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Starting...</span>
            </div>
          )}
        </div>
      )}
    </motion.div>
  );
}

interface StepItemProps {
  step: SSEMessage;
  isExpanded: boolean;
  onToggle: (e: React.MouseEvent) => void;
  isActive: boolean;
  streamedContent?: string;
  isContentComplete?: boolean;
}

function StepItem({ step, isExpanded, onToggle, isActive, streamedContent, isContentComplete }: StepItemProps) {
  const hasError = !!step.error;
  const previewText = getPreviewText(step);
  const displayContent = isActive ? (streamedContent || getStepContent(step)) : getStepContent(step);

  // Status indicator
  const getStatusIndicator = () => {
    if (hasError) {
      return (
        <div className="w-2 h-2 rounded-full bg-red-500 flex-shrink-0" />
      );
    }
    if (isActive) {
      return (
        <motion.div
          animate={{ scale: [1, 1.2, 1], opacity: [1, 0.5, 1] }}
          transition={{ repeat: Infinity, duration: 1 }}
          className="w-2 h-2 rounded-full bg-primary flex-shrink-0"
        />
      );
    }
    return (
      <div className="w-2 h-2 rounded-full bg-green-500 flex-shrink-0" />
    );
  };

  return (
    <div className="group">
      {/* Clickable header row */}
      <div 
        className="flex items-start gap-2 cursor-pointer py-1 hover:bg-muted/30 rounded px-1 -mx-1"
        onClick={onToggle}
      >
        {/* Status dot */}
        <div className="pt-1">
          {getStatusIndicator()}
        </div>

        {/* Preview text (always visible) */}
        <div className="flex-1 min-w-0 text-sm text-foreground/90">
          <span className="truncate block">{previewText}</span>
        </div>

        {/* Expand/collapse indicator */}
        <div className="text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity">
          {isExpanded ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}
        </div>
      </div>

      {/* Expanded content */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden ml-4 pl-2 border-l border-border/50"
          >
            <div className="space-y-2 py-2">
              {/* Planning content */}
              {step.step_type === "PlanningStep" && step.plan && (
                <div className="text-sm text-foreground/90">
                  <MarkdownRenderer content={displayContent} />
                </div>
              )}

              {/* Action content */}
              {step.step_type !== "PlanningStep" && (
                <>
                  {/* Thought */}
                  {displayContent && (
                    <div className="text-sm text-foreground/90 relative">
                      <MarkdownRenderer content={displayContent} />
                      {isActive && !isContentComplete && (
                        <motion.span
                          animate={{ opacity: [1, 0] }}
                          transition={{ repeat: Infinity, duration: 0.6 }}
                          className="absolute -right-1 top-0 w-2 h-4 bg-primary rounded-sm"
                        />
                      )}
                    </div>
                  )}

                  {/* Code */}
                  {step.code_action && (
                    <CodeBlock
                      code={step.code_action}
                      language="python"
                      showHeader={true}
                      maxHeight="150px"
                    />
                  )}

                  {/* Observations/Output */}
                  {step.observations && (
                    <div className="text-xs text-muted-foreground">
                      <pre className="whitespace-pre-wrap">{step.observations}</pre>
                    </div>
                  )}

                  {/* Error */}
                  {step.error && (
                    <div className="text-xs text-destructive">
                      <pre className="whitespace-pre-wrap">{step.error}</pre>
                    </div>
                  )}
                </>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function CopyAllButton({ steps }: { steps: SSEMessage[] }) {
  const [copied, setCopied] = useState(false);

  const copyAll = async () => {
    const allText = steps.map((step) => {
      const isPlanning = step.step_type === "PlanningStep";
      
      if (isPlanning && step.plan) {
        return step.plan;
      }
      
      let text = "";
      if (step.model_output) {
        text += parseThought(step.model_output) + "\n\n";
      }
      if (step.code_action) {
        text += step.code_action + "\n\n";
      }
      if (step.observations) {
        text += step.observations + "\n";
      }
      if (step.error) {
        text += "Error: " + step.error + "\n";
      }
      return text;
    }).join("\n---\n");

    await navigator.clipboard.writeText(allText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <button
      onClick={(e) => {
        e.stopPropagation();
        copyAll();
      }}
      className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
    >
      {copied ? (
        <>
          <Check className="w-3.5 h-3.5" />
          <span>Copied!</span>
        </>
      ) : (
        <>
          <Copy className="w-3.5 h-3.5" />
          <span>Copy</span>
        </>
      )}
    </button>
  );
}
