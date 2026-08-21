"use client";

import { useTheme } from "@/hooks/useTheme";
import { MoonIcon, SunIcon } from "./icons";

export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";

  return (
    <button
      type="button"
      onClick={toggleTheme}
      role="switch"
      aria-checked={isDark}
      aria-label="Toggle light / dark theme"
      title="Toggle light / dark theme"
      className="theme-toggle relative inline-flex items-center shrink-0 w-[50px] h-[28px] rounded-full cursor-pointer"
    >
      <span
        className={`theme-toggle-thumb absolute top-[2.5px] left-[2.5px] w-[21px] h-[21px] rounded-full flex items-center justify-center transition-transform duration-200 ease-out ${
          isDark ? "translate-x-[22px]" : "translate-x-0"
        }`}
      >
        {theme !== null && (isDark ? <MoonIcon className="w-3 h-3" /> : <SunIcon className="w-3 h-3" />)}
      </span>
    </button>
  );
}
