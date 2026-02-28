"use client";

import { createContext, useContext, useState, ReactNode } from "react";

interface SessionContextType {
  sessionTitle: string;
  setSessionTitle: (title: string) => void;
}

const SessionContext = createContext<SessionContextType | undefined>(undefined);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [sessionTitle, setSessionTitle] = useState("");
  return (
    <SessionContext.Provider value={{ sessionTitle, setSessionTitle }}>
      {children}
    </SessionContext.Provider>
  );
}

export function useSessionTitle() {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error("useSessionTitle must be used within SessionProvider");
  }
  return context;
}
