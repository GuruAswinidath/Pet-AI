import type { Metadata } from "next";
import { Plus_Jakarta_Sans } from "next/font/google";
import Script from "next/script";
import "./globals.css";

const jakarta = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Pet AI - Cat Vet Triage Assistant",
  description: "AI-assisted cat symptom triage - text and voice, multilingual.",
};

// Resolves the theme before first paint (stored choice, else system
// preference) and stamps it on <html> so there's no flash of the wrong
// theme. Runs as a blocking inline script - useTheme() then just reads
// back what this already set rather than racing it.
const themeInitScript = `
(function () {
  try {
    var stored = localStorage.getItem("pet-ai-theme");
    var theme = stored === "light" || stored === "dark"
      ? stored
      : (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    document.documentElement.setAttribute("data-theme", theme);
  } catch (e) {}
})();
`;

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${jakarta.variable} h-full antialiased`} suppressHydrationWarning>
      <body className="min-h-full flex flex-col">
        {/* beforeInteractive: the only Next.js-supported way to run a script
            ahead of hydration - a plain <script> JSX tag isn't executed by
            React's client renderer and would leave this racing hydration. */}
        <Script id="theme-init" strategy="beforeInteractive">
          {themeInitScript}
        </Script>
        {children}
      </body>
    </html>
  );
}
