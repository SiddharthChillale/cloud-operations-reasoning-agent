"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, ChevronUp, Brain, Code, CheckCircle2, Sparkles } from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { SSEMessage } from "@/lib/types";
import { CodeBlock } from "./CodeBlock";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface ReasoningHistoryProps {
  steps: SSEMessage[];
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

function stripMarkdown(text: string): string {
  return text
    .replace(/\*\*([^*]+)\*\*/g, "$1")
    .replace(/\*([^*]+)\*/g, "$1")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/```[\s\S]*?```/g, "")
    .replace(/^#+\s+/gm, "")
    .replace(/^[-*]\s+/gm, "")
    .replace(/^\d+\.\s+/gm, "");
}

export function ReasoningHistory({ steps, className }: ReasoningHistoryProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!steps || steps.length === 0) {
    return null;
  }

  const planningSteps = steps.filter((s) => s.step_type === "PlanningStep");
  const actionSteps = steps.filter((s) => s.step_type === "ActionStep");

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn("rounded-lg overflow-hidden", className)}
    >
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className={cn(
          "flex items-center justify-between w-full px-4 py-3",
          "text-left transition-colors",
        )}
      >
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <Sparkles className="w-8 h-8 text-purple-500" />
            <span className="text-sm font-medium">Reasoning</span>
          </div>
          <span className="text-xs text-muted-foreground">
            {planningSteps.length} planning, {actionSteps.length} actions
          </span>
        </div>
        <div className="flex items-center gap-2">
          <motion.div
            animate={{ scale: [1, 1.1, 1] }}
            transition={{ repeat: Infinity, duration: 2, delay: 1 }}
          >
            <CheckCircle2 className="w-4 h-4 text-green-500" />
          </motion.div>
          {isExpanded ? (
            <ChevronUp className="w-4 h-4 text-muted-foreground" />
          ) : (
            <ChevronDown className="w-4 h-4 text-muted-foreground" />
          )}
        </div>
      </button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 space-y-2 border-t border-border/50">
              {steps.map((step, index) => (
                <StepItem key={index} step={step} stepIndex={index} />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

function StepItem({ step, stepIndex }: { step: SSEMessage; stepIndex: number }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const isPlanning = step.step_type === "PlanningStep";
  const defaultFields = isPlanning ? new Set<string>() : new Set<string>(["thought"]);
  const [expandedFields, setExpandedFields] = useState<Set<string>>(defaultFields);

  const toggleField = (field: string) => {
    setExpandedFields((prev) => {
      const next = new Set(prev);
      if (next.has(field)) {
        next.delete(field);
      } else {
        next.add(field);
      }
      return next;
    });
  };

  const isFieldExpanded = (field: string) => expandedFields.has(field);
  const thought = step.model_output ? parseThought(step.model_output) : "";

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: stepIndex * 0.05 }}
      className="pt-3"
    >
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 text-sm font-medium w-full rounded px-2 py-1 -ml-2 transition-colors"
      >
        {isPlanning ? (
          <Brain className="w-4 h-4 text-purple-500 flex-shrink-0" />
        ) : (
          <Code className="w-4 h-4 text-blue-500 flex-shrink-0" />
        )}
        <span className="text-foreground">
          {isPlanning ? "Planning" : "Action"} {step.step_number}
        </span>
        {step.error && (
          <span className="text-xs bg-destructive/10 text-destructive px-2 py-0.5 rounded">
            Error
          </span>
        )}
        <span className="flex-1" />
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-muted-foreground flex-shrink-0" />
        ) : (
          <ChevronDown className="w-4 h-4 text-muted-foreground flex-shrink-0" />
        )}
      </button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="pl-6 pr-2 py-2 space-y-2 text-sm">
              {isPlanning && step.plan && (
                <p className="italic whitespace-pre-wrap">{stripMarkdown(step.plan)}</p>
              )}

              {!isPlanning && thought && (
                <p className="italic whitespace-pre-wrap">{thought}</p>
              )}

              {step.code_action && (
                <CollapsibleSection
                  label="Code"
                  isExpanded={isFieldExpanded("code_action")}
                  onToggle={() => toggleField("code_action")}
                >
                  <CodeBlock
                    code={step.code_action}
                    language="python"
                    showHeader={false}
                    maxHeight="200px"
                  />
                </CollapsibleSection>
              )}

              {step.observations && (
                <CollapsibleSection
                  label="Output"
                  isExpanded={isFieldExpanded("observations")}
                  onToggle={() => toggleField("observations")}
                >
                  <pre className="text-xs whitespace-pre-wrap text-foreground">
                    {step.observations}
                  </pre>
                </CollapsibleSection>
              )}

              {step.error && (
                <CollapsibleSection
                  label="Error"
                  isExpanded={isFieldExpanded("error")}
                  onToggle={() => toggleField("error")}
                  isError
                >
                  <pre className="text-xs whitespace-pre-wrap text-destructive">
                    {step.error}
                  </pre>
                </CollapsibleSection>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

function CollapsibleSection({
  label,
  isExpanded,
  onToggle,
  isError = false,
  children,
}: {
  label: string;
  isExpanded: boolean;
  onToggle: () => void;
  isError?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div>
      <button
        onClick={onToggle}
        className={cn(
          "flex items-center gap-1 font-medium text-xs uppercase tracking-wide",
          isError ? "text-red-600" : "text-green-600"
        )}
      >
        {label}
        {isExpanded ? (
          <ChevronUp className="w-3 h-3" />
        ) : (
          <ChevronDown className="w-3 h-3" />
        )}
      </button>
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="overflow-hidden"
          >
            <div className="mt-1">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
