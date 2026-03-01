"use client";

import Image from "next/image";
import { MarkdownRenderer } from "./MarkdownRenderer";

interface MultimediaRendererProps {
  output?: string;
  output_type?: "text" | "image";
  url?: string | null;
  mime_type?: string | null;
  className?: string;
}

export function MultimediaRenderer({
  output,
  output_type,
  url,
  mime_type,
  className = "",
}: MultimediaRendererProps) {
  if (output_type === "image" && url) {
    return (
      <div className={`multimedia-renderer ${className}`}>
        <div className="relative border rounded-lg overflow-hidden inline-block max-w-full">
          <Image
            src={url}
            alt="Generated image"
            width={512}
            height={512}
            className="max-w-full h-auto"
            unoptimized
          />
        </div>
        {output && (
          <p className="text-sm text-gray-500 mt-1">{output}</p>
        )}
      </div>
    );
  }

  if (output) {
    return <MarkdownRenderer content={output} className={className} />;
  }

  return null;
}
