"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
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

interface MarkdownRendererProps {
  content: string;
  className?: string;
  stripMarkdown?: boolean;
}

export function MarkdownRenderer({
  content,
  className = "",
  stripMarkdown: shouldStrip = false,
}: MarkdownRendererProps) {
  if (!content) {
    return null;
  }

  const processedContent = shouldStrip ? stripMarkdown(content) : content;

  return (
    <div className={cn("markdown-content", className)}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          p: ({ children }) => (
            <p className="mb-2 last:mb-0">{children}</p>
          ),
          strong: ({ node, className: strongClassName, children, ...props }) => (
            <strong className="font-semibold" {...props}>{children}</strong>
          ),
          em: ({ node, className: emClassName, children, ...props }) => (
            <em className="italic" {...props}>{children}</em>
          ),
          ul: ({ children }) => (
            <ul className="list-disc pl-4 mb-2">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="list-decimal pl-4 mb-2">{children}</ol>
          ),
          li: ({ children }) => (
            <li className="mb-1">{children}</li>
          ),
          code: ({ className: codeClassName, children, ...props }) => {
            const isInline = !codeClassName?.includes("language-");
            if (isInline) {
              return (
                <code className="rounded px-1 py-0.5 text-sm font-mono" {...props}>
                  {children}
                </code>
              );
            }
            return (
              <code className={codeClassName} {...props}>
                {children}
              </code>
            );
          },
          pre: ({ children }) => (
            <pre className="bg-gray-800 text-gray-100 rounded p-3 overflow-x-auto mb-2 text-sm font-mono">
              {children}
            </pre>
          ),
          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline"
            >
              {children}
            </a>
          ),
          h1: ({ children }) => (
            <h1 className="text-2xl font-bold mb-2">{children}</h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-xl font-bold mb-2">{children}</h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-lg font-semibold mb-1">{children}</h3>
          ),
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-gray-300 pl-3 italic text-gray-600 mb-2">
              {children}
            </blockquote>
          ),
          hr: () => <hr className="my-4 border-gray-300" />,
        }}
      >
        {processedContent}
      </ReactMarkdown>
    </div>
  );
}
