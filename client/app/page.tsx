"use client";

import Link from "next/link";
import Image from "next/image";
import { useTheme } from "next-themes";
import { useState, useEffect } from "react";
import { 
  Bot, 
  Zap, 
  Shield, 
  Cpu, 
  Database, 
  Terminal, 
  Search, 
  Wrench, 
  Lock, 
  ChevronRight,
  BarChart3,
  Layers,
  Sparkles
} from "lucide-react";
import { motion, useScroll, useTransform } from "framer-motion";

export default function Home() {
  const { theme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const { scrollY } = useScroll();

  // Hero animations
  const heroOpacity = useTransform(scrollY, [0, 150], [1, 0]);
  const heroScale = useTransform(scrollY, [0, 150], [1, 0.95]);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  return (
    <div className="min-h-screen bg-background">
      <main>
        {/* Hero Section */}
        <section className="relative pt-20 pb-16 md:pt-32 md:pb-24 px-4 overflow-hidden border-b border-border/40">
          <motion.div 
            style={{ opacity: heroOpacity, scale: heroScale }}
            className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-[1fr_2fr] gap-12 items-center"
          >
            <div className="flex justify-center md:justify-end">
              <div className="relative w-48 h-48 sm:w-64 sm:h-64 md:w-80 md:h-80">
                <Image
                  src={theme === "dark" ? "/cora-icon-dark.svg" : "/cora-icon-large.svg"}
                  alt="CORA"
                  fill
                  className="object-contain"
                  priority
                />
              </div>
            </div>
            <div className="text-left">
              <span className="inline-block px-3 py-1 rounded-full bg-primary/10 text-primary text-sm font-medium mb-4">
                Next-Gen Cloud Reasoning
              </span>
              <h1 className="text-6xl md:text-8xl font-black tracking-tighter text-foreground mb-2">
                CORA
              </h1>
              <h2 className="text-3xl md:text-5xl font-bold tracking-tight text-foreground/90 max-w-2xl">
                Cloud Operations Reasoning Agent
              </h2>
              <p className="mt-6 text-xl text-muted-foreground max-w-xl leading-relaxed">
                Reason with your cloud infrastructure using 
                <span className="text-foreground font-semibold"> Code Actions (CodeAct)</span>.
              </p>
              <div className="mt-10 flex flex-wrap gap-4">
                <Link
                  href="/chat"
                  className="rounded-xl bg-primary px-8 py-4 text-lg font-bold text-primary-foreground shadow-xl hover:bg-primary/90 transition-all active:scale-95 flex items-center gap-2"
                >
                  Start Chatting <ChevronRight className="w-5 h-5" />
                </Link>
                <a
                  href="#features"
                  className="rounded-xl bg-secondary/50 border border-border px-8 py-4 text-lg font-bold text-foreground hover:bg-secondary transition-all active:scale-95"
                >
                  Explore Features
                </a>
              </div>
            </div>
          </motion.div>
        </section>

        {/* Key Advantages (Bento Grid) */}
        <section id="features" className="py-24 px-4 bg-muted/30">
          <div className="max-w-7xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-sm font-bold tracking-widest text-primary uppercase mb-3">Capabilities</h2>
              <h3 className="text-4xl md:text-5xl font-black tracking-tight text-foreground">
                Engineered for Performance.
              </h3>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* One-Shot Execution */}
              <div className="md:col-span-2 p-8 rounded-3xl border border-border bg-card hover:border-primary/50 transition-colors group">
                <div className="flex items-start justify-between mb-8">
                  <div className="p-3 rounded-2xl bg-primary/10 text-primary">
                    <Zap className="w-8 h-8" />
                  </div>
                  <span className="text-xs font-mono text-muted-foreground px-2 py-1 rounded border border-border">01 // EFFICIENCY</span>
                </div>
                <h4 className="text-2xl font-bold mb-4">One-Shot Execution</h4>
                <p className="text-muted-foreground text-lg max-w-md">
                  Complete complex multi-step cloud audits in a single inference turn. 
                  Minimize latency and eliminate redundant &ldquo;chatty&rdquo; interactions.
                </p>
              </div>

              {/* Native Batching */}
              <div className="p-8 rounded-3xl border border-border bg-card hover:border-primary/50 transition-colors">
                <div className="p-3 rounded-2xl bg-accent/10 text-accent mb-8 w-fit">
                  <Layers className="w-8 h-8" />
                </div>
                <h4 className="text-2xl font-bold mb-4">Native Batching</h4>
                <p className="text-muted-foreground">
                  Execute multiple API calls simultaneously via optimized Python blocks, saving both time and cost.
                </p>
              </div>

              {/* Python Libraries */}
              <div className="p-8 rounded-3xl border border-border bg-card hover:border-primary/50 transition-colors">
                <div className="p-3 rounded-2xl bg-secondary text-secondary-foreground mb-8 w-fit">
                  <Cpu className="w-8 h-8" />
                </div>
                <h4 className="text-2xl font-bold mb-4">Unlimited Python</h4>
                <p className="text-muted-foreground">
                  Leverage the entire Python ecosystem—pandas, numpy, boto3—for advanced data analysis.
                </p>
              </div>

              {/* Evolving Skills */}
              <div className="md:col-span-2 p-8 rounded-3xl border border-border bg-card hover:border-primary/50 transition-colors">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-8">
                  <div>
                    <div className="p-3 rounded-2xl bg-primary/10 text-primary mb-6 w-fit">
                      <Sparkles className="w-8 h-8" />
                    </div>
                    <h4 className="text-2xl font-bold mb-4">Evolving Skills</h4>
                    <p className="text-muted-foreground text-lg max-w-md">
                      Code Actions can be saved as parameterized skills, allowing CORA&apos;s capabilities to evolve at runtime.
                    </p>
                  </div>
                  <div className="flex-1 p-4 rounded-xl bg-muted font-mono text-xs text-muted-foreground overflow-hidden">
                    <div className="flex gap-2 mb-2"><div className="w-2 h-2 rounded-full bg-red-500" /><div className="w-2 h-2 rounded-full bg-yellow-500" /><div className="w-2 h-2 rounded-full bg-green-500" /></div>
                    <pre><code>{`def audit_s3_encryption():
  buckets = s3.list_buckets()
  # Evolving skill...
  return unencrypted`}</code></pre>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* The CORA Loop (Workflow) */}
        <section className="py-24 px-4">
          <div className="max-w-7xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-sm font-bold tracking-widest text-primary uppercase mb-3">Process</h2>
              <h3 className="text-4xl md:text-5xl font-black tracking-tight text-foreground">
                The CORA Loop.
              </h3>
            </div>

            <div className="relative">
              <div className="hidden md:block absolute top-1/2 left-0 w-full h-0.5 bg-border -translate-y-1/2 z-0" />
              <div className="grid grid-cols-1 md:grid-cols-6 gap-8 relative z-10">
                {[
                  { icon: Search, title: "Query", desc: "Request Analysis" },
                  { icon: Bot, title: "Reason", desc: "Chain of Thought" },
                  { icon: Terminal, title: "Plan", desc: "Code Generation" },
                  { icon: Cpu, title: "Execute", desc: "Lambda Sandbox" },
                  { icon: Wrench, title: "Debug", desc: "Self-Correction" },
                  { icon: Zap, title: "Response", desc: "Final Insight" }
                ].map((step, i) => (
                  <div key={i} className="flex flex-col items-center">
                    <div className="w-16 h-16 rounded-2xl bg-card border border-border flex items-center justify-center mb-6 hover:border-primary transition-colors bg-background">
                      <step.icon className="w-8 h-8 text-primary" />
                    </div>
                    <h5 className="font-bold text-lg mb-1">{step.title}</h5>
                    <p className="text-xs text-muted-foreground text-center uppercase tracking-tighter">{step.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Security & Efficiency */}
        <section className="py-24 px-4 bg-primary text-primary-foreground">
          <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-16 items-center">
            <div>
              <h3 className="text-4xl md:text-6xl font-black tracking-tighter mb-8 leading-none">
                Security-First Architecture.
              </h3>
              <div className="space-y-8">
                <div className="flex gap-6">
                  <div className="p-3 rounded-2xl bg-white/10 h-fit">
                    <Lock className="w-8 h-8" />
                  </div>
                  <div>
                    <h4 className="text-2xl font-bold mb-2">Secure Sandbox</h4>
                    <p className="text-primary-foreground/80 text-lg">
                      Execution happens in isolated, ephemeral AWS Lambda environments with full audit trails and no persistent state.
                    </p>
                  </div>
                </div>
                <div className="flex gap-6">
                  <div className="p-3 rounded-2xl bg-white/10 h-fit">
                    <Shield className="w-8 h-8" />
                  </div>
                  <div>
                    <h4 className="text-2xl font-bold mb-2">IAM Scoped</h4>
                    <p className="text-primary-foreground/80 text-lg">
                      CORA operates with granular, ReadOnly IAM permissions, ensuring least-privilege access to your infrastructure.
                    </p>
                  </div>
                </div>
              </div>
            </div>
            <div className="p-1 rounded-[2rem] bg-white/10 backdrop-blur-3xl border border-white/20 shadow-2xl overflow-hidden aspect-video relative">
              <div className="absolute inset-0 bg-gradient-to-br from-cora-emerald/40 to-transparent" />
              <div className="relative p-8 font-mono text-sm">
                <div className="flex gap-2 mb-6"><div className="w-3 h-3 rounded-full bg-white/20" /><div className="w-3 h-3 rounded-full bg-white/20" /><div className="w-3 h-3 rounded-full bg-white/20" /></div>
                <div className="space-y-2 opacity-80">
                  <p className="text-green-300"># Initializing secure sandbox...</p>
                  <p className="text-white">λ AWS_LAMBDA_REQUEST_ID: 88f2-...</p>
                  <p className="text-white">λ Validating IAM Policy: ReadOnlyAccess</p>
                  <p className="text-green-300"># Policy Verified. Executing CodeAct.</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Use Cases */}
        <section className="py-24 px-4">
          <div className="max-w-7xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-sm font-bold tracking-widest text-primary uppercase mb-3">Scenarios</h2>
              <h3 className="text-4xl md:text-5xl font-black tracking-tight text-foreground">
                Real-World Impact.
              </h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {[
                { 
                  title: "Audit & Compliance", 
                  desc: "Identify unencrypted S3 buckets and calculate data size at risk instantly.",
                  icon: BarChart3
                },
                { 
                  title: "Cloud Optimization", 
                  desc: "Real-time cloud footprint analysis and cost optimization at scale.",
                  icon: Database
                },
                { 
                  title: "Operations", 
                  desc: "Automated compliance checking and instant troubleshooting/remediation.",
                  icon: Wrench
                }
              ].map((useCase, i) => (
                <div key={i} className="p-8 rounded-3xl border border-border bg-card hover:bg-cora-parchment/10 transition-colors group">
                  <useCase.icon className="w-12 h-12 text-primary mb-6 group-hover:scale-110 transition-transform" />
                  <h4 className="text-2xl font-bold mb-4">{useCase.title}</h4>
                  <p className="text-muted-foreground">{useCase.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-border/40 py-12 px-4 bg-muted/50">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="flex items-center gap-2">
            <Image
              src={theme === "dark" ? "/cora-icon-dark.svg" : "/cora-icon-large.svg"}
              alt="CORA"
              width={32}
              height={32}
              className="object-contain"
            />
            <span className="text-xl font-bold text-foreground">CORA</span>
          </div>
          <p className="text-sm text-muted-foreground">
            © 2026 Siddharth Chillale. Built for AI Hackathon 2.0.
          </p>
          <div className="flex gap-6">
            <Link href="/chat" className="text-sm font-bold text-foreground hover:text-primary transition-colors">Chat</Link>
            <a href="https://huggingface.co/docs/smolagents/en/tutorials/secure_code_execution#code-agents" className="text-sm font-bold text-foreground hover:text-primary transition-colors">smolagents</a>
            <a href="https://github.com/SiddharthChillale/cloud-operations-reasoning-agent" className="text-sm font-bold text-foreground hover:text-primary transition-colors">GitHub</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
