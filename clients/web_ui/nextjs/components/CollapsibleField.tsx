"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight, ChevronUp } from "lucide-react";
import { MarkdownRenderer } from "./MarkdownRenderer";

interface CollapsibleFieldProps {
  label: string;
  content: string;
  isExpanded: boolean;
  onToggle: () => void;
  isCode?: boolean;
  isError?: boolean;
  useMarkdown?: boolean;
  stripMarkdownField?: boolean;
}

export function CollapsibleField({
  label,
  content,
  isExpanded,
  onToggle,
  isCode = false,
  isError = false,
  useMarkdown = false,
  stripMarkdownField = false,
}: CollapsibleFieldProps) {
  return (
    <div className={isError ? "text-red-600 bg-red-50 p-2 rounded" : ""}>
      <button
        onClick={onToggle}
        className="flex items-center gap-1 font-medium text-xs uppercase tracking-wide"
      >
        {label}
        {isExpanded ? (
          <ChevronUp className="w-3 h-3" />
        ) : (
          <ChevronDown className="w-3 h-3" />
        )}
      </button>
      {isExpanded && (
        <div
          className={`mt-1 rounded p-2 text-xs overflow-x-auto ${
            isCode
              ? "bg-gray-800 text-green-400"
              : isError
              ? "bg-red-100"
              : "bg-white"
          }`}
        >
          {useMarkdown ? (
            <MarkdownRenderer content={content} stripMarkdown={stripMarkdownField} />
          ) : (
            <pre className="whitespace-pre-wrap">{content}</pre>
          )}
        </div>
      )}
    </div>
  );
}
