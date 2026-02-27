"use client";

import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { dark } from "react-syntax-highlighter/dist/esm/styles/prism";

interface CodeBlockProps {
  code: string;
  language: string;
}

export function CodeBlock({ code, language }: CodeBlockProps) {
  return (
    <div className="rounded-lg overflow-hidden">
      <SyntaxHighlighter
        language={language}
        style={dark}
        customStyle={{
          margin: 0,
          borderRadius: "0.5rem",
          fontSize: "0.75rem",
          padding: "1rem",
        }}
      >
        {code}
      </SyntaxHighlighter>
    </div>
  );
}
