"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useTheme } from "next-themes";
import { useState, useEffect } from "react";
import { Sun, Moon, MessageSquare, LogOut, User } from "lucide-react";
import Image from "next/image";
import { motion, useScroll, useTransform } from "framer-motion";
import { createClient } from "@/lib/supabase/client";
import type { User as SupabaseUser } from "@supabase/supabase-js";

export function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const [user, setUser] = useState<SupabaseUser | null>(null);
  const supabase = createClient();
  
  const { scrollY } = useScroll();
  const logoOpacity = useTransform(scrollY, [100, 200], [0, 1]);

  useEffect(() => {
    setMounted(true);
    
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
    });

    supabase.auth.getUser().then(({ data: { user } }) => {
      setUser(user);
    });

    return () => subscription.unsubscribe();
  }, [supabase]);

  const handleSignOut = async () => {
    await supabase.auth.signOut();
    router.push("/login");
    router.refresh();
  };

  const isChatPage = pathname.startsWith("/chat");
  const isHomePage = pathname === "/";
  const isLoginPage = pathname === "/login";

  if (isChatPage) return null;

  return (
    <header className="sticky top-0 z-50 border-b bg-background/80 backdrop-blur-md transition-all duration-200">
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 group">
          <motion.div 
            className="relative w-8 h-8"
            style={isHomePage ? { opacity: logoOpacity } : { opacity: 1 }}
          >
            <Image
              src={mounted && theme === "dark" ? "/cora-icon-dark.svg" : "/cora-icon-large.svg"}
              alt="CORA"
              width={32}
              height={32}
              className="object-contain"
            />
          </motion.div>
          <motion.span 
            className="text-xl font-bold text-foreground"
            style={isHomePage ? { opacity: logoOpacity } : { opacity: 1 }}
          >
            CORA
          </motion.span>
        </Link>

        <div className="flex items-center gap-4">
          <button
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            className="p-2 rounded-md hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
            title={mounted && theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          >
            {mounted && theme === "dark" ? (
              <Sun className="w-5 h-5" />
            ) : (
              <Moon className="w-5 h-5" />
            )}
          </button>

          {user ? (
            <>
              <Link
                href="/chat"
                className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors text-sm font-medium"
              >
                <MessageSquare className="w-4 h-4" />
                Chat
              </Link>
              <button
                onClick={handleSignOut}
                className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
                title="Sign out"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </>
          ) : !isLoginPage && (
            <Link
              href="/login"
              className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors text-sm font-medium"
            >
              <User className="w-4 h-4" />
              Login
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
