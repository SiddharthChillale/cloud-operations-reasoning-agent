"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";

interface CollapsibleFieldProps {
  label: string;
  content: string;
  isExpanded: boolean;
  onToggle: () => void;
  isCode?: boolean;
  isError?: boolean;
}

export function CollapsibleField({
  label,
  content,
  isExpanded,
  onToggle,
  isCode = false,
  isError = false,
}: CollapsibleFieldProps) {
  return (
    <div className={isError ? "text-red-600 bg-red-50 p-2 rounded" : ""}>
      <button
        onClick={onToggle}
        className="flex items-center gap-1 font-medium text-xs uppercase tracking-wide hover:underline"
      >
        {isExpanded ? (
          <ChevronDown className="w-3 h-3" />
        ) : (
          <ChevronRight className="w-3 h-3" />
        )}
        {label}
      </button>
      {isExpanded && (
        <pre
          className={`mt-1 whitespace-pre-wrap rounded p-2 text-xs overflow-x-auto ${
            isCode
              ? "bg-gray-800 text-green-400"
              : isError
              ? "bg-red-100"
              : "bg-white"
          }`}
        >
          {content}
        </pre>
      )}
    </div>
  );
}
