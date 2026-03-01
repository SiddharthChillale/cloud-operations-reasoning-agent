"use client";

import { useState } from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Copy, Check, ChevronDown, ChevronUp } from "lucide-react";

interface CodeBlockProps {
  code: string;
  language?: string;
  showHeader?: boolean;
  headerTitle?: string;
  maxHeight?: string;
}

export function CodeBlock({
  code,
  language = "",
  showHeader = true,
  headerTitle,
  maxHeight,
}: CodeBlockProps) {
  const [copied, setCopied] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const hasMaxHeight = !!maxHeight;
  const isCollapsed = hasMaxHeight && !isExpanded;

  return (
    <div className="rounded-md overflow-hidden mb-2 border border-gray-700">
      {showHeader && (
        <div className="flex items-center justify-between px-3 py-1.5 bg-gray-800/80 border-b border-gray-700">
          <span className="text-gray-400 text-[10px] uppercase tracking-wider">
            {headerTitle || language || "Code"}
          </span>
          <div className="flex items-center gap-2">
            {hasMaxHeight && (
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-200 transition-colors"
              >
                {isExpanded ? (
                  <>
                    <ChevronUp className="w-3 h-3" />
                    <span>Collapse</span>
                  </>
                ) : (
                  <>
                    <ChevronDown className="w-3 h-3" />
                    <span>Expand</span>
                  </>
                )}
              </button>
            )}
            <button
              onClick={handleCopy}
              className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-200 transition-colors"
            >
              {copied ? (
                <>
                  <Check className="w-3 h-3" />
                  <span>Copied!</span>
                </>
              ) : (
                <>
                  <Copy className="w-3 h-3" />
                  <span>Copy</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}
      <div style={{ maxHeight: isCollapsed ? maxHeight : undefined, overflow: isCollapsed ? "hidden" : "auto" }}>
        <SyntaxHighlighter
          style={vscDarkPlus}
          language={language}
          PreTag="div"
          customStyle={{
            margin: 0,
            borderRadius: "inherit",
            background: "#1e1e1e",
            fontSize: "0.875rem",
          }}
          showLineNumbers={false}
        >
          {code}
        </SyntaxHighlighter>
      </div>
    </div>
  );
}
