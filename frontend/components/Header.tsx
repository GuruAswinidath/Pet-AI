"use client";

import { LANGUAGES } from "@/lib/types";
import ThemeToggle from "./ThemeToggle";
import { GearIcon, PawIcon, PlusIcon } from "./icons";

interface HeaderProps {
  languageCode: string;
  onLanguageChange: (code: string) => void;
  onNewChat: () => void;
  onOpenSettings: () => void;
}

export default function Header({ languageCode, onLanguageChange, onNewChat, onOpenSettings }: HeaderProps) {
  return (
    <header className="app-header px-6 py-3.5 shrink-0 sticky top-0 z-10">
      <div className="max-w-4xl mx-auto flex items-center justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <div className="brand-badge w-10 h-10 shrink-0 rounded-2xl flex items-center justify-center">
            <PawIcon className="w-5 h-5" />
          </div>
          <div className="min-w-0">
            <div className="brand-name font-extrabold text-[1.15rem] leading-tight">Pet AI</div>
            <div className="brand-sub text-xs leading-tight hidden sm:block">Cat Vet Triage Assistant</div>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <ThemeToggle />

          <select
            value={languageCode}
            onChange={(e) => onLanguageChange(e.target.value)}
            className="lang-pill rounded-full px-3 py-2 text-[0.8rem] cursor-pointer hidden md:block"
            title="Reply language"
          >
            {LANGUAGES.map((lang) => (
              <option key={lang.code} value={lang.code}>
                {lang.label}
              </option>
            ))}
          </select>

          <button
            onClick={onNewChat}
            className="pill-btn pill-btn-primary inline-flex items-center gap-1.5 rounded-full px-4 py-2 text-[0.85rem] font-semibold cursor-pointer whitespace-nowrap"
            title="Start a new consultation"
          >
            <PlusIcon className="w-4 h-4 shrink-0" />
            New Chat
          </button>

          <button
            onClick={onOpenSettings}
            className="pill-btn inline-flex items-center gap-1.5 rounded-full px-4 py-2 text-[0.85rem] font-semibold cursor-pointer whitespace-nowrap"
            title="Knowledge base settings"
          >
            <GearIcon className="w-4 h-4 shrink-0" />
            <span className="hidden sm:inline">Settings</span>
          </button>
        </div>
      </div>
    </header>
  );
}
