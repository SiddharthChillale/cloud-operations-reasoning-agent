"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { Plus, MessageSquare } from "lucide-react";
import { getSessions, createSession } from "@/lib/api";

export default function Home() {
  const queryClient = useQueryClient();

  const { data: sessions, isLoading } = useQuery({
    queryKey: ["sessions"],
    queryFn: getSessions,
  });

  const createSessionMutation = useMutation({
    mutationFn: createSession,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["sessions"] });
      window.location.href = data.redirect_url;
    },
  });

  const handleNewChat = () => {
    createSessionMutation.mutate(undefined);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">CORA</h1>
          <button
            onClick={handleNewChat}
            disabled={createSessionMutation.isPending}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            <Plus className="w-4 h-4" />
            New Chat
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow">
          <div className="p-4 border-b">
            <h2 className="text-lg font-semibold">Sessions</h2>
          </div>

          {isLoading ? (
            <div className="p-8 text-center text-gray-500">Loading...</div>
          ) : sessions && sessions.length > 0 ? (
            <ul className="divide-y">
              {sessions.map((session) => (
                <li key={session.id}>
                  <Link
                    href={`/sessions/${session.id}`}
                    className="block p-4 hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <MessageSquare className="w-5 h-5 text-gray-400" />
                      <div>
                        <p className="font-medium text-gray-900">
                          {session.title}
                        </p>
                        <p className="text-sm text-gray-500">
                          {session.status} •{" "}
                          {session.updated_at
                            ? new Date(session.updated_at).toLocaleString()
                            : "No activity"}
                        </p>
                      </div>
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <div className="p-8 text-center">
              <p className="text-gray-500 mb-4">No sessions yet</p>
              <button
                onClick={handleNewChat}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Start a new chat
              </button>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
