"use client";

import { useCallback, useEffect, useState } from "react";

export type Theme = "light" | "dark";

const STORAGE_KEY = "pet-ai-theme";

export function useTheme() {
  // Starts null on both server and client's first render so hydration
  // never mismatches - layout.tsx's blocking script already set the real
  // value on <html> before paint; this just reads it back after mount.
  const [theme, setTheme] = useState<Theme | null>(null);

  useEffect(() => {
    // One-time read of what layout.tsx's blocking inline script already
    // set on <html> before this ever mounted - not a derived-state
    // anti-pattern, it's the standard fix for SSR/CSR theme mismatch
    // (same approach next-themes uses internally).
    const current = document.documentElement.getAttribute("data-theme");
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setTheme(current === "dark" ? "dark" : "light");
  }, []);

  const toggleTheme = useCallback(() => {
    setTheme((prev) => {
      const next: Theme = prev === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      try {
        localStorage.setItem(STORAGE_KEY, next);
      } catch {
        // localStorage can throw in private-browsing/blocked-storage
        // contexts - the toggle still works for the session either way.
      }
      return next;
    });
  }, []);

  return { theme, toggleTheme };
}
