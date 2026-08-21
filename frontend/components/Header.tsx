"use client";

import { LANGUAGES } from "@/lib/types";
import { GearIcon, PawIcon, PlusIcon } from "./icons";

interface HeaderProps {
  languageCode: string;
  onLanguageChange: (code: string) => void;
  onNewChat: () => void;
  onOpenSettings: () => void;
}

export default function Header({ languageCode, onLanguageChange, onNewChat, onOpenSettings }: HeaderProps) {
  return (
    <header className="flex items-center justify-between gap-3 px-6 py-3.5 bg-[var(--panel-bg)] border-b border-[var(--border)] shrink-0">
      <div className="flex items-center gap-2.5 min-w-0">
        <div className="brand-icon w-9 h-9 shrink-0">
          <PawIcon className="w-full h-full" />
        </div>
        <div className="min-w-0">
          <div className="brand-name font-bold text-[1.15rem] leading-tight">Pet AI</div>
          <div className="text-[var(--text-muted)] text-xs leading-tight hidden sm:block">
            AI Veterinary Assistant for Cats
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2 shrink-0">
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
    </header>
  );
}
