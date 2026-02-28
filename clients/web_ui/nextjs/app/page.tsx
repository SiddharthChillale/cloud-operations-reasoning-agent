"use client";

import Link from "next/link";
import Image from "next/image";
import { useTheme } from "next-themes";
import { useState, useEffect } from "react";
import { Bot, Zap, Shield } from "lucide-react";

export default function Home() {
  const { theme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <div className="min-h-screen bg-background">
      <main>
        <section className="relative overflow-hidden">
          <div className="max-w-7xl mx-auto px-4 py-24 sm:py-32">
            <div className="text-center">
              <div className="mx-auto mb-8 relative w-48 h-48 sm:w-64 sm:h-64">
                <Image
                  src={mounted && theme === "dark" ? "/cora-icon-dark.svg" : "/cora-icon-large.svg"}
                  alt="CORA"
                  fill
                  className="object-contain"
                  priority
                />
              </div>
              <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-6xl">
                Chat with your cloud
              </h1>
              <p className="mt-6 text-lg leading-8 text-muted-foreground max-w-2xl mx-auto">
                CORA stands for Cloud Operations Reasoning Agent. Chat with your Cloud resources, generate diagrams and reports troubleshooting issues in an interactive manner. 
                
              </p>
              <div className="mt-10 flex items-center justify-center gap-x-6">
                <Link
                  href="/chat"
                  className="rounded-lg bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary transition-colors"
                >
                  Chat
                </Link>
              </div>
            </div>
          </div>
        </section>

        <section className="py-16 bg-card">
          <div className="max-w-7xl mx-auto px-4">
            <div className="grid grid-cols-1 gap-8 sm:grid-cols-3">
              <div className="text-center">
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                  <Bot className="h-6 w-6 text-primary" />
                </div>
                <h3 className="mt-4 text-lg font-semibold text-foreground">AI-Powered</h3>
                <p className="mt-2 text-sm text-muted-foreground">
                  Powered by advanced language models for intelligent conversations
                </p>
              </div>
              <div className="text-center">
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                  <Zap className="h-6 w-6 text-primary" />
                </div>
                <h3 className="mt-4 text-lg font-semibold text-foreground">Real-time Responses</h3>
                <p className="mt-2 text-sm text-muted-foreground">
                  Get instant responses with streaming support
                </p>
              </div>
              <div className="text-center">
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                  <Shield className="h-6 w-6 text-primary" />
                </div>
                <h3 className="mt-4 text-lg font-semibold text-foreground">Secure Sessions</h3>
                <p className="mt-2 text-sm text-muted-foreground">
                  Your conversations are saved in secure, isolated sessions
                </p>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t bg-card">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <p className="text-center text-sm text-muted-foreground">
            Built with smolagents
          </p>
        </div>
      </footer>
    </div>
  );
}
