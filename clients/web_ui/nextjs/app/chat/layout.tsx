"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import {
  Plus,
  MessageSquare,
  Menu,
  Trash2,
} from "lucide-react";
import { getSessions, createSession, deleteSession } from "@/lib/api";

export default function ChatLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  const { data: sessions, isLoading } = useQuery({
    queryKey: ["sessions"],
    queryFn: getSessions,
  });

  const createSessionMutation = useMutation({
    mutationFn: createSession,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["sessions"] });
      window.location.href = `/chat/${data.session_id}`;
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
    <div className="fixed top-16 left-0 right-0 bottom-0 flex bg-background overflow-hidden">
      <aside
        className={`${
          isSidebarCollapsed ? "w-16" : "w-64"
        } bg-card border-r flex flex-col transition-all duration-300`}
      >
        <div className="p-3 border-b">
          <button
            onClick={toggleSidebar}
            className="p-1.5 rounded-md hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
            title={isSidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            <Menu className="w-5 h-5" />
          </button>
        </div>

        {!isSidebarCollapsed && (
          <div className="p-4">
            <button
              onClick={handleNewChat}
              disabled={createSessionMutation.isPending}
              className="flex items-center justify-center gap-2 w-full px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors text-sm font-medium"
            >
              <Plus className="w-4 h-4" />
              New Chat
            </button>
          </div>
        )}

        {isSidebarCollapsed ? (
          <div className="flex flex-col items-center gap-2 p-2">
            <button
              onClick={handleNewChat}
              disabled={createSessionMutation.isPending}
              className="p-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              title="New Chat"
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto">
            {isLoading ? (
              <div className="p-4 text-center text-muted-foreground text-sm">
                Loading...
              </div>
            ) : sessions && sessions.length > 0 ? (
              <ul className="">
                {sessions.map((session) => (
                  <li key={session.id}>
                    <Link
                      href={`/chat/${session.id}`}
                      className={`group flex items-center justify-between px-3 py-2 text-sm transition-colors ${
                        pathname === `/chat/${session.id}`
                          ? "bg-primary/10 text-primary font-medium"
                          : "text-muted-foreground hover:bg-muted hover:text-foreground"
                      }`}
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        <span className="truncate">{session.title}</span>
                      </div>
                      <button
                        onClick={(e) => handleDeleteSession(e, session.id)}
                        className="p-1 opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive transition-all flex-shrink-0"
                        title="Delete session"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </Link>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="p-4 text-center text-muted-foreground text-sm">
                No sessions yet
              </div>
            )}
          </div>
        )}
      </aside>

      <main className="flex-1 flex flex-col min-w-0 h-full">{children}</main>
    </div>
  );
}
