"use client";

import { Bot } from "lucide-react";

export default function ChatPage() {
  return (
    <div className="flex flex-col h-full items-center justify-center bg-muted/5">
      <div className="text-center max-w-sm px-6">
        <div className="w-16 h-16 rounded-3xl bg-primary/10 flex items-center justify-center mx-auto mb-6 text-primary animate-pulse">
          <Bot className="w-8 h-8" />
        </div>
        <h3 className="text-xl font-black tracking-tight text-foreground mb-2">Ready to reason.</h3>
        <p className="text-muted-foreground text-sm leading-relaxed">
          Select an existing session from the sidebar or start a new conversation to explore your cloud infrastructure.
        </p>
      </div>
    </div>
  );
}
