"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";
import { ThemeProvider as NextThemesProvider } from "next-themes";

interface ProvidersProps {
  children: ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  const [queryClient] = useState(() => new QueryClient());

  return (
    <QueryClientProvider client={queryClient}>
      <NextThemesProvider attribute="class" defaultTheme="light" enableSystem>
        {children}
      </NextThemesProvider>
    </QueryClientProvider>
  );
}
