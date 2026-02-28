"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useTheme } from "next-themes";
import { useState, useEffect } from "react";
import Image from "next/image";
import {
  Plus,
  MessageSquare,
  Menu,
  Trash2,
  Sun,
  Moon,
} from "lucide-react";
import { getSessions, createSession, deleteSession } from "@/lib/api";
import { Session } from "@/lib/types";
import { SessionProvider, useSessionTitle } from "@/lib/SessionContext";

function SessionTitleDisplay() {
  const { sessionTitle } = useSessionTitle();
  if (!sessionTitle) return null;
  return (
    <span className="text-sm font-medium text-muted-foreground truncate max-w-md">
      {sessionTitle}
    </span>
  );
}

export default function ChatLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const { data: sessions, isLoading } = useQuery({
    queryKey: ["sessions"],
    queryFn: getSessions,
  });

  const createSessionMutation = useMutation({
    mutationFn: createSession,
    onSuccess: (data) => {
      queryClient.setQueryData(["sessions"], (old: Session[] | undefined) => {
        const newSession: Session = {
          id: data.session_id,
          title: "New Chat",
          status: "idle",
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };
        return old ? [newSession, ...old] : [newSession];
      });
      router.push(`/chat/${data.session_id}`);
    },
  });

  const deleteSessionMutation = useMutation({
    mutationFn: deleteSession,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sessions"] });
      router.push("/chat");
    },
  });

  const handleNewChat = () => {
    createSessionMutation.mutate(undefined);
  };

  const toggleSidebar = () => {
    setIsSidebarCollapsed(!isSidebarCollapsed);
  };

  const handleDeleteSession = (e: React.MouseEvent, sessionId: string) => {
    e.preventDefault();
    e.stopPropagation();
    if (window.confirm("Are you sure you want to delete this session?")) {
      deleteSessionMutation.mutate(sessionId);
    }
  };

  return (
    <div className="fixed inset-0 flex bg-background overflow-hidden">
      <aside
        className={`${
          isSidebarCollapsed ? "w-16" : "w-64"
        } bg-card border-r flex flex-col transition-all duration-300 relative z-40`}
      >
        <div className="p-4 border-b h-16 flex items-center justify-between">
          <button
            onClick={toggleSidebar}
            className="p-2 rounded-md hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
            title={isSidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            <Menu className="w-5 h-5" />
          </button>
          {!isSidebarCollapsed && (
            <button
              onClick={handleNewChat}
              disabled={createSessionMutation.isPending}
              className="p-2 rounded-md hover:bg-primary/10 text-primary transition-colors disabled:opacity-50"
              title="New Chat"
            >
              <Plus className="w-5 h-5" />
            </button>
          )}
        </div>

        {isSidebarCollapsed ? (
          <div className="flex flex-col items-center gap-4 py-4">
            <button
              onClick={handleNewChat}
              disabled={createSessionMutation.isPending}
              className="p-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 shadow-sm"
              title="New Chat"
            >
              <Plus className="w-5 h-5" />
            </button>
            <div className="h-px w-8 bg-border" />
            <div className="flex flex-col gap-2 w-full px-2 overflow-y-auto max-h-[calc(100vh-120px)] scrollbar-none">
              {sessions?.map((session) => (
                <Link
                  key={session.id}
                  href={`/chat/${session.id}`}
                  className={`p-2 rounded-md flex justify-center transition-colors ${
                    pathname === `/chat/${session.id}`
                      ? "bg-primary/10 text-primary"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground"
                  }`}
                  title={session.title}
                >
                  <MessageSquare className="w-5 h-5" />
                </Link>
              ))}
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col min-h-0">
            <div className="flex-1 overflow-y-auto">
              {isLoading ? (
                <div className="p-8 text-center">
                  <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                  <p className="text-xs text-muted-foreground">Syncing sessions...</p>
                </div>
              ) : sessions && sessions.length > 0 ? (
                <div className="py-2">
                  {sessions.map((session) => (
                    <div key={session.id} className="px-2 mb-1">
                      <Link
                        href={`/chat/${session.id}`}
                        className={`group flex items-center justify-between px-3 py-2.5 text-sm rounded-lg transition-all ${
                          pathname === `/chat/${session.id}`
                            ? "bg-primary text-primary-foreground font-medium shadow-md shadow-primary/20"
                            : "text-muted-foreground hover:bg-muted hover:text-foreground"
                        }`}
                      >
                        <div className="flex items-center gap-3 min-w-0">
                          <MessageSquare className={`w-4 h-4 flex-shrink-0 ${pathname === `/chat/${session.id}` ? "text-primary-foreground" : "text-primary"}`} />
                          <span className="truncate">{session.title}</span>
                        </div>
                        <button
                          onClick={(e) => handleDeleteSession(e, session.id)}
                          className={`p-1 rounded hover:bg-black/10 dark:hover:bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity ${pathname === `/chat/${session.id}` ? "text-primary-foreground" : "text-muted-foreground hover:text-destructive"}`}
                          title="Delete session"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </Link>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-8 text-center text-muted-foreground text-sm flex flex-col items-center gap-4">
                  <div className="w-12 h-12 rounded-2xl bg-muted flex items-center justify-center">
                    <MessageSquare className="w-6 h-6 opacity-20" />
                  </div>
                  <p>Start a new reasoning session to begin.</p>
                </div>
              )}
            </div>
          </div>
        )}
      </aside>

      <main className="flex-1 flex flex-col min-w-0 h-full relative">
        <SessionProvider>
          {/* Chat Area Header */}
          <header className="h-16 border-b flex items-center justify-between px-6 bg-background/80 backdrop-blur-md sticky top-0 z-30">
            <div className="flex items-center gap-3">
              <Link href="/" className="flex items-center gap-2 group">
                <div className="relative w-8 h-8 transition-transform group-hover:scale-105">
                  <Image
                    src={mounted && theme === "dark" ? "/cora-icon-dark.svg" : "/cora-icon-large.svg"}
                    alt="CORA"
                    width={32}
                    height={32}
                    className="object-contain"
                  />
                </div>
                <span className="text-xl font-bold tracking-tighter text-foreground">CORA</span>
              </Link>
            </div>

            <div className="flex-1 flex justify-center overflow-hidden px-4">
              <SessionTitleDisplay />
            </div>

            <div className="flex items-center gap-4">
              <button
                onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
                className="p-2.5 rounded-xl hover:bg-muted text-muted-foreground hover:text-foreground transition-all active:scale-95 border border-transparent hover:border-border"
                title={mounted && theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
              >
                {mounted && theme === "dark" ? (
                  <Sun className="w-5 h-5 text-cora-green" />
                ) : (
                  <Moon className="w-5 h-5 text-cora-emerald" />
                )}
              </button>
            </div>
          </header>

          <div className="flex-1 overflow-hidden relative">
            {children}
          </div>
        </SessionProvider>
      </main>
    </div>
  );
}
