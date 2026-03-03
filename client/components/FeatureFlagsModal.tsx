"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";

interface FeatureFlagsContextType {
  dummyResponse: boolean;
  setDummyResponse: (value: boolean) => void;
  useManagerAgent: boolean;
  setUseManagerAgent: (value: boolean) => void;
}

const FeatureFlagsContext = createContext<FeatureFlagsContextType | undefined>(undefined);

const STORAGE_KEY = "dev-feature-flags";

interface FeatureFlagsProviderProps {
  children: ReactNode;
}

export function FeatureFlagsProvider({ children }: FeatureFlagsProviderProps) {
  const [dummyResponse, setDummyResponseState] = useState(false);
  const [useManagerAgent, setUseManagerAgentState] = useState(false);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        const flags = JSON.parse(stored);
        setDummyResponseState(flags.dummyResponse ?? false);
        setUseManagerAgentState(flags.useManagerAgent ?? false);
      } catch {
        // Ignore parse errors
      }
    }
    setIsLoaded(true);
  }, []);

  const setDummyResponse = (value: boolean) => {
    setDummyResponseState(value);
    const flags = { dummyResponse: value, useManagerAgent };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(flags));
  };

  const setUseManagerAgent = (value: boolean) => {
    setUseManagerAgentState(value);
    const flags = { dummyResponse, useManagerAgent: value };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(flags));
  };

  if (!isLoaded) {
    return <>{children}</>;
  }

  return (
    <FeatureFlagsContext.Provider value={{ dummyResponse, setDummyResponse, useManagerAgent, setUseManagerAgent }}>
      {children}
    </FeatureFlagsContext.Provider>
  );
}

export function useFeatureFlags() {
  const context = useContext(FeatureFlagsContext);
  if (!context) {
    throw new Error("useFeatureFlags must be used within a FeatureFlagsProvider");
  }
  return context;
}

interface FeatureFlagsModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function FeatureFlagsModal({ open, onOpenChange }: FeatureFlagsModalProps) {
  const { dummyResponse, setDummyResponse, useManagerAgent, setUseManagerAgent } = useFeatureFlags();

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Developer Settings</DialogTitle>
          <DialogDescription>
            Feature flags for development. These settings are persisted locally.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-sm font-medium leading-none">Dummy Response</p>
              <p className="text-xs text-muted-foreground">
                Return mock responses instead of calling the agent
              </p>
            </div>
            <button
              type="button"
              role="switch"
              aria-checked={dummyResponse}
              onClick={() => setDummyResponse(!dummyResponse)}
              className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 focus:ring-offset-background ${
                dummyResponse ? "bg-primary" : "bg-muted"
              }`}
            >
              <span
                className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-background shadow-lg ring-0 transition duration-200 ease-in-out ${
                  dummyResponse ? "translate-x-5" : "translate-x-0"
                }`}
              />
            </button>
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-sm font-medium leading-none">Use Manager Agent</p>
              <p className="text-xs text-muted-foreground">
                Use the manager agent (orchestrates AWS + Diagramer)
              </p>
            </div>
            <button
              type="button"
              role="switch"
              aria-checked={useManagerAgent}
              onClick={() => setUseManagerAgent(!useManagerAgent)}
              className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 focus:ring-offset-background ${
                useManagerAgent ? "bg-primary" : "bg-muted"
              }`}
            >
              <span
                className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-background shadow-lg ring-0 transition duration-200 ease-in-out ${
                  useManagerAgent ? "translate-x-5" : "translate-x-0"
                }`}
              />
            </button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
